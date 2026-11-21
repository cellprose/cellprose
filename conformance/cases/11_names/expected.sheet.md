---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Beta

## A1:A2

#|A
-|-
1|0.05
2|100

# Sheet: Alpha

```cells
A1: 0.07
```

# Sheet: Q1 Data

## A1:A2

#|A
-|-
1|1
2|2

# Names

```names
Alpha = Beta!$A$1
Doubled = Beta!$A$2*2
Tax = 0.07
Zeta = 'Q1 Data'!$A$1:$A$2
Alpha!Rate = Alpha!$A$1
Beta!Cap = Beta!$A$2
Beta!Rate = Beta!$A$1
```
