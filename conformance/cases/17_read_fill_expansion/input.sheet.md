---
cellprose: 0.3
---

# Sheet: P&L

## A1:G6

#|A|B|C|D|E|F|G
-|-|-|-|-|-|-|-
1||1|2|3
2|10|10|20|30|?|?|?
3|20|20|40|60|?|?|?
4|30|30|60|90|?|?|?
5|Total|60|120|180
6|Name|1|1|1|1|1|1

```formulas
B2:D4 = $A2*B$1
E2:E4 = SUM(B2:D2)
F2:G2 = 'Other Sheet'!B2+$A$1
F3:G4 = Rate*B3
B5:D5 = SUM(B2:B4)
B6:G6 = LEN("B2")+LOG10(B1)
```

# Sheet: Other Sheet

## A1:B2

#|A|B
-|-|-
1|1|2
2|3|4

# Names

```names
Rate = 'P&L'!$A$1
```
