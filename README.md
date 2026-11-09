# agent-latency-budget

A small Hermes Agent plugin that makes tool latency observable per session.

## What it does
- `pre_tool_call` records a monotonic start time.
- `post_tool_call` stores Hermes-reported `duration_ms` (or measures fallback time) for the last 200 calls per session.
- `latency_budget_check` returns pass/fail against a configurable budget.
- `latency_budget_report` returns count / p50 / p95 / max and the slowest tool.

## Install (local)
```bash
cp -R hermes-plugin-demo ~/.hermes/plugins/agent-latency-budget
hermes plugins enable agent-latency-budget
hermes plugins doctor ~/.hermes/plugins/agent-latency-budget --ci
```

## Demo script (90 seconds)
1. Open Hermes with the plugin enabled.
2. Ask: "Run a terminal command that sleeps 2 seconds, then call latency_budget_check with budget_ms=500."
3. Expected: `verdict: exceeded`, `tool: terminal`, `elapsed_ms >= 2000`.
4. Ask: "Call latency_budget_report." Expected: p50/p95/max and `slowest_tool: terminal`.

## Design notes
- No network calls.
- No core overrides.
- Hooks never raise into the agent loop.
- State is in-memory and bounded (200 calls/session).
