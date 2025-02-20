from enum import Enum


class OperationType(str, Enum):
    BACKUP = "backup"
    RESTORE = "restore"


METADATA_SUFFIX = ".meta"
ARCHIVE_SUFFIX = ".tar.zst.crypt"
MIGRATION_SUFFIX = ".migration.bak"

ANALYSIS_FILE = "analysis.json"
