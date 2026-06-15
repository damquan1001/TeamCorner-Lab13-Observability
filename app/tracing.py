from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()
if not os.getenv("LANGFUSE_HOST") and os.getenv("LANGFUSE_BASE_URL"):
    os.environ["LANGFUSE_HOST"] = os.environ["LANGFUSE_BASE_URL"]

try:
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        raise ImportError("Langfuse credentials are not configured")

    from langfuse import get_client, observe

    class _LangfuseContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            get_client().update_current_trace(**kwargs)

        def update_current_observation(self, **kwargs: Any) -> None:
            usage_details = kwargs.pop("usage_details", None)
            if usage_details is not None:
                metadata = kwargs.get("metadata") or {}
                kwargs["metadata"] = {**metadata, "usage_details": usage_details}
            get_client().update_current_span(**kwargs)

        def flush(self) -> None:
            get_client().flush()

    langfuse_context = _LangfuseContext()
except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def flush_traces() -> None:
    langfuse_context.flush()
