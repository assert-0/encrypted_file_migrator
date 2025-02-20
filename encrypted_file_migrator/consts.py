from enum import Enum


class OperationType(str, Enum):
    BACKUP = "backup"
    RESTORE = "restore"
