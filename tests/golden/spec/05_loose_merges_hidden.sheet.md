---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: "Q1 #2"

## A3:C6

#|A|B|C
-|-|-|-
3|Item|Cost|Share
4|Rent|900|0.225
5|Wages|3100|0.775
6|Total|4000

```formulas
C4 = B4/B6
C5 = B5/B6
B6 = SUM(B4:B5)
```

```formats
C4:C5 = 0.0%
```

```cells
A1: Quarterly report
F2: Prepared by finance
F4: 2026-12-25
F6 = B6*2  # 8000
```

```formats
F4 = yyyy-mm-dd
F6 = #,##0
```

```merges
A1:C1
```

# Sheet: Notes

```meta
hidden: true
```

## A1:B1

#|A|B
-|-|-
1|secret|1

# Names

```names
Notes!Local = Notes!$B$1
```
