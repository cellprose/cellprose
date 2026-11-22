"""E31 addendum: tiny VLOOKUP check of the row-number note (see experiments/E31-address-fault-ab.md). Haiku 5.5, 5 repeats."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from exp_address_ab import transform
from runner import models
from runner.prompts import SYSTEM
from runner.providers import get_provider

TEXT = Path("/mnt/project-files/sheetmark-report/vlookup-example.sheet.md").read_text()
Q = [("q1", "Which column letter of the Rates sheet does the formula in Orders!D2 return? Answer with the column letter only.", "B"),
     ("q2", "What value would =VLOOKUP(B3,Rates!$A$2:$C$4,3,FALSE()) return?", "Bo"),
     ("q3", "Which cell holds the Manager for the West region? Give its cell address.", "Rates!C4"),
     ("q4", "Which cell holds the Rate for the South region? Give its cell address.", "Rates!B3"),
     ("q5", "Which cell does the formula in Orders!D4 read its result from? Give its cell address.", "Rates!B4"),
     ("q6", "What value would =VLOOKUP(B4,Rates!$A$2:$C$4,2,FALSE()) return?", "13")]
cfg = models.get("haiku55"); prov = get_provider(cfg); res = {}; cost = 0
for v in ["v03", "note", "note_each", "note_ex"]:
    t = transform(TEXT, v); ok = 0; n = 0
    for r in range(5):
        user = (f'<workbook format="Sheetmark">\n{t}\n</workbook>\n\nAnswer each question. Cell addresses use A1 notation qualified with the sheet name, e.g. Sheet1!B5. '
                "For value questions, return a number without units or thousands separators, or a short string.\n\nQuestions:\n"
                + "\n".join(f"{i} : {q}" for i, q, _ in Q) + '\n\nReturn JSON like {"q1": ..., "q2": ...} with every question id.')
        out = prov.complete(cfg, SYSTEM, user); u = out.usage
        cost += u.total_input * cfg.price_in / 1e6 + u.output_tokens * cfg.price_out / 1e6
        a = json.loads(re.search(r"\{.*\}", out.text, re.S).group(0))
        for i, _, tr in Q:
            n += 1; ok += re.sub(r"[\s']", "", str(a.get(i, ""))).upper() == tr.upper()
            if re.sub(r"[\s']", "", str(a.get(i, ""))).upper() != tr.upper(): res.setdefault(v, []).append((i, a.get(i)))
    print(v, f"{ok}/{n}", res.get(v, [])[:8])
print(f"cost ${cost:.3f}")
