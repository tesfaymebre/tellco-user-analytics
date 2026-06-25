# Task 1 — Streamlit Source Code Overview

**Author:** Tesfamariam Asfaw  
**Date:** June 22, 2026  
**Repository studied:** [streamlit/streamlit `develop` branch — `lib/`](https://github.com/streamlit/streamlit/tree/develop/lib)

---

## 1. Executive Summary

Streamlit's Python library (`lib/streamlit/`) is the server-side half of the framework: it executes the user's script, manages session state, serializes UI updates, and serves the app over HTTP/WebSockets. The `lib/` folder is organized as an installable package (`streamlit/`) with a parallel test suite (`tests/`), configured through `pyproject.toml`. Business logic is split by concern — UI elements, runtime execution, web server, and protobuf messaging — so each layer can be developed and tested independently.

---

## 2. Repository & Package Structure

### 2.1 Top-level layout of `lib/`

| Path | Purpose |
|------|---------|
| `lib/streamlit/` | Main Python package: all production code that powers `import streamlit as st` |
| `lib/tests/` | Pytest suite mirroring `streamlit/`; targets 95%+ unit-test coverage |
| `lib/pyproject.toml` | Package metadata, runtime dependencies, pytest/coverage configuration |

### 2.2 Key subpackages inside `lib/streamlit/`

| Subpackage | Responsibility | Example file |
|------------|----------------|--------------|
| `elements/` | Backend implementation of each `st.*` widget and display element | `elements/widgets/button.py` |
| `runtime/` | Script execution, caching, session state, app lifecycle | `runtime/scriptrunner/script_runner.py` |
| `web/` | CLI entry point (`streamlit run`) and Starlette/Uvicorn web server | `web/cli.py` |
| `commands/` | Non-UI `st` commands (configuration, secrets, page config) | `commands/page_config.py` |
| `connections/` | `st.connection` backends for SQL, Snowflake, Snowpark | `connections/sql_connection.py` |
| `proto/` | Auto-generated Protocol Buffer message classes for client–server communication | `proto/ForwardMsg_pb2.py` |

### 2.3 Architecture diagram

```
User script (app.py)
       │
       ▼
ScriptRunner ── executes script top-to-bottom on each rerun
       │
       ▼
DeltaGenerator (st.* API) ── records UI "deltas"
       │
       ▼
Runtime + SessionState ── manages sessions, widget values, cache
       │
       ▼
ForwardMsg (protobuf) ── serialized over WebSocket
       │
       ▼
React frontend ── renders widgets in the browser
```

---

## 3. Advanced Python Techniques Observed

| Technique | Where you saw it | Why Streamlit uses it |
|-----------|------------------|------------------------|
| Generics (`TypeVar`, `ParamSpec`, `Generic`) | `runtime/caching/cache_utils.py` — `CachedFunc(Generic[P, R])` | Preserves type safety when wrapping arbitrary user functions with `@st.cache_data` |
| Descriptor protocol (`__get__`) | `CachedFunc.__get__` in `cache_utils.py` | Allows cache decorators to work correctly on instance methods (binds `self`) |
| Abstract base classes (`@abstractmethod`) | `Cache` class in `cache_utils.py` | Defines a contract for pluggable cache backends (memory, disk) |
| Singleton pattern | `Runtime.instance()` in `runtime/runtime.py` | Ensures one application runtime coordinates all browser sessions |
| Protocol Buffers code generation | `proto/` directory | Efficient, schema-versioned messages between Python server and React client |
| Type-checking guard (`TYPE_CHECKING`) | `errors.py` — imports under `if TYPE_CHECKING:` | Avoids circular imports at runtime while keeping full type hints for mypy |
| `@property` | `CachedFuncInfo.cache_type` in `cache_utils.py` | Exposes cache-type metadata without storing duplicate state on every instance |
| Custom decorators | `@st.cache_data`, `@st.cache_resource`, `@st.fragment` | Add caching, resource lifecycle, and partial-rerun behavior without changing user function bodies |

---

## 4. Dependencies (`lib/pyproject.toml`)

> Streamlit uses `pyproject.toml`, not a separate `requirements.txt` inside `lib/`.

### 4.1 Core runtime dependencies

| Package | Version constraint | Role in Streamlit |
|---------|-------------------|-------------------|
| `starlette` / `uvicorn` | `starlette>=0.40.0`, `uvicorn>=0.30.0` | ASGI web framework and server that host the app and WebSocket endpoints |
| `protobuf` | `>=3.20,<8` | Serializes ForwardMsg/BackMsg between Python backend and React frontend |
| `pandas` / `numpy` | `pandas>=1.4.0,<4`, `numpy>=1.23,<3` | Native data structures for charts, tables, and dataframe display |
| `websockets` | `>=12.0.0` | Real-time bidirectional communication for live UI updates |
| `cachetools` | `>=5.5,<8` | TTL and size-bounded caches backing `@st.cache_data` |

### 4.2 Optional dependency groups

Streamlit uses `[project.optional-dependencies]` so users install only what they need:

- **`charts`** — `matplotlib`, `plotly`, `graphviz` for extended visualizations
- **`sql`** — `SQLAlchemy>=2.0.0` for `st.connection("sql", ...)`
- **`snowflake`** — Snowpark/Snowflake connector for cloud data warehouses
- **`auth`** — `Authlib` for OAuth-based authentication
- **`performance`** — `orjson`, `uvloop` for faster serialization and event loops
- **`all`** — installs every optional group plus `rich` for improved tracebacks

This keeps the default install lean — a deliberate design choice documented in `pyproject.toml`.

---

## 5. Docstrings, Logging & Error Handling

### 5.1 Docstring style

`lib/AGENTS.md` mandates **NumPy-style docstrings** for all user-facing modules. Docstrings are written for **callers of an API**, not for future maintainers (internal notes belong in `#` comments). Example from `logger.py`:

```python
def get_logger(name: str) -> logging.Logger:
    """Return a logger.

    Parameters
    ----------
    name : str
        The name of the logger to use. You should just pass in __name__.

    Returns
    -------
    Logger
    """
```

### 5.2 Logging

`logger.py` provides a centralized `get_logger(name)` factory. All loggers share a global log level (`set_log_level`), a custom console formatter, and are cached in a module-level `_loggers` dict. Callers use `get_logger(__name__)` — the standard Python pattern — so log output is namespaced (e.g. `streamlit.runtime.caching.cache_utils`).

### 5.3 Error handling

`errors.py` defines a hierarchy rooted at `streamlit.errors.Error`. Subclasses cover specific domains:

- **`StreamlitAPIException`** — user misused the API (wrong argument, called outside script context)
- **`CacheError` / `UnhashableParamError`** — caching failures with actionable messages
- **`CustomComponentError`** — third-party component failures

User-facing errors use clear, templated messages (not bare tracebacks). Internal code catches low-level exceptions and re-raises domain-specific ones so the UI can display helpful guidance.

---

## 6. Testing Strategy

### 6.1 Unit tests

Tests live in `lib/tests/`, structured to mirror `lib/streamlit/`. Key patterns from `lib/tests/AGENTS.md`:

- Prefer plain `def test_*` pytest functions over `unittest.TestCase`
- Target **95%+ coverage** on `lib/streamlit`
- Use **`@pytest.mark.parametrize`** for input/output matrices
- Add **negative/regression tests** (invalid input raises expected exception)
- NumPy-style docstrings on every test function
- Full type annotations on test signatures

Pytest is configured in `pyproject.toml` with `--cov=streamlit`, custom markers (`slow`, `require_integration`, `performance`), and warning filters for third-party libraries.

### 6.2 Integration tests

Tests that need packages from `[dependency-groups] integration` (e.g. `sqlalchemy`, `polars`) must:

1. Import those packages **inside** the test function
2. Be marked with **`@pytest.mark.require_integration`**

This lets the suite skip gracefully when integration dependencies are not installed.

### 6.3 Example test studied

**File:** `lib/tests/streamlit/runtime/caching/cache_utils_test.py`

**What it verifies:** `get_session_id_or_throw()` returns the session ID when a script context exists, and raises `StreamlitAPIException` when called outside a running app.

**Technique used:** `unittest.mock.patch` on `get_script_run_ctx` to simulate runtime context without starting a web server — a clean unit-test isolation pattern.

**Possible extension:** Add a test for concurrent cache access under `compute_value_lock` to verify double-checked locking behavior.

---

## 7. Decorators & Properties

### 7.1 Built-in / standard decorators

| Decorator | Example location | Purpose |
|-----------|-----------------|---------|
| `@abstractmethod` | `Cache.read_result`, `Cache.write_result` | Force subclasses to implement cache storage |
| `@overload` | `CachedFunc.clear()` | Type-safe signatures for overloaded `clear()` with/without args |
| `@pytest.mark.parametrize` | `cache_utils_test.py` — `test_get_positional_arg_name` | One test function, many input/output pairs |

### 7.2 Custom Streamlit decorators

| Decorator | File | What it wraps / controls |
|-----------|------|--------------------------|
| `@st.cache_data` | `runtime/caching/cache_data_api.py` | Caches serializable return values (DataFrames, numbers); keyed by function args |
| `@st.cache_resource` | `runtime/caching/cache_resource_api.py` | Caches non-serializable resources (DB connections, ML models); one instance per session/global |
| `@st.fragment` | `runtime/fragment.py` | Runs only a portion of the script on widget interaction — partial reruns for performance |

### 7.3 `@property` usage

`CachedFuncInfo.cache_type` is declared as a `@property` raising `NotImplementedError` in the base class, forcing each cache variant (`cache_data` vs `cache_resource`) to declare its type. This avoids storing redundant metadata while keeping the interface uniform across cache implementations.

---

## 8. Lessons for the TellCo Project

- **Modular package layout:** Mirror Streamlit's split — `data/` and `analysis/` for logic, `notebooks/` for exploration, future `app/` for Streamlit dashboard — so each layer is independently testable.
- **Testing:** Write pytest unit tests for aggregation and cleaning functions; keep notebooks thin (call library code, display results).
- **Error messages / logging:** Use a small custom exception hierarchy and `logging.getLogger(__name__)` in database and analysis modules for debuggable failures.
- **Separation of data logic vs UI:** Notebooks and the Streamlit dashboard should import from `tellco_user_analytics`, never embed SQL or clustering logic inline.

---

## 9. Personal Observations

Three things stood out:

1. **Minimal dependency philosophy** — Streamlit explicitly discourages adding packages and documents version bounds carefully. This is good practice for library maintainers and applies to our project too.
2. **The rerun model** — The entire script re-executes on each interaction, with SessionState preserving widget values. Understanding this explains why expensive operations must be cached or moved to modules called via `@st.cache_data`.
3. **Mixin composition on DeltaGenerator** — The `st` namespace is built by mixing in dozens of element modules rather than one giant class. This is a scalable pattern we can follow as our analysis modules grow.

---

## References

- [Streamlit lib source](https://github.com/streamlit/streamlit/tree/develop/lib)
- [Streamlit lib AGENTS.md](https://github.com/streamlit/streamlit/blob/develop/lib/AGENTS.md)
- [Streamlit tests AGENTS.md](https://github.com/streamlit/streamlit/blob/develop/lib/tests/AGENTS.md)
- [Streamlit pyproject.toml](https://github.com/streamlit/streamlit/blob/develop/lib/pyproject.toml)
