"""AutoTester — an AI system that does the automated-tester job end to end.

Pipeline: INGEST (video/docs -> FlowSpec) -> EXPAND (best/worst/edge cases) ->
EXECUTE (real visible browser) -> GRADE (independent judge) -> REPORT +
COVERAGE (ask for the videos it still needs).

Start reading at docs/ARCHITECTURE.md, then autotester/schema/.
"""

from autotester.cli import main

__version__ = "0.1.0"
__all__ = ["main"]
