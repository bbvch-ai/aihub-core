import hashlib
import inspect
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import ModuleType
from unittest.mock import patch
from zipfile import ZipFile

from aihub_mods.backend_package import BackendPackage
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.callable_transform import CallableTransform


class CallableCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name: str, source: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        return path

    def test_discovery_does_not_execute_optional_code_or_advertise_unsupported_targets(self) -> None:
        self.write("__init__.py", "def root_function(): pass\n")
        self.write("not-a-module.py", "this is not valid Python")
        self.write("migrations/versions/valid_identifier.py", "def upgrade(): pass\n")
        self.write("nested/__init__.py", "def exported(): pass\n")
        marker = self.root / "executed"
        self.write("optional.py", f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
                   "import unavailable_optional_dependency\n" + '''
def helper():
    def closure(): pass
    class Local:
        def method(self): pass
    return closure
class Example:
    @staticmethod
    def static(value): return value
    @classmethod
    def factory(cls): return cls()
    @property
    def property_value(self): return 1
    @field_validator('value')
    def field(cls, value): return value
    @pydantic.model_validator(mode='after')
    def model(self): return self
    @validator('value')
    def legacy(cls, value): return value
''')
        catalog = CallableTransform.catalog(self.root)
        self.assertEqual(set(catalog), {
            "open_webui.nested:exported", "open_webui.optional:helper",
            "open_webui.optional:Example.static", "open_webui.optional:Example.factory",
        })
        self.assertFalse(marker.exists())

    def test_conditional_and_decorated_imports_leave_the_source_contract_unchanged(self) -> None:
        source = '''from contextlib import contextmanager
if choose_first:
    def value(amount): return amount
else:
    async def value(amount, extra): return amount + extra
@contextmanager
def resource(): yield 'native'
'''
        self.write("conditional.py", source)
        catalog = CallableTransform.catalog(self.root)
        baseline = json.dumps(catalog, sort_keys=True)
        token = CallableRegistry.active.set({})
        self.addCleanup(CallableRegistry.active.reset, token)
        with patch.object(CallableRegistry, "catalog", catalog):
            for first in (True, False):
                module = ModuleType("open_webui.conditional")
                module.choose_first = first
                tree = CallableTransform(module.__name__).transform(source.encode(), "conditional.py")
                exec(compile(tree, "conditional.py", "exec"), module.__dict__)
                self.assertEqual(inspect.iscoroutinefunction(module.value), not first)
                self.assertEqual(list(inspect.signature(module.value).parameters), ["amount"] if first else ["amount", "extra"])
                with module.resource() as result:
                    self.assertEqual(result, "native")
                self.assertEqual(json.dumps(CallableRegistry.catalog, sort_keys=True), baseline)
        self.assertEqual(set(catalog), {"open_webui.conditional:value", "open_webui.conditional:resource"})

    def test_changed_and_removed_source_targets_reject_a_previously_valid_publication(self) -> None:
        native = self.write("optional.py", "raise RuntimeError('Must not import')\ndef value(): return 1\n")
        target = "open_webui.optional:value"
        declared = CallableTransform.catalog(self.root)
        source = BytesIO()
        with ZipFile(source, "w") as archive:
            archive.writestr("mod.json", json.dumps({"id": "source-contract", "backend": "backend.py",
                                                   "backend_overrides": {target: "override"}}))
            archive.writestr("backend.py", "def override(next, context): return next()\n")
        content = source.getvalue()
        package = BackendPackage(hashlib.sha256(content).hexdigest(), content, "source-contract")
        self.addCleanup(package.close)
        with patch.object(CallableRegistry, "catalog", declared):
            package.check_targets(declared)
        native.write_text(native.read_text().replace("return 1", "return 2"))
        with patch.object(CallableRegistry, "catalog", CallableTransform.catalog(self.root)):
            with self.assertRaisesRegex(ValueError, "changed") as caught:
                package.check_targets(declared)
            self.assertIn(target, str(caught.exception))
        native.unlink()
        with patch.object(CallableRegistry, "catalog", CallableTransform.catalog(self.root)):
            with self.assertRaisesRegex(ValueError, "absent"):
                package.check_targets(declared)
