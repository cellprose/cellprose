"""Per-call averages measured in the API pilot (E32, `results/e32_repilot`: 15 Enron workbooks, the same four models,
prompts and runners), used by the cost estimates in place of older CLI averages. A guide, not a promise: the pilot
had no Damodaran workbooks and ran agent turns uncached."""
import json
from functools import lru_cache
from pathlib import Path

from .ids import canon

PILOT = Path(__file__).resolve().parent.parent / "results" / "e32_repilot" / "raw"
FALLBACK = {"agent_xlsx_viewer": "agent_xlsx"}       # no pilot runs of the viewer arm: the plain-shell arm's average


@lru_cache(maxsize=None)
def _calls(alias: str) -> dict:
    out = {}
    for f in sorted((PILOT / alias).glob("*.json")) if (PILOT / alias).exists() else []:
        d = json.loads(f.read_text())
        if d.get("failed"):
            continue
        out.setdefault(canon(d["encoding"]), []).append((d["usage"]["output_tokens"], d["cost"]))
    return out


def measured(alias: str, arm: str) -> tuple[float, float, int] | None:
    """(mean output tokens, mean uncached list-price cost, calls) for this model and arm in the pilot, or None."""
    calls = _calls(alias).get(arm) or _calls(alias).get(FALLBACK.get(arm, ""))
    if not calls:
        return None
    return sum(o for o, _ in calls) / len(calls), sum(c for _, c in calls) / len(calls), len(calls)
