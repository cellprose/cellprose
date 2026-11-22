"""Hard workbooks: logic that cannot be reverse-engineered from labels and values alone.

- hard-coded overrides mixed into formula rows
- look-alike assumptions (several inputs with the same value)
- a scenario switch where inactive scenarios feed nothing
- allocations driven by inputs on another sheet, with some allocations typed in
Adds a 'hardcode' audit task: which cells in a range are typed-in numbers, not formulas.
"""
import openpyxl
from openpyxl.utils import get_column_letter as L

from gen_workbooks import save, add_name, q_lookup, q_address, q_trace, q_impact

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def q_hard(text, rng):
    return {"type": "hardcode", "q": text + " List the cells that hold typed-in numbers rather than formulas.",
            "cell": rng.split(":")[0], "range": rng}


# ---------------------------------------------------------------- 11 forecast with overrides
def overrides():
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Forecast"
    ws.append(["Line"] + MONTHS + ["FY"])
    ws["A2"] = "Bookings"; ws["A3"] = "Revenue"; ws["A4"] = "Headcount"; ws["A5"] = "Payroll"
    ws["A7"] = "Monthly growth"; ws["B7"] = 0.04
    ws["A8"] = "Revenue per booking"; ws["B8"] = 1.0
    ws["A9"] = "Cost per head"; ws["B9"] = 9500
    ws["A10"] = "Hires per month"; ws["B10"] = 2
    ws["B2"] = 100000
    vals = {}
    for j in range(1, 12):
        c, p = L(j + 2), L(j + 1)
        ws[f"{c}2"] = f"={p}2*(1+$B$7)"
    # overrides: plausible typed numbers that break the chain (values close to the formula result)
    over_b = {"F": 117000, "J": 140000}  # May, Sep bookings typed in
    for c, v in over_b.items():
        ws[f"{c}2"] = v
    ws["B4"] = 40
    for j in range(12):
        c, p = L(j + 2), L(j + 1)
        ws[f"{c}3"] = f"={c}2*$B$8"
        if j:
            ws[f"{c}4"] = f"={p}4+$B$10"
        ws[f"{c}5"] = f"={c}4*$B$9"
    ws["H4"] = 52  # Jul headcount typed in (formula would give 52 too: 40+6*2)
    ws["K5"] = 480000  # Oct payroll typed in
    for r in (2, 3, 5):
        ws[f"N{r}"] = f"=SUM(B{r}:M{r})"
    qs = [
        q_lookup("What are FY bookings?", "Forecast!N2"),
        q_hard("Consider the bookings row for Feb through Dec (C2:M2).", "Forecast!C2:M2"),
        q_hard("Consider the headcount and payroll rows for Feb through Dec (C4:M5).", "Forecast!C4:M5"),
        q_trace("Consider Jun bookings.", "Forecast!G2"),
        q_impact("Suppose monthly growth increased by 10%.", "Forecast!B7"),
        q_impact("Suppose hires per month increased by 50%.", "Forecast!B10", 1.5),
    ]
    save(wb, "11_forecast_overrides", qs)


# ---------------------------------------------------------------- 12 look-alike drivers
def lookalike():
    wb = openpyxl.Workbook(); a = wb.active; a.title = "Drivers"
    a.append(["Driver", "Value"])
    for lab, v in [("Price inflation", 0.03), ("Wage inflation", 0.03), ("Rent escalation", 0.03),
                   ("Volume growth", 0.05), ("Marketing growth", 0.05), ("Utilities inflation", 0.03)]:
        a.append([lab, v])
    p = wb.create_sheet("Plan"); p.append(["Line", "Y1", "Y2", "Y3", "Y4"])
    lines = [("Volume", 50000, "Drivers!$B$5"), ("Unit price", 20, "Drivers!$B$2"), ("Wages", 400000, "Drivers!$B$3"),
             ("Rent", 120000, "Drivers!$B$4"), ("Marketing", 90000, "Drivers!$B$6"), ("Utilities", 30000, "Drivers!$B$7")]
    for i, (lab, y1, drv) in enumerate(lines):
        r = i + 2
        p[f"A{r}"] = lab; p[f"B{r}"] = y1
        for c, prev in (("C", "B"), ("D", "C"), ("E", "D")):
            p[f"{c}{r}"] = f"={prev}{r}*(1+{drv})"
    p["A8"] = "Revenue"; p["A9"] = "Total costs"; p["A10"] = "Profit"
    for c in "BCDE":
        p[f"{c}8"] = f"={c}2*{c}3"; p[f"{c}9"] = f"=SUM({c}4:{c}7)"; p[f"{c}10"] = f"={c}8-{c}9"
    qs = [
        q_lookup("What is profit in Y4?", "Plan!E10"),
        q_trace("Consider Y3 rent.", "Plan!D5"),
        q_trace("Consider Y2 wages.", "Plan!C4"),
        q_trace("Consider Y2 marketing.", "Plan!C6"),
        q_impact("Suppose wage inflation increased by 10%.", "Drivers!B3"),
        q_impact("Suppose price inflation increased by 10%.", "Drivers!B2"),
        q_impact("Suppose marketing growth increased by 10%.", "Drivers!B6"),
    ]
    save(wb, "12_lookalike_drivers", qs)


# ---------------------------------------------------------------- 13 scenario switch
def scenario():
    wb = openpyxl.Workbook(); s = wb.active; s.title = "Scenarios"
    s["A1"] = "Active scenario (1=Base, 2=Upside, 3=Downside)"; s["B1"] = 1
    s.append([])
    s.append(["Driver", "Base", "Upside", "Downside", "Active"])
    for i, (lab, b, u, d) in enumerate([("Growth", 0.06, 0.12, 0.01), ("Margin", 0.22, 0.27, 0.15),
                                        ("Capex % revenue", 0.08, 0.1, 0.05)]):
        r = 4 + i
        s[f"A{r}"] = lab; s[f"B{r}"] = b; s[f"C{r}"] = u; s[f"D{r}"] = d
        s[f"E{r}"] = f"=CHOOSE($B$1,B{r},C{r},D{r})"
    add_name(wb, "Growth", "Scenarios!$E$4"); add_name(wb, "Margin", "Scenarios!$E$5")
    add_name(wb, "CapexPct", "Scenarios!$E$6")
    m = wb.create_sheet("Model"); m.append(["Line", "Y1", "Y2", "Y3", "Y4", "Y5"])
    m["A2"] = "Revenue"; m["A3"] = "EBIT"; m["A4"] = "Capex"; m["A5"] = "Free cash flow"
    m["B2"] = 2000000
    for j, c in enumerate("BCDEF"):
        if j:
            m[f"{c}2"] = f"={'BCDEF'[j-1]}2*(1+Growth)"
        m[f"{c}3"] = f"={c}2*Margin"; m[f"{c}4"] = f"={c}2*CapexPct"; m[f"{c}5"] = f"={c}3-{c}4"
    qs = [
        q_lookup("What is free cash flow in Y5?", "Model!F5"),
        q_address("Which cell holds the growth rate the model actually uses?", "Scenarios!E4"),
        q_trace("Consider Y3 revenue.", "Model!D2"),
        q_impact("Suppose upside growth increased by 10%.", "Scenarios!C4"),
        q_impact("Suppose base margin increased by 10%.", "Scenarios!B5"),
        q_impact("Suppose downside capex % increased by 10%.", "Scenarios!D6"),
    ]
    save(wb, "13_scenario_switch", qs)


# ---------------------------------------------------------------- 14 cost allocation
def allocation():
    wb = openpyxl.Workbook(); d = wb.active; d.title = "Drivers"
    d.append(["Department", "Headcount", "Floor area", "Tickets"])
    depts = [("Engineering", 60, 900, 120), ("Sales", 25, 600, 40), ("Support", 30, 400, 900), ("Finance", 10, 200, 60),
             ("Marketing", 15, 300, 80)]
    for row in depts:
        d.append(list(row))
    d["A7"] = "Total"
    for c in "BCD":
        d[f"{c}7"] = f"=SUM({c}2:{c}6)"
    sh = wb.create_sheet("Shared"); sh.append(["Pool", "Annual cost", "Driver"])
    sh.append(["IT", 600000, "Headcount"]); sh.append(["Facilities", 450000, "Floor area"])
    sh.append(["Helpdesk", 300000, "Tickets"])
    al = wb.create_sheet("Allocation"); al.append(["Department", "IT", "Facilities", "Helpdesk", "Total"])
    for i, (dep, *_r) in enumerate(depts):
        r = i + 2
        al[f"A{r}"] = dep
        al[f"B{r}"] = f"=Shared!$B$2*Drivers!B{r}/Drivers!$B$7"
        al[f"C{r}"] = f"=Shared!$B$3*Drivers!C{r}/Drivers!$C$7"
        al[f"D{r}"] = f"=Shared!$B$4*Drivers!D{r}/Drivers!$D$7"
        al[f"E{r}"] = f"=SUM(B{r}:D{r})"
    al["C5"] = 37500  # Finance facilities typed in (formula would give 37500 too)
    al["D3"] = 9000   # Sales helpdesk typed in (formula gives 10000)
    al["A7"] = "Total"
    for c in "BCDE":
        al[f"{c}7"] = f"=SUM({c}2:{c}6)"
    qs = [
        q_lookup("What is Support's total allocated cost?", "Allocation!E4"),
        q_hard("Consider the allocation table body (B2:D6).", "Allocation!B2:D6"),
        q_trace("Consider Marketing's IT allocation.", "Allocation!B6"),
        q_impact("Suppose Finance's floor area increased by 10%.", "Drivers!C5"),
        q_impact("Suppose Sales' ticket count increased by 10%.", "Drivers!D3"),
        q_impact("Suppose the Facilities annual cost increased by 10%.", "Shared!B3"),
    ]
    save(wb, "14_cost_allocation", qs)


if __name__ == "__main__":
    for f in (overrides, lookalike, scenario, allocation):
        f()
    print("hard workbooks generated")
