#!/usr/bin/env python3
"""End-to-end demo: Hermes loads the plugin, then drives a real tool call through
the real pre_tool_call / post_tool_call hook pipeline.

Run it from a hermes-agent checkout:

    .venv/bin/python demo/e2e_demo.py

Sequence:
  1. Copy the plugin into a throwaway HERMES_HOME and enable it in config.yaml.
  2. Let Hermes discover + load it through the real PluginManager.
  3. Import a real built-in tool and call it via model_tools.handle_function_call,
     which fires the real pre_tool_call and post_tool_call hooks.
  4. Ask the plugin whether that call blew a latency budget.
  5. Print the session latency report.

Nothing here stubs the hook pipeline: the same code path the agent loop uses.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent


def hr(title: str) -> None:
    print(f"\n\033[1m── {title}\033[0m")


def main() -> int:
    home = Path(tempfile.mkdtemp(prefix="hermes-e2e-home-"))
    os.environ["HERMES_HOME"] = str(home)
    plugins_dir = home / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    hr("1. Install into a throwaway HERMES_HOME")
    shutil.copytree(PLUGIN_DIR, plugins_dir / "agent-latency-budget", dirs_exist_ok=True)
    (home / "config.yaml").write_text(
        "plugins:\n  enabled:\n    - agent-latency-budget\n", encoding="utf-8"
    )
    print(f"HERMES_HOME = {home}")
    print("config      : plugins.enabled = [agent-latency-budget]")

    hr("2. Hermes loads the plugin itself")
    from hermes_cli.plugins import discover_plugins, get_plugin_manager
    discover_plugins(force=True)
    manager = get_plugin_manager()
    print(f"has_hook('pre_tool_call') : {manager.has_hook('pre_tool_call')}")
    print(f"has_hook('post_tool_call'): {manager.has_hook('post_tool_call')}")

    from tools.registry import registry
    for name in ("latency_budget_check", "latency_budget_report"):
        entry = registry.get_entry(name)
        assert entry is not None, f"{name} missing from the real registry"
        print(f"registered tool           : {name}  (toolset={entry.toolset})")

    hr("3. Real tool call through the real hook pipeline")
    import tools.terminal_tool  # noqa: F401  (registers the built-in `terminal` tool)
    from model_tools import handle_function_call

    result = handle_function_call(
        "terminal",
        {"command": "sleep 2; echo demo-finished"},
        task_id="demo-session",
        session_id="demo-session",
        tool_call_id="demo-call-1",
    )
    print(f"terminal result: {str(result)[:100]}")

    hr("4. Did that call blow a 500 ms budget?")
    check = handle_function_call(
        "latency_budget_check", {"budget_ms": 500},
        task_id="demo-session", session_id="demo-session",
    )
    print(json.dumps(json.loads(check), indent=2))

    hr("5. Session latency report")
    report = handle_function_call(
        "latency_budget_report", {},
        task_id="demo-session", session_id="demo-session",
    )
    print(json.dumps(json.loads(report), indent=2))

    hr("Done")
    print("Hermes loaded the plugin, the real hook pipeline recorded the call,")
    print("and both tools answered through the real registry.")
    shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
