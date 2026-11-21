---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Assumptions

## A1:B3

#|A|B
-|-|-
1|Driver|Value
2|Growth|0.12
3|Price|45

```formats
B2 = 0%
```

# Sheet: P&L

```meta
freeze: B2
```

## A1:F4

#|A|B|C|D|E|F
-|-|-|-|-|-|-
1||Q1|Q2|Q3|Q4|Total
2|Units|1200|1344|1505.28|1685.91|5735.19
3|Price|45|45|45|45
4|Revenue|54000|60480|67737.6|75866.1|258084

```formulas
C2:E2 = B2*(1+Growth)
F2 = SUM(B2:E2)
B3:E3 = Assumptions!$B$3
B4:E4 = B2*B3
F4 = SUM(B4:E4)
```

```formats
B4:F4 = $#,##0
```

# Names

```names
Growth = Assumptions!$B$2
```
