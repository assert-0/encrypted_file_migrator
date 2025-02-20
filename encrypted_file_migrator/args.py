from .consts import OperationType


class Args:
    def __init__(
            self,
            operation: OperationType,
            encryption_password: str,
            threads: int,
            manifest_path: str,
            exclude_manifest_path: str,
            destination_path: str, source_backup_path: str
    ):
        self.operation = operation
        self.encryption_password = encryption_password
        self.threads = threads
        self.manifest_path = manifest_path
        self.exclude_manifest_path = exclude_manifest_path
        self.destination_path = destination_path
        self.source_backup_path = source_backup_path

        self.validate()

    def validate(self):
        if self.operation not in OperationType.__members__.values():
            raise ValueError(f"Unrecognized operation: '{self.operation}'")

    def __str__(self):
        return str({
            "operation": self.operation,
            "encryption_password": self.encryption_password,
            "threads": self.threads,
            "manifest_path": self.manifest_path,
            "exclude_manifest_path": self.exclude_manifest_path,
            "destination_path": self.destination_path,
            "source_backup_path": self.source_backup_path,
        })
