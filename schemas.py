"""Tool schemas for the agent-latency-budget plugin."""

LATENCY_BUDGET_CHECK = {
    "name": "latency_budget_check",
    "description": (
        "Check whether the most recent tool call in this session exceeded its latency budget. "
        "Returns the elapsed milliseconds, the configured budget, and a pass/fail verdict. "
        "Useful before expensive workflows where a slow dependency should trigger a fallback."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "budget_ms": {
                "type": "integer",
                "description": "Latency budget in milliseconds. Defaults to the plugin setting.",
                "minimum": 1,
            }
        },
        "required": [],
    },
}

LATENCY_BUDGET_REPORT = {
    "name": "latency_budget_report",
    "description": (
        "Return latency statistics for tools observed in this session: count, p50, p95, max, "
        "and the slowest tool. Use it to decide which tool to avoid or cache."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}
