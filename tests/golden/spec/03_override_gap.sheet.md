---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Forecast

## A1:H2

#|A|B|C|D|E|F|G|H
-|-|-|-|-|-|-|-|-
1|Line|Jan|Feb|Mar|Apr|May|Jun|Jul
2|Bookings|100000|104000|108160|112486|117000|121680|126547

```formulas
C2:E2 = B2*(1+$B$4)
G2:H2 = F2*(1+$B$4)
```

## A4:B4

#|A|B
-|-|-
4|Monthly growth|0.04

```formats
B4 = 0%
```
