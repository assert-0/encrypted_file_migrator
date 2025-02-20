import argparse
from getpass import getpass

from .models.args import Args
from .operations import OperationsFactory


def parse_args() -> Args:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "operation", choices=["backup", "restore"]
    )
    arg_parser.add_argument(
        "--threads", "-t",
        help=(
            "Number of threads to use for (de)compression "
            "(default is -1, which means all available cores)"
        ),
        type=int, default=-1
    )
    arg_parser.add_argument(
        "--manifest-path", "-m",
        help="Path to the manifest file (backup phase)",
        default=None
    )
    arg_parser.add_argument(
        "--exclude-manifest-path", "-e",
        help="Path to the exclude manifest file (backup phase)",
        default=None
    )
    arg_parser.add_argument(
        "--destination-path", "-d",
        help="Path to save the backup to (backup phase)",
        default=None
    )
    arg_parser.add_argument(
        "--source-backup-path", "-s",
        help="Path to the backup file that will be restored (restore phase)",
        default=None
    )
    arg_parser.add_argument(
        "--metadata-path",
        help="Path to the metadata file "
             "(defaults to the same path as the backup file)",
        default=None
    )
    args = arg_parser.parse_args()

    encryption_password = getpass(prompt="Enter the encryption password: ")

    return Args(
        operation=args.operation,
        encryption_password=encryption_password,
        threads=args.threads,
        manifest_path=args.manifest_path,
        exclude_manifest_path=args.exclude_manifest_path,
        destination_path=args.destination_path,
        source_backup_path=args.source_backup_path,
        metadata_path=args.metadata_path
    )


def main():
    args = parse_args()
    try:
        op = OperationsFactory.create_operation(args)
        op.execute()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    exit(0)


if __name__ == "__main__":
    main()
