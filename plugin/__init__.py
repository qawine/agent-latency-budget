"""Hermes plugin: per-session tool latency budget + report.

Why this exists: agent pipelines silently tolerate slow tools. This plugin turns
latency into an observable, enforceable signal without patching Hermes core.
"""

from __future__ import annotations

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)


def register(ctx) -> None:
    ctx.register_tool(
        name="latency_budget_check",
        toolset="latency_budget",
        schema=schemas.LATENCY_BUDGET_CHECK,
        handler=tools.handle_check,
        emoji="⏱️",
    )
    ctx.register_tool(
        name="latency_budget_report",
        toolset="latency_budget",
        schema=schemas.LATENCY_BUDGET_REPORT,
        handler=tools.handle_report,
        emoji="📊",
    )
    ctx.register_hook("pre_tool_call", tools.on_pre_tool_call)
    ctx.register_hook("post_tool_call", tools.on_post_tool_call)
