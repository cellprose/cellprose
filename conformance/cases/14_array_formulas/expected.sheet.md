---
cellprose: 0.3
note: '? = formula with no cached value; open and save in Excel or LibreOffice to compute'
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Arrays

## A1:C2

#|A|B|C
-|-|-|-
1|1|2|?
2|2|4|3

```cells
H10: 3
```

```arrays
B1:B2 = A1:A2*2
C1:C2 = A1:A2+1
H10 = SUM(A1:A2)
```
