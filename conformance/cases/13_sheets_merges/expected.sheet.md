---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Visible

```meta
freeze: C3
```

## A1:C3

#|A|B|C
-|-|-|-
1|Title
2|Sub
3|x|1|2

## A5:B6

#|A|B
-|-|-
5|m|Merged
6|n

```cells
A10: Wide
C10 = 'Bob''s Sheet'!A1+1  # 8
```

```merges
A10:B10
A1:C1
A2:B2
B5:C6
```

# Sheet: Hidden One

```meta
hidden: true
```

## A1:B1

#|A|B
-|-|-
1|h|1

# Sheet: Empty

# Sheet: Deep

```meta
hidden: veryHidden
freeze: A2
```

## A1:A2

#|A
-|-
1|Head
2|1

# Sheet: Bob's Sheet

```cells
A1: 7
```
