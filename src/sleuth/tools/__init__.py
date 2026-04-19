"""The 5 tools exposed to the agent inside the sandboxed REPL.

Each tool is a plain Python function callable as `tools.schema()`,
`tools.top_errors(limit=20)`, etc. The REPL runs in-process with an
`ast.PyCF_ALLOW_TOP_LEVEL_AWAIT` compile + restricted globals.
"""
from sleuth.tools.around import around
from sleuth.tools.schema import schema
from sleuth.tools.search import search
from sleuth.tools.top_errors import top_errors
from sleuth.tools.trace import trace

__all__ = ["schema", "top_errors", "search", "around", "trace"]
