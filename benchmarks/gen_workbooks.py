"""Generate benchmark workbooks and question specs.

Each workbook is built with openpyxl (formulas only, no cached values), then
recalculated by LibreOffice in recalc.py. Questions here only name the target
cell and task type; ground truth is computed from the recalculated files in
ground_truth.py, never typed by hand.
"""
import json
import random
import datetime as dt
from pathlib import Path

import openpyxl
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import get_column_letter as L

OUT = Path(__file__).parent / "workbooks_src"
QOUT = Path(__file__).parent / "questions"
OUT.mkdir(exist_ok=True)
QOUT.mkdir(exist_ok=True)

FIRST = ["Aarav", "Maya", "Liam", "Priya", "Noah", "Zara", "Ethan", "Ananya", "Lucas", "Sofia",
         "Kabir", "Emma", "Rohan", "Olivia", "Arjun", "Isla", "Vikram", "Chloe", "Dev", "Ava",
         "Ishaan", "Mia", "Leo", "Aditi", "Omar", "Nina", "Ravi", "Grace", "Samir", "Elena"]
LAST = ["Shah", "Patel", "Kim", "Garcia", "Iyer", "Brown", "Rao", "Nguyen", "Singh", "Lopez",
        "Mehta", "Chen", "Das", "Fischer", "Khan", "Silva", "Joshi", "Novak", "Bose", "Ward"]


def name(rng):
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def add_name(wb, nm, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref)


def save(wb, key, questions):
    wb.save(OUT / f"{key}.xlsx")
    for i, q in enumerate(questions, 1):
        q["id"] = f"q{i}"
    (QOUT / f"{key}.json").write_text(json.dumps(questions, indent=1))


def q_lookup(text, cell):
    return {"type": "lookup", "q": text, "cell": cell}


def q_address(text, cell):
    return {"type": "address", "q": text + " Give its cell address.", "cell": cell}


def q_trace(text, cell):
    return {"type": "trace", "q": text + " List the cells its formula reads directly (not indirectly).", "cell": cell}


def q_impact(text, cell, factor=1.1):
    return {"type": "impact", "q": text + " List every other cell whose value would change.", "cell": cell, "factor": factor}


# ---------------------------------------------------------------- 1 sales log
def sales_log():
    rng = random.Random(1)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Sales"
    hdr = ["Order ID", "Date", "Region", "Rep", "Product", "Units", "Unit Price", "Revenue"]
    ws.append(hdr)
    products = {"Widget": 12.5, "Gadget": 39.0, "Gizmo": 74.0, "Doohickey": 8.25, "Sprocket": 21.0}
    reps = [name(rng) for _ in range(8)]
    n = 150
    for i in range(n):
        r = i + 2
        p = rng.choice(list(products))
        ws.append([f"SO-{1001+i}", dt.date(2026, 1, 1) + dt.timedelta(days=rng.randint(0, 270)),
                   rng.choice(["North", "South", "East", "West"]), rng.choice(reps), p,
                   rng.randint(1, 60), products[p], f"=F{r}*G{r}"])
        ws[f"B{r}"].number_format = "yyyy-mm-dd"
        ws[f"G{r}"].number_format = "$#,##0.00"
        ws[f"H{r}"].number_format = "$#,##0.00"
    t = n + 3
    ws[f"A{t}"] = "Total"; ws[f"F{t}"] = f"=SUM(F2:F{n+1})"; ws[f"H{t}"] = f"=SUM(H2:H{n+1})"
    ws[f"H{t}"].number_format = "$#,##0.00"
    row = lambda oid: oid - 1001 + 2
    qs = [
        q_lookup("What is the revenue of order SO-1042?", f"Sales!H{row(1042)}"),
        q_lookup("How many units were sold in order SO-1100?", f"Sales!F{row(1100)}"),
        q_lookup("What is the total revenue across all orders?", f"Sales!H{t}"),
        q_address("Which cell holds the revenue of order SO-1077?", f"Sales!H{row(1077)}"),
        q_address("Which cell holds the total units?", f"Sales!F{t}"),
        q_trace("Consider the revenue of order SO-1042.", f"Sales!H{row(1042)}"),
        q_impact("Suppose the units of order SO-1042 increased by 10%.", f"Sales!F{row(1042)}"),
    ]
    save(wb, "01_sales_log", qs)


# ---------------------------------------------------------------- 2 employees
def employees():
    rng = random.Random(2)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Employees"
    ws.append(["Employee ID", "Name", "Department", "City", "Age", "Salary", "Start Date"])
    for i in range(120):
        r = i + 2
        ws.append([f"E{1000+i}", name(rng), rng.choice(["Engineering", "Sales", "Finance", "Support", "Marketing", "HR"]),
                   rng.choice(["Pune", "London", "Austin", "Berlin", "Singapore"]), rng.randint(22, 61),
                   rng.randrange(42000, 190000, 500), dt.date(2014, 1, 1) + dt.timedelta(days=rng.randint(0, 4300))])
        ws[f"F{r}"].number_format = "#,##0"
        ws[f"G{r}"].number_format = "yyyy-mm-dd"
    r = lambda e: e - 1000 + 2
    qs = [
        q_lookup("What is the salary of employee E1042?", f"Employees!F{r(1042)}"),
        q_lookup("How old is employee E1007?", f"Employees!E{r(1007)}"),
        q_lookup("Which department is employee E1088 in?", f"Employees!C{r(1088)}"),
        q_lookup("In which city does employee E1115 work?", f"Employees!D{r(1115)}"),
        q_address("Which cell holds the salary of employee E1063?", f"Employees!F{r(1063)}"),
        q_address("Which cell holds the start date of employee E1019?", f"Employees!G{r(1019)}"),
    ]
    save(wb, "02_employees", qs)


# ---------------------------------------------------------------- 3 quarterly P&L
def pnl():
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "P&L"
    ws.append(["", "Q1", "Q2", "Q3", "Q4", "Total"])
    labels = ["Units", "Price", "Revenue", "COGS", "Gross profit", "Opex", "EBITDA", "EBITDA margin"]
    for i, lab in enumerate(labels):
        ws.cell(row=i + 2, column=1, value=lab)
    ws["B2"] = 1200
    for c in "CDE":
        p = chr(ord(c) - 1)
        ws[f"{c}2"] = f"={p}2*(1+Growth)"
    for c in "BCDE":
        ws[f"{c}3"] = "=Price"
        ws[f"{c}4"] = f"={c}2*{c}3"
        ws[f"{c}5"] = f"={c}4*COGS_Pct"
        ws[f"{c}6"] = f"={c}4-{c}5"
        ws[f"{c}7"] = "=Opex"
        ws[f"{c}8"] = f"={c}6-{c}7"
        ws[f"{c}9"] = f"={c}8/{c}4"
        for rr in (4, 5, 6, 7, 8):
            ws[f"{c}{rr}"].number_format = "$#,##0"
        ws[f"{c}9"].number_format = "0.0%"
    for rr in (2, 4, 5, 6, 7, 8):
        ws[f"F{rr}"] = f"=SUM(B{rr}:E{rr})"
    ws["F9"] = "=F8/F4"; ws["F9"].number_format = "0.0%"
    ws["A11"] = "Assumptions"
    for i, (lab, v) in enumerate([("Growth", 0.08), ("Price", 45), ("COGS %", 0.42), ("Opex per quarter", 18000)]):
        ws.cell(row=12 + i, column=1, value=lab); ws.cell(row=12 + i, column=2, value=v)
    ws["B12"].number_format = "0%"; ws["B14"].number_format = "0%"
    add_name(wb, "Growth", "'P&L'!$B$12"); add_name(wb, "Price", "'P&L'!$B$13")
    add_name(wb, "COGS_Pct", "'P&L'!$B$14"); add_name(wb, "Opex", "'P&L'!$B$15")
    qs = [
        q_lookup("What is EBITDA in Q3?", "P&L!D8"),
        q_lookup("What is total revenue for the year?", "P&L!F4"),
        q_address("Which cell holds Q2 gross profit?", "P&L!C6"),
        q_address("Which cell holds the growth assumption?", "P&L!B12"),
        q_trace("Consider Q3 EBITDA.", "P&L!D8"),
        q_trace("Consider Q2 units.", "P&L!C2"),
        q_impact("Suppose the growth assumption increased by 10%.", "P&L!B12"),
        q_impact("Suppose Opex per quarter increased by 10%.", "P&L!B15"),
    ]
    save(wb, "03_pnl_quarterly", qs)


# ---------------------------------------------------------------- 4 SaaS model
def saas():
    wb = openpyxl.Workbook(); a = wb.active; a.title = "Assumptions"
    rows = [("Driver", "Value"), ("Starting customers", 200), ("New customers per month", 35),
            ("Monthly churn", 0.03), ("ARPU", 89), ("CAC", 420), ("Gross margin", 0.78)]
    for r in rows:
        a.append(list(r))
    a["B4"].number_format = "0.0%"; a["B7"].number_format = "0%"
    add_name(wb, "Churn", "Assumptions!$B$4"); add_name(wb, "ARPU", "Assumptions!$B$5")
    m = wb.create_sheet("Monthly")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m.append(["Metric"] + months + ["FY"])
    labs = ["Starting customers", "New customers", "Churned", "Ending customers", "MRR", "Gross profit", "S&M spend", "Contribution"]
    for i, lab in enumerate(labs):
        m.cell(row=i + 2, column=1, value=lab)
    for j in range(12):
        c = L(j + 2); p = L(j + 1)
        m[f"{c}2"] = "=Assumptions!B2" if j == 0 else f"={p}5"
        m[f"{c}3"] = "=Assumptions!$B$3"
        m[f"{c}4"] = f"=ROUND({c}2*Churn,0)"
        m[f"{c}5"] = f"={c}2+{c}3-{c}4"
        m[f"{c}6"] = f"={c}5*ARPU"
        m[f"{c}7"] = f"={c}6*Assumptions!$B$7"
        m[f"{c}8"] = f"={c}3*Assumptions!$B$6"
        m[f"{c}9"] = f"={c}7-{c}8"
        for rr in (6, 7, 8, 9):
            m[f"{c}{rr}"].number_format = "$#,##0"
    m["N3"] = "=SUM(B3:M3)"; m["N6"] = "=SUM(B6:M6)"; m["N9"] = "=SUM(B9:M9)"
    qs = [
        q_lookup("How many ending customers are there in June?", "Monthly!G5"),
        q_lookup("What is full-year MRR summed across months (FY)?", "Monthly!N6"),
        q_address("Which cell holds September contribution?", "Monthly!J9"),
        q_trace("Consider starting customers in February.", "Monthly!C2"),
        q_trace("Consider January gross profit.", "Monthly!B7"),
        q_impact("Suppose monthly churn increased by 10%.", "Assumptions!B4"),
        q_impact("Suppose CAC increased by 10%.", "Assumptions!B6"),
    ]
    save(wb, "04_saas_model", qs)


# ---------------------------------------------------------------- 5 multi-sheet model
def multisheet():
    wb = openpyxl.Workbook(); i = wb.active; i.title = "Inputs"
    inputs = [("Input", "Value"), ("Price A", 120), ("Price B", 80), ("Price C", 45), ("Volume A", 1000),
              ("Volume B", 2500), ("Volume C", 6000), ("Volume growth", 0.1), ("Price growth", 0.03),
              ("Fixed costs", 150000), ("Variable cost %", 0.35), ("Tax rate", 0.25)]
    for r in inputs:
        i.append(list(r))
    rv = wb.create_sheet("Revenue"); rv.append(["Product", "Y1", "Y2", "Y3"])
    for k, p in enumerate("ABC"):
        r = k + 2
        rv[f"A{r}"] = f"Product {p}"
        rv[f"B{r}"] = f"=Inputs!B{2+k}*Inputs!B{5+k}"
        rv[f"C{r}"] = f"=B{r}*(1+Inputs!$B$8)*(1+Inputs!$B$9)"
        rv[f"D{r}"] = f"=C{r}*(1+Inputs!$B$8)*(1+Inputs!$B$9)"
    rv["A5"] = "Total"
    for c in "BCD":
        rv[f"{c}5"] = f"=SUM({c}2:{c}4)"
    co = wb.create_sheet("Costs"); co.append(["Cost", "Y1", "Y2", "Y3"])
    co["A2"] = "Variable"; co["A3"] = "Fixed"; co["A4"] = "Total"
    for c in "BCD":
        co[f"{c}2"] = f"=Revenue!{c}5*Inputs!$B$11"
        co[f"{c}3"] = "=Inputs!$B$10"
        co[f"{c}4"] = f"={c}2+{c}3"
    s = wb.create_sheet("Summary"); s.append(["Line", "Y1", "Y2", "Y3"])
    for k, lab in enumerate(["Revenue", "Costs", "EBIT", "Tax", "Net income"]):
        s.cell(row=k + 2, column=1, value=lab)
    for c in "BCD":
        s[f"{c}2"] = f"=Revenue!{c}5"; s[f"{c}3"] = f"=Costs!{c}4"; s[f"{c}4"] = f"={c}2-{c}3"
        s[f"{c}5"] = f"=MAX(0,{c}4*Inputs!$B$12)"; s[f"{c}6"] = f"={c}4-{c}5"
    qs = [
        q_lookup("What is net income in Y3?", "Summary!D6"),
        q_lookup("What is Y2 revenue for Product B?", "Revenue!C3"),
        q_address("Which cell holds tax in Y2?", "Summary!C5"),
        q_trace("Consider EBIT in Y1.", "Summary!B4"),
        q_trace("Consider variable costs in Y2.", "Costs!C2"),
        q_impact("Suppose fixed costs increased by 10%.", "Inputs!B10"),
        q_impact("Suppose Volume B increased by 10%.", "Inputs!B6"),
    ]
    save(wb, "05_multisheet_model", qs)


# ---------------------------------------------------------------- 6 budget vs actual
def bva():
    rng = random.Random(6)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "BvA"
    ws.append(["Department", "Jan Budget", "Jan Actual", "Feb Budget", "Feb Actual", "Mar Budget", "Mar Actual",
               "Q1 Budget", "Q1 Actual", "Variance", "Variance %"])
    depts = ["Engineering", "Sales", "Marketing", "Support", "Finance", "HR", "Legal", "Operations"]
    for k, d in enumerate(depts):
        r = k + 2
        vals = []
        for _ in range(3):
            b = rng.randrange(20000, 250000, 1000)
            vals += [b, round(b * rng.uniform(0.85, 1.15))]
        ws.append([d] + vals + [f"=B{r}+D{r}+F{r}", f"=C{r}+E{r}+G{r}", f"=I{r}-H{r}", f"=IF(H{r}=0,0,J{r}/H{r})"])
        ws[f"K{r}"].number_format = "0.0%"
    ws["A11"] = "Total"
    for c in "BCDEFGHIJ":
        ws[f"{c}11"] = f"=SUM({c}2:{c}9)"
    ws["K11"] = "=J11/H11"; ws["K11"].number_format = "0.0%"
    qs = [
        q_lookup("What is Marketing's Q1 variance?", "BvA!J4"),
        q_lookup("What is total Q1 actual spend?", "BvA!I11"),
        q_lookup("What is Support's February actual?", "BvA!E5"),
        q_address("Which cell holds Legal's March budget?", "BvA!F8"),
        q_trace("Consider Marketing's Q1 variance.", "BvA!J4"),
        q_trace("Consider the total Q1 budget.", "BvA!H11"),
        q_impact("Suppose Sales' January actual increased by 10%.", "BvA!C3"),
    ]
    save(wb, "06_budget_vs_actual", qs)


# ---------------------------------------------------------------- 7 messy report
def messy():
    rng = random.Random(7)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Report"
    ws["A1"] = "Warehouse Report - Q3 2026"
    ws["A2"] = "Prepared by the ops team. Figures in units unless noted."
    ws["A4"] = "Inventory"
    for j, h in enumerate(["SKU", "Item", "On hand", "Reorder point", "Below reorder?"]):
        ws.cell(row=5, column=j + 1, value=h)
    items = ["Bolt M6", "Bolt M8", "Nut M6", "Washer", "Bracket", "Hinge", "Spring", "Gasket", "Clamp",
             "Rivet", "Pin", "Bearing", "Seal", "Spacer", "Shim"]
    for k, it in enumerate(items):
        r = 6 + k
        ws[f"A{r}"] = f"SKU-{1001+k}"; ws[f"B{r}"] = it
        ws[f"C{r}"] = rng.randint(0, 900); ws[f"D{r}"] = rng.randrange(50, 400, 25)
        ws[f"E{r}"] = f'=IF(C{r}<D{r},"YES","NO")'
    ws["A24"] = "Pending orders"
    for j, h in enumerate(["PO", "SKU", "Qty", "Unit cost", "Line total"]):
        ws.cell(row=25, column=j + 1, value=h)
    for k in range(8):
        r = 26 + k
        ws[f"A{r}"] = f"PO-{5001+k}"; ws[f"B{r}"] = f"SKU-{1001+rng.randint(0,14)}"
        ws[f"C{r}"] = rng.randrange(100, 1000, 50); ws[f"D{r}"] = round(rng.uniform(0.05, 4.5), 2)
        ws[f"E{r}"] = f"=C{r}*D{r}"
        ws[f"D{r}"].number_format = "$0.00"; ws[f"E{r}"].number_format = "$#,##0.00"
    ws["A34"] = "Total"; ws["E34"] = "=SUM(E26:E33)"; ws["E34"].number_format = "$#,##0.00"
    ws["A36"] = "Note: costs exclude freight."
    ws["H5"] = "Summary"
    ws["H6"] = "Items below reorder"; ws["I6"] = '=COUNTIF(E6:E20,"YES")'
    ws["H7"] = "Total on hand"; ws["I7"] = "=SUM(C6:C20)"
    ws["H8"] = "Open PO value"; ws["I8"] = "=E34"; ws["I8"].number_format = "$#,##0.00"
    qs = [
        q_lookup("How many units of SKU-1007 are on hand?", "Report!C12"),
        q_lookup("What is the line total of PO-5003?", "Report!E28"),
        q_lookup("What is the open PO value?", "Report!I8"),
        q_address("Which cell holds the reorder point of SKU-1010?", "Report!D15"),
        q_trace("Consider the open PO value in the summary box.", "Report!I8"),
        q_trace("Consider the line total of PO-5003.", "Report!E28"),
        q_impact("Suppose the on-hand count of SKU-1004 increased by 10%.", "Report!C9"),
    ]
    save(wb, "07_messy_report", qs)


# ---------------------------------------------------------------- 8 loan schedule
def loan():
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Loan"
    ws["A1"] = "Loan amount"; ws["B1"] = 250000
    ws["A2"] = "Annual rate"; ws["B2"] = 0.065; ws["B2"].number_format = "0.00%"
    ws["A3"] = "Term (years)"; ws["B3"] = 2
    ws["A4"] = "Monthly payment"; ws["B4"] = "=PMT(B2/12,B3*12,-B1)"; ws["B4"].number_format = "$#,##0.00"
    for j, h in enumerate(["Month", "Opening balance", "Payment", "Interest", "Principal", "Closing balance"]):
        ws.cell(row=6, column=j + 1, value=h)
    for k in range(24):
        r = 7 + k
        ws[f"A{r}"] = 1 if k == 0 else f"=A{r-1}+1"
        ws[f"B{r}"] = "=$B$1" if k == 0 else f"=F{r-1}"
        ws[f"C{r}"] = "=$B$4"; ws[f"D{r}"] = f"=B{r}*$B$2/12"
        ws[f"E{r}"] = f"=C{r}-D{r}"; ws[f"F{r}"] = f"=B{r}-E{r}"
        for c in "BCDEF":
            ws[f"{c}{r}"].number_format = "$#,##0.00"
    ws["A32"] = "Total interest"; ws["D32"] = "=SUM(D7:D30)"; ws["D32"].number_format = "$#,##0.00"
    qs = [
        q_lookup("What is the closing balance after month 12?", "Loan!F18"),
        q_lookup("What is the total interest paid?", "Loan!D32"),
        q_lookup("What is the monthly payment?", "Loan!B4"),
        q_address("Which cell holds the interest paid in month 6?", "Loan!D12"),
        q_trace("Consider the opening balance in month 2.", "Loan!B8"),
        q_trace("Consider the interest in month 6.", "Loan!D12"),
        q_impact("Suppose the loan amount increased by 10%.", "Loan!B1"),
    ]
    save(wb, "08_loan_schedule", qs)


# ---------------------------------------------------------------- 9 products / orders / summary
def orders():
    rng = random.Random(9)
    wb = openpyxl.Workbook(); p = wb.active; p.title = "Products"
    p.append(["SKU", "Name", "Category", "Unit price", "Unit cost"])
    cats = ["Hardware", "Software", "Services", "Accessories"]
    nouns = ["Router", "Switch", "Cable", "License", "Support plan", "Adapter", "Camera", "Dock", "Hub", "Mount"]
    for k in range(40):
        price = round(rng.uniform(5, 900), 2)
        p.append([f"P{101+k}", f"{rng.choice(nouns)} {k+1}", cats[k % 4], price, round(price * rng.uniform(0.35, 0.8), 2)])
    o = wb.create_sheet("Orders")
    o.append(["Order", "SKU", "Qty", "Unit price", "Revenue", "Cost", "Margin", "Category"])
    rngP = "Products!$A$2:$E$41"
    for k in range(60):
        r = k + 2
        o.append([f"ORD-{2001+k}", f"P{101+rng.randint(0,39)}", rng.randint(1, 25),
                  f"=VLOOKUP(B{r},{rngP},4,FALSE)", f"=C{r}*D{r}", f"=C{r}*VLOOKUP(B{r},{rngP},5,FALSE)",
                  f"=E{r}-F{r}", f"=VLOOKUP(B{r},{rngP},3,FALSE)"])
    s = wb.create_sheet("Summary"); s.append(["Category", "Revenue", "Margin"])
    for k, c in enumerate(cats):
        r = k + 2
        s.append([c, f"=SUMIF(Orders!$H$2:$H$61,A{r},Orders!$E$2:$E$61)", f"=SUMIF(Orders!$H$2:$H$61,A{r},Orders!$G$2:$G$61)"])
    s.append(["Total", "=SUM(B2:B5)", "=SUM(C2:C5)"])
    qs = [
        q_lookup("What is the revenue of order ORD-2015?", "Orders!E16"),
        q_lookup("What is total margin across all categories?", "Summary!C6"),
        q_lookup("What is the category of order ORD-2030?", "Orders!H31"),
        q_address("Which cell holds the margin of order ORD-2044?", "Orders!G45"),
        q_trace("Consider the revenue of order ORD-2009.", "Orders!E10"),
        q_impact("Suppose the quantity of order ORD-2009 increased by 10%.", "Orders!C10"),
    ]
    save(wb, "09_orders_lookup", qs)


# ---------------------------------------------------------------- 10 gradebook
def grades():
    rng = random.Random(10)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Grades"
    ws.append(["Student", "HW1", "HW2", "HW3", "Midterm", "Final", "Weighted", "Letter"])
    ws.append(["Weight", 0.1, 0.1, 0.1, 0.3, 0.4])
    for c in "BCDEF":
        ws[f"{c}2"].number_format = "0%"
    used = set()
    for k in range(30):
        r = k + 3
        nm = name(rng)
        while nm in used:
            nm = name(rng)
        used.add(nm)
        ws.append([nm] + [rng.randint(45, 100) for _ in range(5)] +
                  [f"=SUMPRODUCT($B$2:$F$2,B{r}:F{r})",
                   f'=IF(G{r}>=90,"A",IF(G{r}>=80,"B",IF(G{r}>=70,"C",IF(G{r}>=60,"D","F"))))'])
    ws["A34"] = "Class average"
    for c in "BCDEFG":
        ws[f"{c}34"] = f"=AVERAGE({c}3:{c}32)"
    s10 = ws["A10"].value; s20 = ws["A20"].value; s5 = ws["A5"].value; s15 = ws["A15"].value
    qs = [
        q_lookup(f"What is {s10}'s weighted score?", "Grades!G10"),
        q_lookup("What is the class average on the final?", "Grades!F34"),
        q_lookup(f"What letter grade did {s5} get?", "Grades!H5"),
        q_address(f"Which cell holds {s20}'s midterm score?", "Grades!E20"),
        q_trace(f"Consider {s15}'s weighted score.", "Grades!G15"),
        q_impact("Suppose the weight of the final increased by 10%.", "Grades!F2"),
    ]
    save(wb, "10_gradebook", qs)


if __name__ == "__main__":
    for f in (sales_log, employees, pnl, saas, multisheet, bva, messy, loan, orders, grades):
        f()
    print("generated", len(list(OUT.glob("*.xlsx"))), "workbooks")
