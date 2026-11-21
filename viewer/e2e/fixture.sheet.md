---
sheetmark: 0.2
---

# Sheet: P&L

## A1:F4

|#|A|B|C|D|E|F|
|-|-|-|-|-|-|-|
|1||Q1|Q2|Q3|Q4|Total|
|2|Units|1200|1296|1399.68|1511.65|5407.33|
|3|Price|45|45|45|45||
|4|Revenue|54000|58320|62985.6|68024.4|243330|

```formulas
C2:E2 = B2*(1+Growth)
F2 = SUM(B2:E2)
B3:E3 = Price
B4:E4 = B2*B3
F4 = SUM(B4:E4)
```

```formats
B4:F4 = $#,##0
```

# Sheet: Assumptions

## A1:B3

|#|A|B|
|-|-|-|
|1|Name|Value|
|2|Growth|0.08|
|3|Price|45|

# Names

```names
Growth = Assumptions!$B$2
Price = Assumptions!$B$3
```
