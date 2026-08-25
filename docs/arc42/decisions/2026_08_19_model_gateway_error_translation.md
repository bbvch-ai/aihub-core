# Model-Gateway Failures Are Translated at the HTTP Boundary

## Context

Voice input in OpenWebUI failed with:

```
Error transcribing chunk: External: 500 Server Error: Internal Server Error for url:
http://api:8000/api/v1/active/openai/audio/transcriptions
```

Nothing in that message is true except the URL. The API's own log held the actual cause:

```
openai.BadRequestError: Error code: 400 - litellm.BadRequestError: OpenAIException -
  /audio/transcriptions: Invalid model name passed in model=whisper-large-v3.
```

`SWISS_LLM_CLOUD_WHISPER_MODEL` named a model the upstream provider does not serve. A one-line configuration fix, found
only by reading `docker logs api` by hand.

Three separate gaps turned that into an hour of blind searching:

1. **The caller was told nothing.** Every model call in this API goes through the OpenAI SDK, whose exceptions are not
   `HTTPException`. Unhandled, they left the app as Starlette's plain-text 500 — no JSON, no message. OpenWebUI parses
   `error.message` out of the body, found none, and fell back to printing the transport error.
2. **The trace named no cause.** The span itself *was* marked: `opentelemetry-instrumentation-fastapi` wraps the
   middleware stack in its own `ExceptionHandlerMiddleware`, and `trace.use_span` defaults to
   `record_exception=True` / `set_status_on_exception=True`, so an exception escaping the app already ended the server
   span `ERROR`. What the span carried was the exception *type* — `BadRequestError` on `POST
   /openai/audio/transcriptions` — and never `Invalid model name passed in model=whisper-large-v3`, because the SDK's
   message is the wrapper `Error code: 400 - {…}`. An error-filtered trace view showed the request and still did not say
   what to fix.
3. **The traceback was not exported.** The OTLP `LoggingHandler` is attached to the root logger, but gunicorn's
   `UvicornWorker` re-parents `uvicorn.error` with its own handlers and `propagate = False`. The one record carrying the
   traceback — `Exception in ASGI application` — therefore stopped at the container's stdout and never reached the
   observability backend.

Together these are self-reinforcing: a failure whose only symptom is invisible generates no ticket. `git log -S
"add_exception_handler" --all` returns zero commits, so this was never a regression — the boundary has been unhandled
since the first commit (2024-11-29), and no ADR covers error surfacing.

The trigger is recent. PR #1658 (2026-07-29) replaced the hardcoded `model: openai/whisper-large-v3` in the LiteLLM
config with `os.environ/SWISS_LLM_CLOUD_WHISPER_MODEL`, which is required because Azure and OpenAI-compatible upstreams
need different provider prefixes — and which is what first made a per-environment model name able to be wrong. That same
PR is titled "…and audio endpoint error handling": it converted the API's *own* `ValueError` raises into
`HTTPException(404)` but left the SDK's exceptions untouched.

## Decision Drivers

- **Coding convention 03 says fail fast: no defensive try-catch, let exceptions propagate**\
  Correct for services, and it must stay correct. But at the HTTP boundary "propagate" means "become an anonymous 500",
  which is not fail-fast — it is fail-silent. The codebase already catches `openai.APIError` where a fallback is needed
  (`meta_question_detector.py`), so this is a missing boundary rule, not a conflict of principle.
- **This API advertises OpenAI compatibility**\
  `OpenaiController` exists so clients can point OpenAI SDKs at it unchanged. Its errors have to be shaped like the API
  it emulates, or compatible clients cannot read them.
- **A caller must not be handed a status that misattributes the fault**\
  Reporting an upstream 401 verbatim sends clients to check credentials they never supplied.
- **What is visible must not depend on telemetry being on**\
  `OTEL_ENABLED` defaults to `False`, and a collector can be down or out of quota. Container stdout is the only signal
  always present.
- **Log volume is a cost, and it peaks exactly when things break**\
  Issue #1496 already trimmed high-cardinality metrics to control SigNoz cost. Rate-limit storms against the cloud
  provider are a known failure mode here, and a traceback per rejected request would flood the pipeline during one.
- **No new abstractions**\
  FastAPI already offers exception handlers; the runner already owns app-wide wiring.

## Decision

**Model-gateway failures are translated once, at the HTTP boundary, by `ModelGatewayErrorHandler`**
(`packages/core/swiss_ai_hub/core/exceptions/model_gateway_error_handler.py`), registered in `Runner._get_api_app` for
`APIStatusError`, `APITimeoutError` and `APIConnectionError`. Starlette resolves handlers along the exception's MRO, so
every concrete SDK error is covered by those three registrations.

It sits in `Runner` rather than `ApiRunner` because the boundary rule belongs to every app built from that base —
`packages/sysadmin-api` and `packages/bot` both do — not to one service's runner. What it does **not** do is cover the
bot's chat path: `BaseChatBot` wraps `_respond` in `try/except Exception` and `OpenaiCompletionHandler.handle_exception`
already translates `APIStatusError` itself, inside the route. An app-level handler never sees those, by design of that
class. See the trade-off below.

**1 — The status is reclassified by whose fault it is, not copied.**

| Upstream                          | Returned | Why                                                     |
| --------------------------------- | -------- | ------------------------------------------------------- |
| 400, 413, 422, 429                | as-is    | The request itself was rejected; the caller can act     |
| 401, 403, 404, all 5xx            | 502      | A provider key or model name this deployment got wrong  |
| 408, 504, timeout, connection err | 504/502  | The gateway, not the request                            |

**2 — The body carries the message under both `detail` and `error.message`.** Platform clients read FastAPI's `detail`;
the OpenAI-compatible clients this API emulates read only `error.message`. Dropping either hides the cause from one of
them. The message is the unwrapped upstream `error.message`, not the SDK's `Error code: N - {…}` wrapper.

**3 — Every such failure marks the current span `ERROR`.** Handling the exception is what makes this necessary: it no
longer propagates out of the middleware stack, so the instrumentation's exception branch never sees it and the span would
otherwise end with the status of a normal response. Marking it also deliberately departs from the OTel HTTP convention,
which leaves 4xx unset on server spans on the assumption that a 4xx is the client's fault. For a gateway that passes
upstream statuses through, that assumption is false: the incident above arrived as a 400. The SDK ignores a `set_status`
back to `UNSET`, so the instrumentation's own status setter running afterwards cannot undo this.

**4 — Log level tracks who must act, not whether the request failed.** `logger.exception` (ERROR + traceback) for
everything an operator has to fix — including 400, because that bucket carries this deployment's own faults.
`logger.warning` for 413, 422 and 429, which say nothing actionable and whose volume is worst exactly when the system is
already struggling.

**5 — The streaming chat path opens its stream in the endpoint's scope.** `client.chat.completions.create` was called
inside the generator Starlette drains after the handler returns, so an upstream rejection truncated an already-started
response and no handler could convert it. It is now awaited before `StreamingResponse` is constructed. Chat is the
dominant traffic and it streams, so without this the translation would miss the most common failure.

**6 — Server loggers are attached to the OTLP handler when they stop propagating.**
`OpenTelemetrySettings.configure_logging` now also attaches to `uvicorn`, `uvicorn.error` and `gunicorn.error`, guarded
on `propagate` being false so a still-propagating logger is not exported twice.

**7 — `trace_fn` no longer records the exception itself.** The SDK already records it and sets `ERROR` when the wrapper
re-raises out of the span context (`record_exception` and `set_status_on_exception` both default to true), so the
decorator was emitting a duplicate `exception` event and doubling every exception count in the backend. It keeps only
the queryable attributes.

## Consequences

### Positive

- The incident's cause now reaches the end user's screen: OpenWebUI displays
  `External: Invalid model name passed in model=whisper-large-v3` instead of `500 Server Error`.
- One registration covers every endpoint that talks to a model — chat, embeddings, images, STT, TTS — including the
  dynamically registered agent endpoints, and any app built from `Runner` whose route lets the exception reach the
  boundary.
- Failures are visible in three independent signals with different failure modes: the response, the span, and stdout.
  Losing telemetry no longer loses the evidence.
- Logs and traces are already correlated: `LoggingInstrumentor` injects `trace_id`/`span_id` into every record, so a log
  line pivots to its trace.
- Exception counts in the backend become accurate rather than doubled.

### Trade-offs

- **Error rate gets noisier.** Marking 4xx as span errors means a genuinely malformed client request also counts against
  the service's error rate. Accepted because the alternative is the blindness this ADR exists to remove; STT/TTS traffic
  is low and chat 4xx are rare.
- **A caller-caused 400 is logged at ERROR.** 400 cannot be split by cause at runtime — corrupt audio and a wrong model
  name arrive identically — so the ambiguous bucket is treated as ours. This over-reports rather than under-reports, on
  purpose.
- **Upstream 401/403/404 are flattened into 502.** A caller can no longer distinguish "the platform's provider key is
  wrong" from "the provider is down". That distinction is for the operator, who has the log and the span.
- **The convention now has an exception that has to be taught.** "No defensive try-catch" still holds in services, but
  the boundary rule lives only in `packages/api/CLAUDE.md` and here. A new upstream integration that raises its own SDK
  exception type will repeat the original bug until someone registers it.
- **`Runner` now knows about the OpenAI SDK, and pays for it at import.** The base class for every HTTP service gained a
  dependency on one specific upstream client. `openai` was not previously in `Runner`'s import chain and takes ~750ms to
  import, so a service that never calls a model (`sysadmin-api`) now pays that on cold start. Accepted because `openai`
  is already a direct dependency of `packages/core`, but a second gateway SDK would make this the wrong place.
- **The bot now has two translations of the same error, and the worse one wins.**
  `OpenaiCompletionHandler.handle_exception` reads `exception.body["message"]`; this handler reads the nested
  `body["error"]["message"]` that LiteLLM actually sends. The flat read misses, falls back to `exception.message`, and
  shows the caller exactly the `Error code: N - {…}` wrapper this ADR exists to remove — while `BaseChatBot`'s
  `except Exception` guarantees the app-level handler never gets the chance to do better. Pre-existing, not introduced
  here, and not fixed here either: converging them means deciding whether the bot's in-route handling should exist at
  all, which is a change to `BaseChatBot`, not to this boundary.
- **Streamed failures mid-stream are still opaque.** Only the stream *opening* moved into the endpoint's scope. A
  provider that fails after the first token still truncates the response, and no status code can be sent by then.
- **Server-logger export widens log volume.** `uvicorn.error` tracebacks now reach the paid backend. That is the point,
  but it is new volume, and unhandled exceptions elsewhere in the app will surface with it.
- **The 4xx span decision will read as a bug to anyone checking against the OTel spec.** It is documented in the code
  and here; nothing enforces it beyond that.
- **None of this fixes the misconfiguration.** `SWISS_LLM_CLOUD_WHISPER_MODEL` must still be corrected against the
  provider's `/v1/models`; this ADR only ensures the next such drift names itself.
