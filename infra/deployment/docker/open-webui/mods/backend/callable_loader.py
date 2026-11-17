from importlib.machinery import SourceFileLoader
from types import CodeType

from aihub_mods.callable_transform import CallableTransform


class CallableLoader(SourceFileLoader):
    def get_code(self, fullname: str) -> CodeType:
        tree = CallableTransform(fullname).transform(self.get_data(self.path), self.path)
        return compile(tree, self.path, "exec")
