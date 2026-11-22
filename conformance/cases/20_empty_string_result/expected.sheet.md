---
cellprose: 0.3
note: '? = formula with no cached value; open and save in Excel or LibreOffice to compute'
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Empty

## A1:B4

#|A|B
-|-|-
1|Qty|Label
2|3
3|9|big
4|1|?

```formulas
B2:B3 = IF(A2>5,"big","")
B4 = A4*2
```

```cells
E8 = IF(A2>5,"big","")  # ""
```
