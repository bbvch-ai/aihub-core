import base64
from contextlib import asynccontextmanager
from functools import wraps
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, ContextManager, Optional

import llama_index.core.instrumentation as instrument
from llama_index.core.instrumentation import Dispatcher
from openinference.instrumentation import suppress_tracing, using_session, using_tags, using_user
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import set_tracer_provider
from phoenix.trace import using_project
from pydantic import ValidationError

from lib_core.config.PhoenixConfig import PhoenixConfig
from lib_core.entities.Organization import Organization
from lib_core.records.User import User

if TYPE_CHECKING:
    pass

_TRACER_SETUP = False


def setup_tracer() -> None:
    global _TRACER_SETUP

    try:
        endpoint = PhoenixConfig().PHOENIX_ENDPOINT
        username = PhoenixConfig().PHOENIX_USERNAME
        password = PhoenixConfig().PHOENIX_PASSWORD
    except ValidationError:
        return

    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    endpoint = f"{endpoint}/v1/traces"
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    tracer_provider = trace_sdk.TracerProvider()
    set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint, headers=headers)))

    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

    _TRACER_SETUP = True


def get_dispatcher() -> Optional[Dispatcher]:
    return instrument.get_dispatcher(__name__)


def trace_fn():
    global _TRACER_SETUP

    if not _TRACER_SETUP:
        return get_dispatcher().span

    def noop_decorator(func):
        if iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return sync_wrapper

    return noop_decorator


@asynccontextmanager
async def tracing_context(
    organization: Organization,
    user: User,
    chat_id: str,
) -> ContextManager[None]:
    global _TRACER_SETUP

    if not (_TRACER_SETUP and organization.features.tracing):
        with suppress_tracing():
            yield lambda _: None
    else:
        user_mail = user.email
        if not organization.features.trace_user:
            user_mail = User.anonymous(user.locale).email
        with (
            using_project(organization.name),
            using_session(session_id=chat_id),
            using_user(user_id=user_mail),
            using_tags(tags=[user.locale]),
        ):
            yield
