# Langfuse Python SDK — Tracing & Evals (Self-Hosted, Free)

> **Research Date:** 2026-04  
> **Python SDK:** `langfuse==4.0.6` (requires Python ≥ 3.10)  
> **Server Image:** `langfuse/langfuse:v3.166.0` (2026-04-08)  
> **Source verified against:** [langfuse/langfuse-python @ v4.0.6](https://github.com/langfuse/langfuse-python) (cloned to `repos/langfuse-python/`)  
> **Architecture:** v4 is a **complete rewrite**. The SDK is now fully OpenTelemetry-native — it sends OTLP HTTP spans directly. Do not rely on v3 docs.

---

## 1. What Changed in v4 (vs v3)

| Aspect | v3 | v4 |
|--------|----|----|
| Protocol | Custom HTTP REST trace ingestion | **OpenTelemetry OTLP HTTP** |
| Core abstraction | Custom `trace` / `span` objects | OTel `TracerProvider` + `BatchSpanProcessor` |
| Auth | Bearer token headers | **Basic Auth** (public_key:secret_key bas64 in OTLP headers) |
| Ingest endpoint | `/api/public/traces` | `/api/public/otel/v1/traces` |
| Env var for host | `LANGFUSE_HOST` | **`LANGFUSE_BASE_URL`** (`HOST` is deprecated) |
| `host` constructor arg | ✅ | ⚠️ Deprecated — use `base_url` |
| `blocked_instrumentation_scopes` | ✅ | ⚠️ Deprecated — use `should_export_span` callback |
| Min Python version | 3.8 | **3.10** |

---

## 2. Self-Hosted Docker Compose Setup

The official approach is to clone the langfuse repo and use the bundled `docker-compose.yml`.

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
# Edit docker-compose.yml — update all lines marked # CHANGEME
docker compose up
```

After 2–3 minutes the UI is at **http://localhost:3000**.

The compose stack includes:
- `langfuse-web` — Next.js UI + API server (port 3000)
- `langfuse-worker` — background job processor
- `postgres` — database
- `minio` — S3-compatible blob storage for media

### Pinning to a specific version

If you want to pin to the tested server version instead of using `latest`:

```yaml
# docker-compose.yml (excerpt)
services:
  langfuse-web:
    image: langfuse/langfuse:v3.166.0
  langfuse-worker:
    image: langfuse/langfuse-worker:v3.166.0
```

### Required environment variables in docker-compose.yml

| Variable | Purpose | Note |
|----------|---------|-------|
| `NEXTAUTH_SECRET` | Auth token signing | Must be long random string |
| `ENCRYPTION_KEY` | At-rest encryption | 64 hex chars |
| `SALT` | Hashing | Random string |
| `DATABASE_URL` | Postgres connection string | |
| `NEXTAUTH_URL` | Public URL of the UI | `http://localhost:3000` for local |

After starting, create a project in the UI → Settings → API Keys, and copy the `pk-lf-...` and `sk-lf-...` values.

---

## 3. Installing the Python SDK

```bash
pip install langfuse==4.0.6
# or without pinning:
pip install langfuse
```

**Required transitive deps (resolved automatically):**  
`httpx`, `pydantic>=2`, `backoff`, `wrapt`, `opentelemetry-api>=1.33.1`, `opentelemetry-sdk>=1.33.1`, `opentelemetry-exporter-otlp-proto-http>=1.33.1`

---

## 4. Configuration

### Environment variables (preferred)

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="http://localhost:3000"   # ← self-hosted. NOT _HOST (deprecated)
```

All supported env vars (from `langfuse/_client/environment_variables.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGFUSE_PUBLIC_KEY` | — | Project public key |
| `LANGFUSE_SECRET_KEY` | — | Project secret key |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` | Server URL |
| `LANGFUSE_HOST` | — | **DEPRECATED** — use `LANGFUSE_BASE_URL` |
| `LANGFUSE_TRACING_ENABLED` | `True` | Disable entirely without code changes |
| `LANGFUSE_DEBUG` | `False` | Verbose SDK logging |
| `LANGFUSE_FLUSH_AT` | OTel BSP default | Batch size before send |
| `LANGFUSE_FLUSH_INTERVAL` | OTel BSP default | Max delay between flushes (ms) |
| `LANGFUSE_SAMPLE_RATE` | `1.0` | 0.0–1.0 fraction of spans to export |
| `LANGFUSE_TIMEOUT` | `5` (seconds) | API request timeout |
| `LANGFUSE_TRACING_ENVIRONMENT` | `"default"` | Environment label (prod/staging/dev) |
| `LANGFUSE_RELEASE` | — | App version / git sha for analytics grouping |
| `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED` | `True` | Auto-capture args/return in `@observe` |
| `LANGFUSE_OTEL_TRACES_EXPORT_PATH` | `/api/public/otel/v1/traces` | OTLP ingest path |
| `LANGFUSE_MEDIA_UPLOAD_ENABLED` | `True` | Detect and upload media blobs |
| `LANGFUSE_MEDIA_UPLOAD_THREAD_COUNT` | `1` | Parallel upload threads |
| `LANGFUSE_PROMPT_CACHE_DEFAULT_TTL_SECONDS` | `60` | Prompt template cache TTL |

### Constructor-based initialization

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    base_url="http://localhost:3000",   # self-hosted
    tracing_enabled=True,
    environment="development",
    release="v1.2.3",
    flush_interval=500,                # ms, lower for dev
    sample_rate=1.0,
    # mask=my_mask_fn,                 # callable to redact sensitive fields
    # should_export_span=my_filter_fn, # callable(span) -> bool
)
```

Full `Langfuse.__init__` signature (from `langfuse/_client/client.py`):
```python
Langfuse(
    *,
    public_key=None, secret_key=None, base_url=None,
    host=None,                         # DEPRECATED
    timeout=None, httpx_client=None, debug=False,
    tracing_enabled=True, flush_at=None, flush_interval=None,
    environment=None, release=None, media_upload_thread_count=None,
    sample_rate=None, mask=None,
    blocked_instrumentation_scopes=None,  # DEPRECATED
    should_export_span=None, additional_headers=None,
    tracer_provider=None               # Bring-your-own OTel TracerProvider
)
```

**`base_url` resolution order:**  
`base_url` param → `LANGFUSE_BASE_URL` env → `host` param → `LANGFUSE_HOST` env → `"https://cloud.langfuse.com"`

---

## 5. Tracing

### 5.1 `@observe` decorator (simplest)

Decorate any sync or async function. The decorator automatically:
- Creates a span when the function is called
- Captures function arguments as `input`
- Captures the return value as `output`
- Ends the span on return/exception

```python
from langfuse import observe

@observe(name="my-pipeline", as_type="span")
def run_pipeline(user_query: str) -> str:
    result = call_llm(user_query)
    return result

@observe(name="call-llm", as_type="generation")
def call_llm(prompt: str) -> str:
    # your LLM call here
    return "answer"

run_pipeline("What is 2+2?")
```

`@observe` signature (from `langfuse/_client/observe.py`):
```python
@observe(
    func=None,          # the decorated function (positional, internal)
    *,
    name=None,          # span name (defaults to function name)
    as_type=None,       # see table below
    capture_input=None, # override LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED
    capture_output=None,
    transform_to_string=None,   # callable to stringify non-JSON-serializable outputs
)
```

**`as_type` values:**

| Value | Meaning |
|-------|---------|
| `"span"` | Generic span (default) |
| `"generation"` | LLM generation — enables model/token cost fields |
| `"chain"` | Sequential multi-step pipeline |
| `"embedding"` | Embedding computation |
| `"event"` | Instantaneous event (no duration) |
| `"retriever"` | Vector/keyword retrieval |
| `"agent"` | Autonomous agent step |
| `"tool"` | Tool/function call |
| `"guardrail"` | Safety / content filtering check |
| `"evaluator"` | Inline evaluation step |

**Passing parent key to a decorated function** (rare, multi-project):
```python
@observe(as_type="generation")
def generate(prompt):
    ...

# Pass langfuse_parent_observation_id as kwarg to control parent span
generate(prompt, langfuse_parent_observation_id="<span-id>")
```

**Async example:**
```python
import asyncio
from langfuse import observe

@observe(as_type="agent")
async def run_agent(input: str) -> str:
    await asyncio.sleep(0.1)
    return "done"
```

### 5.2 `start_as_current_observation` context manager

For explicit control over span lifecycle. The created span is the active span in the OTel context — any `@observe` calls inside will nest under it.

```python
from langfuse import Langfuse

langfuse = Langfuse()

with langfuse.start_as_current_observation(
    name="handle-request",
    as_type="span",
    input={"query": "hello"},
) as span:
    result = do_work()
    span.update(output=result, metadata={"source": "cache"})
    # span ends automatically on context exit (end_on_exit=True by default)
```

**Nested spans:**
```python
with langfuse.start_as_current_observation(name="pipeline", as_type="chain") as chain:
    with langfuse.start_as_current_observation(
        name="retrieval",
        as_type="retriever",
        input={"query": "langfuse docs"},
    ) as retrieval:
        docs = retrieve(query)
        retrieval.update(output=docs)

    with langfuse.start_as_current_observation(
        name="llm-call",
        as_type="generation",
        model="gpt-4o-mini",
        model_parameters={"temperature": 0.7},
    ) as gen:
        response = call_llm(docs)
        gen.update(
            output=response,
            usage_details={"input": 500, "output": 120},
            cost_details={"input": 0.0003, "output": 0.00024},
        )
```

`start_as_current_observation` signature:
```python
langfuse.start_as_current_observation(
    *,
    trace_context=None,      # dict {"trace_id": ..., "parent_span_id": ...} for remote parent
    name: str,
    as_type="span",
    input=None, output=None, metadata=None,
    version=None, level=None, status_message=None,
    completion_start_time=None,  # for generation/embedding types
    model=None,                  # for generation/embedding types
    model_parameters=None,       # for generation/embedding types
    usage_details=None,          # dict[str, int] e.g. {"input": 500, "output": 120}
    cost_details=None,           # dict[str, float] e.g. {"input": 0.0003}
    prompt=None,                 # PromptClient from prompt management
    end_on_exit=None,            # default True; if False, call .end() manually
)
```

### 5.3 `start_observation` (manual lifecycle)

Creates a span but does NOT set it as the active OTel span. Must call `.end()` manually.

```python
span = langfuse.start_observation(name="background-task", as_type="span")
try:
    result = do_work()
    span.update(output=result)
finally:
    span.end()
```

### 5.4 Span methods

All span types (returned by `start_observation` / `start_as_current_observation` / `@observe`) share these methods, defined in `LangfuseObservationWrapper` (`langfuse/_client/span.py`):

#### `.update(**kwargs)`

```python
span.update(
    name=None,                  # rename the span
    input=None,                 # overwrite input
    output=None,                # set output
    metadata=None,              # set metadata
    version=None,
    level=None,                 # "DEFAULT" | "DEBUG" | "WARNING" | "ERROR"
    status_message=None,
    # generation-only:
    completion_start_time=None,
    model=None,
    model_parameters=None,
    usage_details=None,
    cost_details=None,
    prompt=None,
)
```

#### `.end(end_time=None)`

Ends the span. `end_time` is nanoseconds since epoch (optional).

#### `.score(name, value, ...)`

Scores **this specific span (observation)**:

```python
span.score(
    name="relevance",
    value=0.9,                  # float for NUMERIC/BOOLEAN, str for CATEGORICAL
    data_type="NUMERIC",        # optional
    comment="Looks correct",    # optional
    config_id=None,             # optional score config UUID from Langfuse UI
    score_id=None,              # auto-generated if omitted
    timestamp=None,
    metadata=None,
)
```

#### `.score_trace(name, value, ...)`

Same signature as `.score()`, but scores the **entire trace** this span belongs to.

#### `.set_trace_io(input, output)` ⚠️ Deprecated

Legacy method for trace-level input/output. Use `propagate_attributes()` instead.

### 5.5 Setting trace-level attributes (user_id, session_id, tags)

In v4, trace attributes (user_id, session_id, tags) are set via **`propagate_attributes()`**, not on the `Langfuse` client or span constructor.

```python
from langfuse import Langfuse

langfuse = Langfuse()

with langfuse.start_as_current_observation(name="user-request") as span:
    with langfuse.propagate_attributes(
        user_id="user-42",
        session_id="session-abc",
        tags=["production", "v2"],
        trace_name="chat-completion",
        metadata={"experiment": "variant-b"},
        version="2.0.1",
    ):
        # ALL spans created inside this context inherit these attributes
        response = call_llm(user_query)
        span.update(output=response)
```

`propagate_attributes` signature (from `langfuse/_client/propagation.py`):
```python
langfuse.propagate_attributes(
    user_id=None,        # str ≤200 ASCII chars
    session_id=None,     # str ≤200 ASCII chars
    metadata=None,       # dict[str, str] — values ≤200 chars
    version=None,        # str
    tags=None,           # list[str]
    trace_name=None,     # str ≤200 ASCII chars
    as_baggage=False,    # if True, propagates via HTTP headers (cross-service)
)
```

> **Important:** Call `propagate_attributes` as early as possible in your trace. Spans created _before_ entering this context will NOT have the attributes set.

### 5.6 `get_client()` — global singleton access

When you don't want to thread the `langfuse` instance through your call stack:

```python
from langfuse import Langfuse, get_client

# Initialize once at startup
Langfuse(public_key="pk-lf-...", secret_key="sk-lf-...", base_url="http://localhost:3000")

# Anywhere else:
client = get_client()
```

`get_client()` behaviour:
- **Single project:** Returns the existing initialized client
- **No client initialized:** Creates a new one (reads from env vars)
- **Multiple projects, no key:** Returns a **disabled** client (to prevent cross-project data leakage)
- **Multi-project with key:** `get_client(public_key="pk-lf-...")` returns the matching client

### 5.7 Flush & shutdown

> Critical: The SDK uses an async batch exporter. In short-lived scripts, you MUST call `flush()` or `shutdown()` before exit.

```python
# Block until all spans are exported
langfuse.flush()

# Or: flush + teardown TracerProvider
langfuse.shutdown()
```

In long-running services (FastAPI, etc.) this is usually not needed since the BSP flushes on its own schedule.

---

## 6. Scoring

### 6.1 Inline scoring via span

The simplest path — score a span as part of normal code flow:

```python
@observe(as_type="generation")
def call_llm(prompt):
    response = llm(prompt)
    # Get the current span and score it
    from langfuse import get_client
    client = get_client()
    span = client.get_current_observation()   # returns current active span
    span.score(name="accuracy", value=0.85, comment="Manual check")
    return response
```

### 6.2 Online scoring from outside the trace

Score after the fact using only `trace_id`:

```python
langfuse.create_score(
    trace_id="<trace-id>",           # required
    name="human-rating",
    value=4.0,
    data_type="NUMERIC",
    comment="Good answer",
    observation_id=None,             # if None, scores the trace, not a span
    config_id=None,
    metadata=None,
)
```

`create_score` overloads support:
- `value: float` + `data_type=NUMERIC` or `BOOLEAN`
- `value: str` + `data_type=CATEGORICAL`

---

## 7. Batch Evaluation (Post-hoc Evals at Scale)

Run evaluation functions over existing traces stored in Langfuse — no re-execution needed.

### 7.1 Core types

**`EvaluatorInputs`** — returned by your mapper, fed into evaluators:
```python
from langfuse import EvaluatorInputs

EvaluatorInputs(
    input=...,           # the input sent to the model
    output=...,          # the model response to evaluate
    expected_output=..., # optional ground truth
    metadata={},         # optional dict for extra context
)
```

**`Evaluation`** — returned by evaluator functions:
```python
from langfuse import Evaluation

Evaluation(
    name="accuracy",          # metric name (consistent across runs!)
    value=0.95,               # float, str, or bool
    comment="Correct",        # optional
    metadata={},              # optional
    data_type=None,           # "NUMERIC" | "CATEGORICAL" | "BOOLEAN"
    config_id=None,           # optional score config UUID
)
```

**`MapperFunction`** (Protocol) — transforms a trace or observation into `EvaluatorInputs`:
```python
def my_mapper(*, item) -> EvaluatorInputs:
    return EvaluatorInputs(
        input=item.input,
        output=item.output,
        expected_output=None,
        metadata={"trace_id": item.id},
    )
```
- `item` is `TraceWithFullDetails` when `scope="traces"`
- `item` is `ObservationsView` when `scope="observations"`
- Can also be `async def`

### 7.2 Running a batch evaluation

```python
from langfuse import Langfuse, EvaluatorInputs, Evaluation

langfuse = Langfuse()

def map_trace(*, item) -> EvaluatorInputs:
    return EvaluatorInputs(
        input=item.input,
        output=item.output,
    )

def score_exact_match(*, input, output, expected_output=None, metadata=None, **kwargs):
    if expected_output is None:
        return Evaluation(name="exact_match", value=0, comment="No ground truth")
    correct = str(output).strip() == str(expected_output).strip()
    return Evaluation(
        name="exact_match",
        value=1.0 if correct else 0.0,
        comment="Match" if correct else "Mismatch",
    )

result = langfuse.run_batched_evaluation(
    scope="traces",              # "traces" | "observations"
    mapper=map_trace,
    evaluators=[score_exact_match],
    filter='[{"type":"stringOptions","column":"name","operator":"any of","value":["my-pipeline"]}]',  # optional JSON filter
    fetch_batch_size=50,         # traces per API call (default 50)
    fetch_trace_fields=None,     # list of extra fields to fetch
    max_items=None,              # limit total items evaluated
    max_concurrency=5,           # parallel evaluator coroutines
    composite_evaluator=None,    # CompositeEvaluatorFunction for aggregate scores
    metadata={"run_description": "nightly eval"},
    max_retries=3,
    verbose=True,
    resume_from=None,            # BatchEvaluationResumeToken for pause/resume
)

print(result)   # BatchEvaluationResult
```

`run_batched_evaluation` is defined on `Langfuse` in `langfuse/_client/client.py` and delegates to `BatchEvaluationRunner`.

### 7.3 Resumable batch runs

For large datasets that might fail mid-run:
```python
token = result.resume_token       # BatchEvaluationResumeToken
# Later / after failure:
result2 = langfuse.run_batched_evaluation(..., resume_from=token)
```

### 7.4 Composite evaluator

Aggregate individual item scores into a batch-level metric:
```python
from langfuse import CompositeEvaluatorFunction, EvaluatorStats

def my_composite(*, evaluator_stats: EvaluatorStats, **kwargs) -> list[Evaluation]:
    avg = evaluator_stats.mean("exact_match")
    return [Evaluation(name="batch_accuracy", value=avg)]

result = langfuse.run_batched_evaluation(
    ...,
    composite_evaluator=my_composite,
)
```

---

## 8. Auto-instrumentation (OpenAI, LangChain, etc.)

Because v4 is OTel-native, you can combine it with OTel auto-instrumentation libraries:

```python
from langfuse import Langfuse
from openai import OpenAI

langfuse = Langfuse()  # sets up the OTel TracerProvider

# OpenAI auto-instrumentation (if using opentelemetry-instrumentation-openai)
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
OpenAIInstrumentor().instrument()

# Or use langfuse's built-in openai integration
from langfuse.openai import openai

client = openai.OpenAI()  # drop-in replacement; spans auto-created
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## 9. Complete Working Example (Self-Hosted)

```python
import os
from langfuse import Langfuse, observe, propagate_attributes, EvaluatorInputs, Evaluation

# --- Config ---
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-..."
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-..."
os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000"

langfuse = Langfuse()

# --- Tracing with @observe ---

@observe(as_type="retriever", name="retrieve-docs")
def retrieve(query: str) -> list[str]:
    return [f"doc about {query}"]

@observe(as_type="generation", name="generate-answer")
def generate(context: list[str], query: str) -> str:
    # Simulate LLM call
    return f"Answer based on {context[0]}"

@observe(as_type="chain", name="rag-pipeline")
def rag(query: str) -> str:
    docs = retrieve(query)
    answer = generate(docs, query)
    return answer


def handle_user_request(user_id: str, session_id: str, query: str) -> str:
    with langfuse.start_as_current_observation(name="user-request", as_type="span") as span:
        with langfuse.propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=["production"],
        ):
            result = rag(query)
            span.update(output=result)

            # Online score
            span.score_trace(name="pipeline-ran", value=1.0, data_type="BOOLEAN")

            return result


# --- Run ---
answer = handle_user_request("user-42", "sess-001", "What is Langfuse?")
print(answer)

# IMPORTANT: flush before exit in scripts
langfuse.flush()


# --- Batch evaluation (post-hoc) ---

def trace_mapper(*, item) -> EvaluatorInputs:
    return EvaluatorInputs(
        input=item.input,
        output=item.output,
        expected_output=None,
    )

def length_check(*, input, output, **kwargs) -> Evaluation:
    return Evaluation(
        name="output_length_ok",
        value=1.0 if len(str(output)) > 10 else 0.0,
        data_type="BOOLEAN",
    )

eval_result = langfuse.run_batched_evaluation(
    scope="traces",
    mapper=trace_mapper,
    evaluators=[length_check],
    max_items=100,
    verbose=True,
)
print(eval_result)
```

---

## 10. Common Gotchas

| Gotcha | Fix |
|--------|-----|
| Using `LANGFUSE_HOST` env var | Use `LANGFUSE_BASE_URL` instead (HOST is deprecated in v4) |
| Using `host=` constructor arg | Use `base_url=` instead |
| Script exits silently with no data | Call `langfuse.flush()` before exit |
| Multi-project setup with no `public_key` in `get_client()` | Returns a disabled client — pass `public_key` explicitly |
| Trace attributes (user_id) not aggregating | Call `propagate_attributes()` BEFORE creating child spans |
| `@observe` not capturing i/o | Set `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED=true` (default is true) |
| Using `set_trace_io()` | Deprecated — use `propagate_attributes()` |
| Using `blocked_instrumentation_scopes` | Deprecated — use `should_export_span` callable |
| Minimal Docker compose lacking media uploads | MinIO inside compose is not externally reachable by default; configure blob storage for multimodal tracing |

---

## 11. Source File Map (repos/langfuse-python @ v4.0.6)

| File | Contents |
|------|---------|
| `langfuse/__init__.py` | All public exports |
| `langfuse/_client/client.py` | `Langfuse` class (init, create_score, flush, shutdown, run_batched_evaluation, start_observation, start_as_current_observation, propagate_attributes) |
| `langfuse/_client/observe.py` | `@observe` decorator (sync + async) |
| `langfuse/_client/span.py` | `LangfuseObservationWrapper`, `LangfuseSpan`, `LangfuseGeneration` — update(), end(), score(), score_trace() |
| `langfuse/_client/get_client.py` | `get_client()` singleton function |
| `langfuse/_client/propagation.py` | `propagate_attributes()` context manager, `propagated_keys` |
| `langfuse/_client/environment_variables.py` | All env var constants with defaults |
| `langfuse/_client/attributes.py` | OTel attribute key constants (`LangfuseOtelSpanAttributes`) |
| `langfuse/batch_evaluation.py` | `EvaluatorInputs`, `MapperFunction`, `CompositeEvaluatorFunction`, `BatchEvaluationRunner`, `BatchEvaluationResumeToken`, `BatchEvaluationResult` |
| `langfuse/experiment.py` | `Evaluation` dataclass |
| `langfuse/openai.py` | OpenAI drop-in wrapper |
| `langfuse/langchain/` | LangChain callback handler |

---

## 12. Doc vs Code Discrepancies Found

| Doc claim | Actual (source-verified) |
|-----------|--------------------------|
| Docs reference `/docs/sdk/python/sdk-v3` URL path | v4 is a full rewrite — architecture is completely different. v3 docs describe custom trace REST API; v4 uses OTLP HTTP. |
| `host` parameter mentioned in older examples | `host` is deprecated; `base_url` is the correct parameter in v4 |
| `blocked_instrumentation_scopes` documented as active feature | Deprecated in v4 — use `should_export_span` callable instead |
| `set_trace_io()` used in some examples | Deprecated in v4 with `@deprecated` decorator — use `propagate_attributes()` |
| OTelTraceExporter docs show `/api/public/otel` path prefix | Full path is `/api/public/otel/v1/traces` (from `LANGFUSE_OTEL_TRACES_EXPORT_PATH`) |
