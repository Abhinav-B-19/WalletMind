"""WalletMind Google ADK Function Tools package."""

from google.adk.tools import FunctionTool

from backend.app.tools.assistant_tool import ASSISTANT_TOOL
from backend.app.tools.budget_tool import BUDGET_TOOL
from backend.app.tools.health_tool import HEALTH_TOOL
from backend.app.tools.insights_tool import INSIGHTS_TOOL
from backend.app.tools.processing_tool import PROCESSING_TOOL
from backend.app.tools.report_tool import REPORT_TOOL

WALLETMIND_FUNCTION_TOOLS: tuple[FunctionTool, ...] = (
    PROCESSING_TOOL,
    HEALTH_TOOL,
    INSIGHTS_TOOL,
    BUDGET_TOOL,
    REPORT_TOOL,
    ASSISTANT_TOOL,
)


def get_walletmind_function_tools() -> list[FunctionTool]:
    """Return WalletMind ADK Function Tools for agent/workflow registration."""

    return list(WALLETMIND_FUNCTION_TOOLS)


__all__ = [
    "ASSISTANT_TOOL",
    "BUDGET_TOOL",
    "HEALTH_TOOL",
    "INSIGHTS_TOOL",
    "PROCESSING_TOOL",
    "REPORT_TOOL",
    "WALLETMIND_FUNCTION_TOOLS",
    "get_walletmind_function_tools",
]
