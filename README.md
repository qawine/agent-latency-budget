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

## Verified end-to-end run

`demo/e2e_demo.py` proves the plugin works through Hermes' own machinery rather than a mock:
it installs the plugin into a throwaway `HERMES_HOME`, lets Hermes' `PluginManager`
discover and load it, then calls a real built-in tool through
`model_tools.handle_function_call` — the same path the agent loop uses — so the real
`pre_tool_call` / `post_tool_call` hooks do the recording.

```bash
# from a hermes-agent checkout
.venv/bin/python demo/e2e_demo.py
```

Captured output is in `demo/expected_output.txt`. The run above recorded a real
`sleep 2` terminal call at 2454 ms, and `latency_budget_check` with a 500 ms budget
returned `verdict: exceeded`.
