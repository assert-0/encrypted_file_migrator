import argparse


class Args:
    def __init__(self, operation: str, manifest_path: str, destination_path: str, source_backup_path: str):
        self.operation = operation
        self.manifest_path = manifest_path
        self.destination_path = destination_path
        self.source_backup_path = source_backup_path

        self.validate()

    def validate(self):
        pass

    def __str__(self):
        return str({
            "operation": self.operation,
            "manifest_path": self.manifest_path,
            "destination_path": self.destination_path,
            "source_backup_path": self.source_backup_path,
        })


def parse_args() -> Args:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "operation", choices=["backup", "restore"]
    )
    arg_parser.add_argument(
        "--manifest-path", "-m", help="Path to the manifest file (backup phase)",
        default=None
    )
    arg_parser.add_argument(
        "--destination-path", "-d", help="Path to save the backup to (backup phase)",
        default=None
    )
    arg_parser.add_argument(
        "--source-backup-path", "-s", help="Path to the backup file that will be restored (restore phase)",
        default=None
    )
    arg_parser.parse_args()

    return Args(
        operation=arg_parser.operation,
        manifest_path=arg_parser.manifest_path,
        destination_path=arg_parser.destination_path,
        source_backup_path=arg_parser.source_backup_path
    )


def main():
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
