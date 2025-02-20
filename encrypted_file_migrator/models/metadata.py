from typing import List

from .model import Model


class Metadata(Model):
    def __init__(
            self,
            input_manifest_files: List[str],
            exclude_manifest_patterns: List[str],
            total_size: int
    ):
        self.input_manifest_files = input_manifest_files
        self.exclude_manifest_patterns = exclude_manifest_patterns
        self.total_size = total_size
