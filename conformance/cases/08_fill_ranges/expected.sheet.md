---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Fills

## A1:G6

#|A|B|C|D|E|F|G
-|-|-|-|-|-|-|-
1||1|2|3|4
2|10|1|1|1|1|1|1
3|20|1|999|1|1|1|1
4|30|1|1|1|1|1|1
5|40|1|1|1|1|1|1
6||1|1|1|1|1

```formulas
B2:E2 = $A2*B$1
F2:F5 = SUM(B2:E2)
G2:G5 = 'Other Sheet'!$A$1+F2
B3:B5 = $A3*B$1
D3:E5 = $A3*D$1
C4:C5 = $A4*C$1
B6:F6 = SUM(B2:B5)
```

```formats
F2:F6 = 0.0
B6:E6 = 0.0
```

# Sheet: Other Sheet

```cells
A1: 5
```
