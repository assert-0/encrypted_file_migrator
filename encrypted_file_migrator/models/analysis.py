from typing import List

from .model import Model


class Analysis(Model):
    def __init__(self, conflicting_files: List[str]):
        self.conflict_files = conflicting_files
