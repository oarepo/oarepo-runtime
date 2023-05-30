import dataclasses
from typing import Any, Dict, Iterator, List, Optional, Union


@dataclasses.dataclass
class PathPrefix:
    key: str
    matched_path: Union[int, None]
    sub_prefixes: List["PathPrefix"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PathStackEntry:
    parent_data: Dict[str, Any]
    prefix: PathPrefix
    index: Optional[int] = None

    @property
    def key(self):
        return self.prefix.key

    @property
    def current(self):
        ret = self.parent_data[self.prefix.key]
        if self.index is not None:
            ret = ret[self.index]
        return ret

    def set(self, value):
        if self.index is None:
            self.parent_data[self.prefix.key] = value
        else:
            self.parent_data[self.prefix.key][self.index] = value

    def enter(self, prefix: PathPrefix):
        current = self.current
        if not isinstance(current, dict):
            return []
        if prefix.key not in current:
            return []
        child = current[prefix.key]
        if isinstance(child, (list, tuple)):
            return [
                # the data in the entry is parent data, that's why current is here
                PathStackEntry(parent_data=current, prefix=prefix, index=idx)
                for idx, x in enumerate(child)
            ]
        else:
            return [
                # the data in the entry is parent data, that's why current is here
                PathStackEntry(parent_data=current, prefix=prefix)
            ]


class PathTraversal:
    """A helper class for getting data at multiple paths"""

    def __init__(self, paths):
        self.paths = paths
        self._create_path_tree()

    def _create_path_tree(self):
        """
        Create tree of PathPrefix objects from a list of paths
        """
        root = PathPrefix("", None)
        for path_idx, pth in enumerate(self.paths):
            node = root
            split_path = pth.split("/")
            for idx, entry in enumerate(split_path):
                try:
                    node = next(x for x in node.sub_prefixes if x.key == entry)
                except StopIteration:
                    child = PathPrefix(
                        entry, path_idx if idx + 1 == len(split_path) else None
                    )
                    node.sub_prefixes.append(child)
                    node = child
        self._path_tree = root

    def iter(self, data) -> Iterator[List[PathStackEntry]]:
        """
        yields List[PathStackEntry] for each matching path
        """
        queue = [[PathStackEntry({"": data}, self._path_tree, None)]]
        while queue:
            prefix_node: PathPrefix
            stack = queue.pop()
            top: PathStackEntry = stack[-1]
            prefix = top.prefix
            if prefix.matched_path is not None:
                yield stack
            for sub_prefix in reversed(prefix.sub_prefixes):
                children = top.enter(sub_prefix)
                for child in children:
                    queue.append(stack + [child])
        return data
