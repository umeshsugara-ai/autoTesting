"""Move the block-reading tests into their own module, by AST span, not by line guess."""
from __future__ import annotations

import ast
from pathlib import Path

SRC = Path("d:/autoTesting/tests/test_ledger_checks.py")
DST = Path("d:/autoTesting/tests/test_marker_blocks.py")

MOVE = [
    "test_a_decorated_marker_line_is_still_a_marker_line",
    "test_prose_that_quotes_the_marker_is_not_a_claim",
    "test_a_line_opening_with_the_marker_in_backticks_is_not_a_claim",
    "test_an_id_on_a_continuation_line_is_still_named",
    "test_a_fix_claim_on_a_continuation_line_is_read",
    "test_a_verdict_block_ends_at_the_next_FIELD_not_at_a_blank_line",
    "test_the_block_ends_at_a_blank_line_or_a_heading",
    "test_a_field_label_carrying_a_parenthetical_still_ends_the_block",
    "test_an_issue_id_with_a_parenthetical_is_not_a_field_label",
    "test_a_code_fence_ends_the_block",
]

HEADER = '''"""How a claim BLOCK is read: which lines carry it, and where it ends.

Split from `test_ledger_checks.py` under AT-513, along the seam those tests already
had. That file asks what the check CONCLUDES about a ledger row — lost, stale, or
fine. This one asks what the check READS before it concludes anything: whether a line
carries a claim at all (AT-504), and where the block that carries it stops (AT-509,
AT-511).

Four consecutive units grew the original to 295 of C2's 300 lines, all four in this
half — the same evidence for both halves of the split.

`_qa` and `ROW` are imported rather than copied: one concept, one place.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from autotester.ledger import checks

from tests.test_ledger_checks import ROW, _qa

__all__ = ["ROW", "_qa"]

'''


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)

    spans: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
            spans[node.name] = (start, node.end_lineno)

    missing = [n for n in MOVE if n not in spans]
    assert not missing, missing

    taken = sorted(spans[n] for n in MOVE)
    moved = "".join("".join(lines[a:b]).rstrip("\n") + "\n\n\n" for a, b in taken)

    keep, drop = [], {i for a, b in taken for i in range(a, b)}
    for i, line in enumerate(lines):
        if i not in drop:
            keep.append(line)

    DST.write_text(HEADER + "\n" + moved.rstrip("\n") + "\n", encoding="utf-8")
    SRC.write_text("".join(keep).rstrip("\n") + "\n", encoding="utf-8")
    print(f"moved {len(MOVE)} tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
