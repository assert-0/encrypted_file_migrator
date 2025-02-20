import json
import multiprocessing
import os
import subprocess
from abc import ABC, abstractmethod
from getpass import getpass
from typing import Type, List, Dict

from .consts import OperationType, METADATA_SUFFIX, MIGRATION_SUFFIX, \
    ANALYSIS_FILE
from .models.analysis import Analysis
from .models.args import Args
from .models.metadata import Metadata
from .utils import to_engineering_notation


class Operation(ABC):
    def __init__(self, args: Args):
        self.args = args
        self.validate()

    @abstractmethod
    def execute(self):
        pass

    def validate(self):
        if self.args.threads < 1:
            self.args.threads = multiprocessing.cpu_count()

    def _create_pipeline(
            self, commands: List[List[str]]
    ) -> List[subprocess.Popen]:
        procs: List[subprocess.Popen] = [
            subprocess.Popen(commands[0], stdout=subprocess.PIPE)
        ]

        for idx, command in enumerate(commands[1:]):
            procs.append(
                subprocess.Popen(
                    command, stdin=procs[idx].stdout, stdout=subprocess.PIPE
                )
            )

        return procs

    def _execute_command(self, command: List[str]) -> str:
        result = subprocess.run(command, capture_output=True)
        if result.returncode != 0:
            raise ValueError(
                f"Command '{' '.join(command)}' failed with "
                f"output: {result.stderr.decode()}"
            )

        return result.stdout.decode()

    def _pv_command(self, total_bytes: int) -> List[str]:
        return [
            f"pv",
            f"--progress",
            f"--bytes",
            f"--rate",
            f"--average-rate",
            f"--eta",
            f"--size", f"{total_bytes}",
        ]

    def _du_command(self, files: List[str]) -> List[str]:
        return [
            f"du",
            f"--total",
            f"--block-size=1",
            *files,
        ]


class OperationsFactory:
    ops: Dict[OperationType, Type[Operation]] = {}

    @classmethod
    def register_operation(
            cls, operation_type: OperationType, operation_cls: Type[Operation]
    ) -> None:
        cls.ops[operation_type] = operation_cls

    @classmethod
    def create_operation(cls, args: Args):
        if not (operation := cls.ops.get(args.operation, None)):
            raise ValueError(f"Unrecognized operation: '{args.operation}'")

        return operation(args=args)


class Backup(Operation):
    def validate(self) -> None:
        super().validate()

        if not self.args.manifest_path:
            raise ValueError("Manifest path is required")

        if not os.path.exists(self.args.manifest_path):
            raise ValueError(
                f"Manifest path '{self.args.manifest_path}' does not exist"
            )

        if self.args.exclude_manifest_path and not os.path.exists(
            self.args.exclude_manifest_path
        ):
            raise ValueError(
                f"Exclude manifest path '{self.args.exclude_manifest_path}' "
                f"does not exist"
            )

        if not self.args.destination_path:
            raise ValueError("Destination path is required")

        if not os.path.exists(
                os.path.dirname(self.args.destination_path)
        ):
            raise ValueError(
                f"Destination directory "
                f"'{os.path.dirname(self.args.destination_path)}' "
                f"does not exist"
            )

        if self.args.threads < 1:
            raise ValueError("Threads must be greater than 0")

        if not self.args.encryption_password:
            raise ValueError("Encryption password is required")

        confirm_password = getpass(prompt="Confirm the encryption password: ")
        if self.args.encryption_password != confirm_password:
            raise ValueError("Encryption passwords do not match")

        if not self.args.metadata_path:
            self.args.metadata_path = (
                    self.args.destination_path + METADATA_SUFFIX
            )

    def execute(self) -> None:
        print("Calculating total size of files to backup...")
        with open(self.args.manifest_path, "r") as f:
            files = [line.strip() for line in f.readlines()]

        sizes = self._execute_command(self._du_command(files)).split("\n")

        # Extract the total size from last non-blank line
        size = float(sizes[-2].split()[0])

        print(
            f"Total size of files to backup: "
            f"{to_engineering_notation(size)} bytes"
        )

        continue_flag = input("Do you want to continue? [Y/n]: ")
        if continue_flag.lower() != "y" and continue_flag.strip() != "":
            print("Backup aborted")
            return

        print(f"Starting backup using {self.args.threads} threads...")

        pipeline = self._create_pipeline(
            [
                self._tar_command(),
                self._pv_command(int(size)),
                self._zstd_command(),
                self._openssl_command(self.args.destination_path),
            ]
        )
        pipeline[-1].communicate()

        print("Backup completed")

        print("Saving metadata...")

        with open(self.args.exclude_manifest_path, "r") as f:
            exclude_manifest_patterns = [
                line.strip() for line in f.readlines()
            ]

        metadata = Metadata(
            input_manifest_files=files,
            exclude_manifest_patterns=exclude_manifest_patterns,
            total_size=int(size),
        )

        metadata_json = json.dumps(metadata.model_dump())

        openssl = subprocess.Popen(
            self._openssl_command(self.args.metadata_path),
            stdin=subprocess.PIPE,
        )
        zstd = subprocess.Popen(
            self._zstd_command(),
            stdin=subprocess.PIPE,
            stdout=openssl.stdin,
        )
        zstd.communicate(input=metadata_json.encode())

    def _tar_command(self) -> List[str]:
        command = [
            f"tar",
            f"--create",
            f"--verbose",
            f"--acls",
            f"--selinux",
            f"--xattrs",
            f"--absolute-names",
            (
                f"--exclude-from={self.args.exclude_manifest_path}"
                if self.args.exclude_manifest_path else ""
            ),
            f"--files-from={self.args.manifest_path}",
        ]

        return command

    def _zstd_command(self) -> List[str]:
        return [
            f"zstd",
            f"--compress",
            f"--threads={self.args.threads}",
            f"--stdout",
        ]

    def _openssl_command(self, destination_path: str) -> List[str]:
        return [
            f"openssl",
            f"enc",
            f"-e",
            f"-aes-256-cbc",
            f"-pbkdf2",
            f"-k", f"{self.args.encryption_password}",
            f"-out", f"{destination_path}",
        ]


class Restore(Operation):
    def validate(self) -> None:
        super().validate()

        if not self.args.source_backup_path:
            raise ValueError("Source backup path is required")

        if not os.path.exists(self.args.source_backup_path):
            raise ValueError(
                f"Source backup path '{self.args.source_backup_path}' "
                f"does not exist"
            )

        if self.args.threads < 1:
            raise ValueError("Threads must be greater than 0")

        if not self.args.encryption_password:
            raise ValueError("Encryption password is required")

        if not self.args.metadata_path:
            self.args.metadata_path = (
                self.args.source_backup_path + METADATA_SUFFIX
            )

        if not os.path.exists(self.args.metadata_path):
            raise ValueError(
                f"Metadata path '{self.args.metadata_path}' does not exist"
            )

    def execute(self) -> None:
        print("Reading metadata...")

        pipeline = self._create_pipeline(
            [
                self._openssl_command(self.args.metadata_path),
                self._zstd_command(),
            ]
        )
        metadata_json = pipeline[-1].communicate()[0].decode("utf-8")
        metadata_dict = json.loads(metadata_json)
        metadata = Metadata.model_load(metadata_dict)

        print(
            f"Size of backup: "
            f"{to_engineering_notation(metadata.total_size)} bytes"
        )

        continue_flag = input("Do you want to continue? [Y/n]: ")
        if continue_flag.lower() != "y" and continue_flag.strip() != "":
            print("Restore aborted")
            return

        print(f"Starting restore using {self.args.threads} threads...")

        pipeline = self._create_pipeline(
            [
                self._openssl_command(self.args.source_backup_path),
                self._zstd_command(),
                self._pv_command(metadata.total_size),
                self._tar_command(),
            ]
        )
        pipeline[-1].communicate()

        print("Restore completed")

        print("Analyzing restore conflicts (old files backed up)...")

        conflicting_files = []
        for file in metadata.input_manifest_files:
            if os.path.isfile(file):
                if os.path.exists(file + MIGRATION_SUFFIX):
                    conflicting_files.append(file)
            elif os.path.isdir(file):
                for root, _, files in os.walk(file):
                    for f in files:
                        f = os.path.join(root, f)
                        if os.path.exists(f + MIGRATION_SUFFIX):
                            conflicting_files.append(f)

        analysis = Analysis(conflicting_files=conflicting_files)
        analysis_json = json.dumps(analysis.model_dump())
        with open(ANALYSIS_FILE, "w") as f:
            f.write(analysis_json)

        print("Analysis completed")
        print(f"Analysis file saved to '{os.getcwd()}/{ANALYSIS_FILE}'")

    def _tar_command(self) -> List[str]:
        return [
            f"tar",
            f"--extract",
            f"--verbose",
            f"--acls",
            f"--selinux",
            f"--xattrs",
            f"--absolute-names",
            f"--same-permissions",
            f"--same-owner",
            f"--backup",
            f"--suffix={MIGRATION_SUFFIX}",
        ]

    def _zstd_command(self) -> List[str]:
        return [
            f"zstd",
            f"--decompress",
            f"--threads={self.args.threads}",
            f"--stdout",
        ]

    def _openssl_command(self, source_path: str) -> List[str]:
        return [
            f"openssl",
            f"enc",
            f"-d",
            f"-aes-256-cbc",
            f"-pbkdf2",
            f"-k", f"{self.args.encryption_password}",
            f"-in", f"{source_path}",
        ]


OperationsFactory.register_operation(OperationType.BACKUP, Backup)
OperationsFactory.register_operation(OperationType.RESTORE, Restore)
