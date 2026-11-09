"""Handlers for the agent-latency-budget plugin."""

from __future__ import annotations

import json
import statistics
import time

# session_id -> list of (tool_name, elapsed_ms, finished_at)
_CALLS: dict[str, list[tuple[str, float, float]]] = {}
_STARTED: dict[str, float] = {}


def _result(**kwargs) -> str:
    return json.dumps(kwargs, ensure_ascii=False)


def handle_check(args: dict, task_id: str = "", **kwargs) -> str:
    try:
        session_id = str(kwargs.get("session_id") or task_id or "default")
        calls = _CALLS.get(session_id) or []
        budget = int(args.get("budget_ms") or 2000)
        if not calls:
            return _result(ok=True, verdict="no_data", budget_ms=budget,
                           message="No tool calls observed in this session yet.")
        tool, elapsed, _ = calls[-1]
        return _result(
            ok=elapsed <= budget,
            verdict="pass" if elapsed <= budget else "exceeded",
            tool=tool,
            elapsed_ms=round(elapsed, 2),
            budget_ms=budget,
        )
    except Exception as exc:  # handlers must never raise
        return _result(ok=False, error=str(exc))


def handle_report(args: dict, task_id: str = "", **kwargs) -> str:
    try:
        session_id = str(kwargs.get("session_id") or task_id or "default")
        calls = _CALLS.get(session_id) or []
        if not calls:
            return _result(ok=True, session_id=session_id, count=0,
                           message="No tool calls observed in this session yet.")
        values = sorted(elapsed for _, elapsed, _ in calls)
        by_tool: dict[str, list[float]] = {}
        for tool, elapsed, _ in calls:
            by_tool.setdefault(tool, []).append(elapsed)
        slowest = max(by_tool.items(), key=lambda kv: max(kv[1]))
        return _result(
            ok=True,
            session_id=session_id,
            count=len(values),
            p50_ms=round(statistics.median(values), 2),
            p95_ms=round(values[min(len(values) - 1, int(len(values) * 0.95))], 2),
            max_ms=round(values[-1], 2),
            slowest_tool=slowest[0],
            tools={name: {"count": len(v), "max_ms": round(max(v), 2)}
                   for name, v in sorted(by_tool.items())},
        )
    except Exception as exc:
        return _result(ok=False, error=str(exc))


def on_pre_tool_call(tool_name: str = "", args=None, task_id: str = "", **kwargs) -> None:
    """Record start time; always returns None so the call is not blocked."""
    try:
        key = str(kwargs.get("session_id") or task_id or "default")
        _STARTED[f"{key}:{tool_name}:{kwargs.get('tool_call_id', '')}"] = time.perf_counter()
    except Exception:
        pass


def on_post_tool_call(tool_name: str = "", args=None, result=None, task_id: str = "",
                      duration_ms: int | None = None, **kwargs) -> None:
    """Record elapsed time; never raises into the agent loop."""
    try:
        session_id = str(kwargs.get("session_id") or task_id or "default")
        key = f"{session_id}:{tool_name}:{kwargs.get('tool_call_id', '')}"
        started = _STARTED.pop(key, None)
        elapsed = float(duration_ms) if duration_ms is not None else (
            (time.perf_counter() - started) * 1000 if started else 0.0)
        _CALLS.setdefault(session_id, []).append((tool_name, elapsed, time.time()))
        if len(_CALLS[session_id]) > 200:
            del _CALLS[session_id][:-200]
    except Exception:
        pass


def reset_session(session_id: str = "default") -> None:
    _CALLS.pop(session_id, None)
