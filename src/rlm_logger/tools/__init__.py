"""The 5 tools exposed to the agent inside the sandboxed REPL.

Each tool is a plain Python function callable as `tools.schema()`,
`tools.top_errors(limit=20)`, etc. The REPL runs in-process with an
`ast.PyCF_ALLOW_TOP_LEVEL_AWAIT` compile + restricted globals.
"""
from rlm_logger.tools.around import around
from rlm_logger.tools.schema import schema
from rlm_logger.tools.search import search
from rlm_logger.tools.top_errors import top_errors
from rlm_logger.tools.trace import trace

__all__ = ["schema", "top_errors", "search", "around", "trace"]
