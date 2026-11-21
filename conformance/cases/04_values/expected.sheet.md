---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Types

## A1:B21

#|A|B
-|-|-
1|Kind|Value
2|Integer|1200
3|Decimal|0.125
4|Small|-3.2e-07
5|Boolean|TRUE
6|Date|2026-10-07
7|Date-time|2026-10-07T14:30:05
8|Time|09:05:00
9|Error|#DIV/0!
10|Empty
11|Text|Revenue
12|Looks numeric|'00123
13|Looks like a formula|'=not a formula
14|Looks boolean|'TRUE
15|Pipe|a\|b
16|Backslash|C:\\dir\\
17|Line break|line1<br>line2
18|Literal tag|1 \<br> 2
19|Padded|" padded "
20|Quoted|"""hello"""
21|Leading apostrophe|''quoted

```formats
B6 = yyyy-mm-dd
B7 = yyyy-mm-dd hh:mm:ss
B8 = hh:mm:ss
```
