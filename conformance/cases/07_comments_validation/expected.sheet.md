---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Budget

## A1:C3

#|A|B|C
-|-|-|-
1|Item|Status|Qty
2|Pens|Yes|5
3|Ink|No|120

```comments
C3: Excludes one-offs.<br>Check with \| finance
```

```validation
B2:B3 = list: "Yes,No"
C2 = whole between: 0 ; 100
```
