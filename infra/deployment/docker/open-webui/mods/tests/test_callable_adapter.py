import asyncio
import inspect
import json
import unittest
from collections.abc import Callable
from types import ModuleType
from typing import Any

from fastapi import WebSocket
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from aihub_mods.callable_imports import CallableImports
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.callable_transform import CallableTransform


class CallableAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.token = CallableRegistry.active.set({})
        self.globals = CallableRegistry.global_handlers
        CallableRegistry.global_handlers = {}

    def tearDown(self) -> None:
        CallableRegistry.active.reset(self.token)
        CallableRegistry.global_handlers = self.globals

    @staticmethod
    def module(source: str) -> ModuleType:
        module = ModuleType("open_webui.adapter_fixture")
        tree = CallableTransform(module.__name__).transform(source.encode(), "adapter_fixture.py")
        exec(compile(tree, "adapter_fixture.py", "exec"), module.__dict__)
        return module

    def test_aliases_chain_and_restore_without_mutating_the_original(self) -> None:
        module = self.module('def value(amount: int = 1) -> int:\n return amount\nalias = value\n')
        original = module.value
        target = "open_webui.adapter_fixture:value"
        CallableRegistry.active.set({target: (
            lambda next, *a, **k: next(*a, **k) * 2,
            lambda next, *a, **k: next(*a, **k) + 3,
        )})
        self.assertEqual(module.alias(4), 14)
        self.assertEqual(inspect.signature(original), inspect.signature(inspect.unwrap(original)))
        CallableRegistry.active.set({})
        self.assertEqual(module.alias(4), 4)
        self.assertIs(module.value, original)

    def test_native_cache_does_not_cache_tenant_modified_results(self) -> None:
        module = self.module('from functools import lru_cache\n@lru_cache\ndef value():\n return 1\n')
        target = "open_webui.adapter_fixture:value"
        for value in (10, 20):
            CallableRegistry.active.set({target: (lambda next, value=value: next() + value,)})
            self.assertEqual(module.value(), value + 1)
        self.assertEqual(module.value.cache_info().misses, 0)
        CallableRegistry.active.set({})
        self.assertEqual(module.value(), 1)
        self.assertEqual(module.value.cache_info().misses, 1)

    def test_cached_enclosing_calls_do_not_reuse_or_store_tenant_results(self) -> None:
        module = self.module('''from functools import lru_cache
calls = []
def value(): return 'original'
@lru_cache
def enclosing():
 calls.append(True)
 return value()
''')
        self.assertEqual(module.enclosing(), 'original')
        for label in ('one', 'two', 'one'):
            CallableRegistry.active.set({'open_webui.adapter_fixture:value': (lambda next, label=label: label,)})
            self.assertEqual(module.enclosing(), label)
        CallableRegistry.active.set({})
        self.assertEqual(module.enclosing(), 'original')
        self.assertEqual(len(module.calls), 4)
        self.assertEqual(module.enclosing.cache_info().hits, 1)

    async def test_async_cache_keeps_unmodified_cache_and_inner_decorators(self) -> None:
        module = self.module('''from aiocache import cached
from functools import wraps
calls = []
def guard(function):
 @wraps(function)
 async def guarded(*args, **kwargs):
  calls.append('guard')
  return await function(*args, **kwargs)
 return guarded
async def value(): return 'original'
@cached(ttl=60)
@guard
async def enclosing(): return await value()
''')
        self.assertEqual(await module.enclosing(), 'original')
        for label in ('one', 'two'):
            async def selected(next, label=label):
                return label
            CallableRegistry.active.set({'open_webui.adapter_fixture:value': (selected,)})
            self.assertEqual(await module.enclosing(), label)
        CallableRegistry.active.set({})
        self.assertEqual(await module.enclosing(), 'original')
        self.assertEqual(module.calls, ['guard', 'guard', 'guard'])

    def test_global_chain_and_pinned_execution_selection(self) -> None:
        module = self.module('def value(): return "native"\n')
        target = 'open_webui.adapter_fixture:value'
        CallableRegistry.global_handlers = {target: (lambda next: 'global-' + next(),)}
        CallableRegistry.active.set(None)
        self.assertEqual(module.value(), 'global-native')
        selection = CallableRegistry.selection({target: (lambda next: 'tenant-' + next(),)})
        CallableRegistry.active.set(selection)
        CallableRegistry.global_handlers = {target: (lambda next: 'updated-' + next(),)}
        self.assertEqual(module.value(), 'tenant-global-native')
        CallableRegistry.active.set(CallableRegistry.selection({}))
        self.assertEqual(module.value(), 'updated-native')

    def test_global_websocket_override_reaches_the_registered_endpoint(self) -> None:
        module = self.module('''from fastapi import Depends, FastAPI, WebSocket
app = FastAPI()
async def identity(): return 'verified'
@app.websocket('/socket')
async def socket(websocket: WebSocket, user: str = Depends(identity)):
 await websocket.accept()
 await websocket.send_text('native-' + user)
 await websocket.close()
''')
        CallableImports.bind_routes(module.app)

        async def override(next: Callable[..., Any], websocket: WebSocket, user: str) -> None:
            await websocket.accept()
            await websocket.send_text('overridden-' + user)
            await websocket.close()

        CallableRegistry.active.set(None)
        CallableRegistry.global_handlers = {'open_webui.adapter_fixture:socket': (override,)}
        with TestClient(module.app) as client:
            with client.websocket_connect('/socket') as socket:
                self.assertEqual(socket.receive_text(), 'overridden-verified')
            CallableRegistry.global_handlers = {}
            with client.websocket_connect('/socket') as socket:
                self.assertEqual(socket.receive_text(), 'native-verified')

    def test_registered_exception_handler_preserves_scoped_dispatch_and_disable(self) -> None:
        module = self.module('''from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.mod_scope_middleware import ModScopeMiddleware
app = FastAPI()
app.add_middleware(ModScopeMiddleware)
class Rejected(Exception): pass
@app.exception_handler(Rejected)
async def rejection(request, exc):
 return JSONResponse({'label': 'native'}, status_code=409)
@app.get('/rejected')
async def endpoint(request: Request):
 if request.headers.get('x-tenant'):
  CallableRegistry.active.set(CallableRegistry.selection(app.state.tenant_handlers))
 raise Rejected()
''')
        CallableImports.bind_routes(module.app)
        target = 'open_webui.adapter_fixture:rejection'

        def prefix(label: str) -> Callable[..., Any]:
            async def override(next: Callable[..., Any], request: Any, exc: Exception) -> JSONResponse:
                response = await next(request, exc)
                content = json.loads(response.body)
                return JSONResponse({'label': label + content['label']}, status_code=response.status_code)
            return override

        CallableRegistry.global_handlers = {target: (prefix('global-'),)}
        module.app.state.tenant_handlers = {target: (prefix('tenant-'),)}
        with TestClient(module.app) as client:
            global_response = client.get('/rejected')
            self.assertEqual(global_response.status_code, 409)
            self.assertEqual(global_response.json(), {'label': 'global-native'})
            tenant_response = client.get('/rejected', headers={'x-tenant': 'one'})
            self.assertEqual(tenant_response.status_code, 409)
            self.assertEqual(tenant_response.json(), {'label': 'tenant-global-native'})
            CallableRegistry.global_handlers = {}
            module.app.state.tenant_handlers = {}
            native_response = client.get('/rejected', headers={'x-tenant': 'one'})
            self.assertEqual(native_response.status_code, 409)
            self.assertEqual(native_response.json(), {'label': 'native'})

    def test_descriptors_keep_method_binding_and_properties(self) -> None:
        module = self.module('''class Example:
 @staticmethod
 def static(value): return value
 @classmethod
 def class_name(cls): return cls.__name__
 @property
 def prop(self): return 'property'
''')
        CallableRegistry.active.set({
            "open_webui.adapter_fixture:Example.static": (lambda next, value: next(value) + 1,),
            "open_webui.adapter_fixture:Example.class_name": (lambda next, cls: next(cls) + ' mod',),
        })
        self.assertEqual(module.Example.static(2), 3)
        self.assertEqual(module.Example.class_name(), "Example mod")
        self.assertEqual(module.Example().prop, "property")

    async def test_contexts_are_isolated_across_tasks_and_inherit_into_threads(self) -> None:
        module = self.module('def value(): return "original"\nasync def async_value(): return value()\n')
        async def selected(value: str) -> tuple[str, str]:
            token = CallableRegistry.active.set({"open_webui.adapter_fixture:value": (lambda next: value,)})
            try:
                await asyncio.sleep(0)
                return await module.async_value(), await asyncio.to_thread(module.value)
            finally:
                CallableRegistry.active.reset(token)
        self.assertEqual(await asyncio.gather(selected("one"), selected("two")), [("one", "one"), ("two", "two")])
        self.assertEqual(module.value(), "original")
        self.assertTrue(inspect.iscoroutinefunction(module.async_value))

    async def test_generators_preserve_send_throw_and_close(self) -> None:
        module = self.module('''closed = []
def stream():
 try:
  received = yield 'first'
  yield received
 except ValueError:
  yield 'caught'
 finally:
  closed.append('sync')
async def async_stream():
 try:
  received = yield 'first'
  yield received
 except ValueError:
  yield 'caught'
 finally:
  closed.append('async')
''')
        stream = module.stream()
        self.assertEqual(next(stream), "first")
        self.assertEqual(stream.send("sent"), "sent")
        self.assertEqual(stream.throw(ValueError()), "caught")
        stream.close()
        stream = module.async_stream()
        self.assertEqual(await anext(stream), "first")
        self.assertEqual(await stream.asend("sent"), "sent")
        self.assertEqual(await stream.athrow(ValueError()), "caught")
        await stream.aclose()
        self.assertEqual(module.closed, ["sync", "async"])
        self.assertTrue(inspect.isgeneratorfunction(module.stream))
        self.assertTrue(inspect.isasyncgenfunction(module.async_stream))

    async def test_context_manager_cleanup_and_hook_errors_propagate(self) -> None:
        module = self.module('''from contextlib import asynccontextmanager
closed = []
@asynccontextmanager
async def resource():
 try:
  yield 'resource'
 except ValueError:
  closed.append('error')
  raise
 finally:
  closed.append('closed')
''')
        with self.assertRaisesRegex(ValueError, "expected"):
            async with module.resource():
                raise ValueError("expected")
        self.assertEqual(module.closed, ["error", "closed"])

    def test_nested_closures_are_left_to_their_enclosing_target(self) -> None:
        module = self.module('def outer(value):\n def inner(): return value\n return inner\n')
        self.assertEqual(module.outer(3)(), 3)
        self.assertNotIn("open_webui.adapter_fixture:inner", CallableRegistry.catalog)
