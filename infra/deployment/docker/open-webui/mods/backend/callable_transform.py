import ast
import hashlib
from pathlib import Path


class CallableTransform(ast.NodeTransformer):
    """Wrap after native decorators, leaving caches and context managers inside each original."""

    ALIAS = "__aihub_callable_registry__"
    DESCRIPTORS = {"property", "field_validator", "model_validator", "validator"}

    def __init__(self, module: str) -> None:
        self.module = module
        self.classes: list[str] = []
        self.targets: set[str] = set()

    @classmethod
    def catalog(cls, root: Path) -> dict[str, dict[str, str]]:
        catalog = {}
        for path in sorted(root.rglob("*.py")):
            parts = path.relative_to(root).with_suffix("").parts
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if not parts or parts[0] == "migrations" or not all(part.isidentifier() for part in parts):
                continue
            source = path.read_bytes()
            transform = cls("open_webui." + ".".join(parts))
            transform.transform(source, str(path))
            fingerprint = {"source_sha256": hashlib.sha256(source).hexdigest()}
            catalog.update({target: fingerprint for target in sorted(transform.targets)})
        return catalog

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self.classes.append(node.name)
        self.generic_visit(node)
        self.classes.pop()
        return node

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.stmt | list[ast.stmt]:
        for decorator in node.decorator_list:
            expression = decorator.func if isinstance(decorator, ast.Call) else decorator
            name = expression.id if isinstance(expression, ast.Name) else getattr(expression, "attr", None)
            if name in self.DESCRIPTORS:
                return node
        target = self.module + ":" + ".".join([*self.classes, node.name])
        self.targets.add(target)
        assignment = ast.Assign(
            targets=[ast.Name(id=node.name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Attribute(value=ast.Name(id=self.ALIAS, ctx=ast.Load()), attr="decorate", ctx=ast.Load()),
                args=[ast.Constant(target), ast.Name(id=node.name, ctx=ast.Load())], keywords=[],
            ),
        )
        return [node, ast.copy_location(assignment, node)]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.stmt | list[ast.stmt]:
        return self._function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.stmt | list[ast.stmt]:
        return self._function(node)

    def transform(self, source: bytes, filename: str) -> ast.Module:
        tree = ast.parse(source, filename)
        if any(isinstance(node, ast.Name) and node.id == self.ALIAS for node in ast.walk(tree)):
            raise ValueError(f"Open WebUI uses the reserved adapter name: {filename}")
        self.visit(tree)
        index = 1 if ast.get_docstring(tree, clean=False) is not None else 0
        while index < len(tree.body) and isinstance(tree.body[index], ast.ImportFrom) and tree.body[index].module == "__future__":
            index += 1
        tree.body.insert(index, ast.ImportFrom(
            module="aihub_mods.callable_registry", names=[ast.alias(name="CallableRegistry", asname=self.ALIAS)], level=0,
        ))
        return ast.fix_missing_locations(tree)
