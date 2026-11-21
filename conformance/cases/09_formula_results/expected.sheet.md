---
cellprose: 0.3
note: '? = formula with no cached value; open and save in Excel or LibreOffice to compute'
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Results

## A1:B16

#|A|B
-|-|-
1|Kind|Result
2|Rounded to 6 figures|1515990
3|Fraction|0.246667
4|One third|0.333333
5|Integer-valued float|3
6|Large|1234570
7|Negative|-2.5
8|Tiny|1.23457e-05
9|Boundary 1e-4|0.0001
10|Boolean|TRUE
11|Error|#DIV/0!
12|Text result|abc
13|Date result|2026-10-07
14|No cached value|?
15|Typed, not rounded|0.30000000000000004
16|Typed integer-valued|5

```formulas
B2 = 1515987648/1000
B3 = 74/300
B4 = 1/3
B5 = 1.5*2
B6 = 12345.675*100
B7 = -20/8
B8 = 1.234567/100000
B9 = 1/10000
B10 = 1>0
B11 = 1/0
B12 = LEFT("abcdef",3)
B13 = DATE(2026,10,7)
B14 = 2*2
```

```formats
B13 = yyyy-mm-dd
```
