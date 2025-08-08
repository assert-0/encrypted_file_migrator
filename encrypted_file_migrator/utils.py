import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Optional, Tuple
from wcmatch import glob
from wcmatch.glob import WcMatcher


def to_engineering_notation(value: float, precision: int = 3):
    if value == 0:
        return "0.0"

    exponent = math.floor(math.log10(abs(value)) / 3) * 3
    mantissa = value / (10 ** exponent)

    return f"{mantissa:.{precision}f}E{exponent:+d}"


class FileIndexer:
    def __init__(
            self,
            exclude_patterns: Optional[List[str]] = None,
            include_hidden=True,
            follow_symlinks=False,
            sort_output=True,
            max_workers: int = 1,
    ):
        self.follow_symlinks = follow_symlinks
        self.sort_output = sort_output
        self.max_workers = max_workers
        self.exclude_patterns = exclude_patterns
        self.include_hidden = include_hidden

    def run(self, roots: List[str]) -> Tuple[List[str], int, List[str]]:
        results: List[str] = []
        missing: List[str] = []
        total_size = 0
        tasks: List[Tuple[str, str]] = []

        for root in roots:
            root = os.path.normpath(root)
            base = os.path.dirname(root)
            tasks.append((root, base))

        if tasks:
            with ProcessPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [
                    ex.submit(self.walk_subtree, start)
                    for start, base in tasks
                ]
                for f in as_completed(futures):
                    sub_paths, sub_size, sub_missing = f.result()
                    results.extend(sub_paths)
                    total_size += sub_size
                    missing.extend(sub_missing)

        if self.sort_output:
            results.sort()

        return results, total_size, missing

    def check_excluded(
            self, path: str, exclude_matcher: Optional[WcMatcher]
    ) -> bool:
        if exclude_matcher and exclude_matcher.match(path):
            return True
        return False

    def walk_subtree(
            self,
            start: str,
    ) -> Tuple[List[str], int, List[str]]:
        out: List[str] = []
        missing: List[str] = []
        total_size = 0
        stack = [os.path.normpath(start)]

        if self.exclude_patterns:
            flags = glob.GLOBSTAR
            if self.include_hidden:
                flags |= glob.DOTGLOB
            exclude_matcher = glob.compile(self.exclude_patterns, flags=flags)
        else:
            exclude_matcher = None

        while stack:
            path = stack.pop()
            if self.check_excluded(path, exclude_matcher):
                continue

            try:
                with os.scandir(path) as it:
                    had_child = False
                    for entry in it:
                        child = entry.path
                        if self.check_excluded(child, exclude_matcher):
                            continue
                        if entry.is_dir(follow_symlinks=self.follow_symlinks):
                            stack.append(child)
                            had_child = True
                        else:
                            out.append(child)
                            try:
                                total_size += entry.stat(
                                    follow_symlinks=False
                                ).st_size
                            except FileNotFoundError:
                                continue
                            had_child = True
                    if not had_child:
                        out.append(path)  # empty dir
            except NotADirectoryError:
                out.append(path)
                try:
                    total_size += os.stat(
                        path, follow_symlinks=False
                    ).st_size
                except FileNotFoundError:
                    pass
            except FileNotFoundError:
                missing.append(path)

        return out, total_size, missing
