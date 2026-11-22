# Questions (benchmark real-world set)

Every question was made by the rules in `external/realworld2.py` and its answer computed from the file. Under each question is what it was built from: the labels it read, or the formula it traces.

## rw2_dam_ddm2st (damodaran: `ddm2st.xlsx`)

- **q1** (address) Which cell holds the value in the row labelled 'Tax Rate on Income=', in the sheet 'ddm2st.xls'? Give its cell address.
  - answer: `ddm2st.xls!D43`; cell `ddm2st.xls!D43`
  - read: ddm2st.xls!B43 = 'Tax Rate on Income='

- **q2** (trace) Consider the cell ddm2st.xls!D95 (in the row labelled 'Dividends'). List the cells its formula reads directly (not indirectly).
  - answer: `['ddm2st.xls!C95', 'ddm2st.xls!D89', 'ddm2st.xls!D94', 'ddm2st.xls!E24']`; cell `ddm2st.xls!D95`
  - formula: `=IF($E$24<D94," ",C95*(1+$D$89))`

- **q3** (trace) Consider the cell ddm2st.xls!E98 (in the row labelled 'Payout Ratio in Stable Phase ='). List the cells its formula reads directly (not indirectly).
  - answer: `['ddm2st.xls!E63', 'ddm2st.xls!E64', 'ddm2st.xls!E65']`; cell `ddm2st.xls!E98`
  - formula: `=IF(E64="No",E63,E65)`

- **q4** (impact) Suppose the number in ddm2st.xls!E61 (in the row labelled 'Enter growth rate in stable growth period?') were 10% higher. List every other cell whose value would change.
  - answer: `37 cells, e.g. ['ddm2st.xls!D116', 'ddm2st.xls!D117', 'ddm2st.xls!D118']`; cell `ddm2st.xls!E61`

- **q5** (hardcode) Consider the range ddm2st.xls!D86:D89 (the column of 'Growth Rate'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `ddm2st.xls!D86`

## rw2_dam_eqexret (damodaran: `eqexret.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Normalized ROE =', in the sheet 'Normalized Earnings'?
  - answer: `0.22`; cell `Normalized Earnings!B8`
  - read: Normalized Earnings!A8 = 'Normalized ROE ='

- **q2** (address) Which cell holds the value in the row labelled 'Net Income =', in the sheet 'Inputs'? Give its cell address.
  - answer: `Inputs!B2`; cell `Inputs!B2`
  - read: Inputs!A2 = 'Net Income  ='

- **q3** (trace) Consider the cell Excess Return Valuation!F13 (in the row labelled 'Present Value'). List the cells its formula reads directly (not indirectly).
  - answer: `['Excess Return Valuation!F10', 'Excess Return Valuation!F11', 'Excess Return Valuation!F12', 'Excess Return Valuation!F7', 'Inputs!B15']`; cell `Excess Return Valuation!F13`
  - formula: `=IF(Inputs!$B$15<'Excess Return Valuation'!F7," ",IF(Inputs!$B$15='Excess Return Valuation'!F7,(F10+F11)/F12,F10/F12))`

- **q4** (trace) Consider the cell Excess Return Valuation!J23 (in the row labelled 'Retained Earnings'). List the cells its formula reads directly (not indirectly).
  - answer: `['Excess Return Valuation!J22', 'Excess Return Valuation!J7', 'Excess Return Valuation!J8', 'Inputs!B15']`; cell `Excess Return Valuation!J23`
  - formula: `=IF(Inputs!$B$15<'Excess Return Valuation'!J7," ",J8-J22)`

- **q5** (impact) Suppose the number in Inputs!B6 (in the row labelled 'Number of shares outstanding =') were 10% higher. List every other cell whose value would change.
  - answer: `['Excess Return Valuation!B28', 'Excess Return Valuation!B29']`; cell `Inputs!B6`

- **q6** (hardcode) Consider the range Normalized Earnings!B5:G5 (the row of 'Net Income'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Normalized Earnings!B5', 'Normalized Earnings!C5', 'Normalized Earnings!D5', 'Normalized Earnings!E5', 'Normalized Earnings!F5']`; cell `Normalized Earnings!B5`

## rw2_dam_fcfe2st (damodaran: `fcfe2st.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Chg. Working Capital/share =', in the sheet 'NewFCFE2Stage'?
  - answer: `1`; cell `NewFCFE2Stage!D27`
  - read: NewFCFE2Stage!B27 = 'Chg. Working Capital/share ='

- **q2** (trace) Consider the cell NewFCFE2Stage!F132 (in the row labelled 'Value of the stock ='). List the cells its formula reads directly (not indirectly).
  - answer: `['NewFCFE2Stage!F130', 'NewFCFE2Stage!F131']`; cell `NewFCFE2Stage!F132`
  - formula: `=F130+F131`

- **q3** (trace) Consider the cell NewFCFE2Stage!D113 (in the row labelled 'Growth rate in depreciation ='). List the cells its formula reads directly (not indirectly).
  - answer: `['NewFCFE2Stage!D108', 'NewFCFE2Stage!D75', 'NewFCFE2Stage!F72']`; cell `NewFCFE2Stage!D113`
  - formula: `=IF(F72="Yes",D108,D75)`

- **q4** (impact) Suppose the number in NewFCFE2Stage!E50 (in the row labelled 'Book Value of Equity =') were 10% higher. List every other cell whose value would change.
  - answer: `29 cells, e.g. ['NewFCFE2Stage!C53', 'NewFCFE2Stage!C57', 'NewFCFE2Stage!D107']`; cell `NewFCFE2Stage!E50`

- **q5** (hardcode) Consider the range NewFCFE2Stage!D21:D27. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['NewFCFE2Stage!D21', 'NewFCFE2Stage!D22', 'NewFCFE2Stage!D23', 'NewFCFE2Stage!D24', 'NewFCFE2Stage!D25', 'NewFCFE2Stage!D27']`; cell `NewFCFE2Stage!D21`

## rw2_dam_fcff2st (damodaran: `fcff2st.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'EBIT * (1 - tax rate)', column headed 'Terminal Year', in the sheet 'NewFCFF2Stage'?
  - answer: `6494.75424716556`; cell `NewFCFF2Stage!N134`
  - read: NewFCFF2Stage!B134 = 'EBIT * (1 - tax rate)'; NewFCFF2Stage!N133 = 'Terminal Year'

- **q2** (trace) Consider the cell NewFCFF2Stage!F149 (in the row labelled 'Present Value of FCFF in high growth phase ='). List the cells its formula reads directly (not indirectly).
  - answer: `10 cells, e.g. ['NewFCFF2Stage!D138', 'NewFCFF2Stage!E138', 'NewFCFF2Stage!F138']`; cell `NewFCFF2Stage!F149`
  - formula: `=SUM(D138:M138)`

- **q3** (trace) Consider the cell NewFCFF2Stage!E137 (in the row labelled 'Free Cashflow to Firm'). List the cells its formula reads directly (not indirectly).
  - answer: `['NewFCFF2Stage!E133', 'NewFCFF2Stage!E134', 'NewFCFF2Stage!E135', 'NewFCFF2Stage!E136', 'NewFCFF2Stage!E43']`; cell `NewFCFF2Stage!E137`
  - formula: `=IF($E$43<E133," ",E134-E135-E136)`

- **q4** (impact) Suppose the number in NewFCFF2Stage!E30 (in the row labelled 'Book Value of Debt =') were 10% higher. List every other cell whose value would change.
  - answer: `42 cells, e.g. ['NewFCFF2Stage!C67', 'NewFCFF2Stage!D122', 'NewFCFF2Stage!D123']`; cell `NewFCFF2Stage!E30`

- **q5** (hardcode) Consider the range NewFCFF2Stage!I133:I138. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `NewFCFF2Stage!I133`

## rw2_dam_fcffeva (damodaran: `fcffeva.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Revenues', column headed 'Base', in the sheet 'FCFF Valuation'?
  - answer: `12406`; cell `FCFF Valuation!B33`
  - read: FCFF Valuation!A33 = 'Revenues'; FCFF Valuation!B30 = 'Base'

- **q2** (address) Which cell holds the value in the row labelled '- Capital Expenditures', column headed 'Base', in the sheet 'FCFF Valuation'? Give its cell address.
  - answer: `FCFF Valuation!B42`; cell `FCFF Valuation!B42`
  - read: FCFF Valuation!A42 = ' - Capital Expenditures'; FCFF Valuation!B30 = 'Base'

- **q3** (trace) Consider the cell FCFF Valuation!I32 (in the row labelled 'Growth in Deprec'n'). List the cells its formula reads directly (not indirectly).
  - answer: `['FCFF Valuation!E15', 'FCFF Valuation!E23', 'FCFF Valuation!I30', 'FCFF Valuation!L30']`; cell `FCFF Valuation!I32`
  - formula: `=$E$23+(($E$15-$E$23)/5)*($L$30-I30)`

- **q4** (trace) Consider the cell FCFF Valuation!C42 (in the row labelled '- Capital Expenditures'). List the cells its formula reads directly (not indirectly).
  - answer: `['FCFF Valuation!B42', 'FCFF Valuation!E15']`; cell `FCFF Valuation!C42`
  - formula: `=B42*(1+$E$15)`

- **q5** (impact) Suppose the number in FCFF Valuation!E24 (in the row labelled 'Enter operating expenses as a % of revenues in stable period =') were 10% higher. List every other cell whose value would change.
  - answer: `75 cells, e.g. ['EVA Valuation!B10', 'EVA Valuation!B7', 'EVA Valuation!H13']`; cell `FCFF Valuation!E24`

- **q6** (hardcode) Consider the range FCFF Valuation!I30:I33. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['FCFF Valuation!I30']`; cell `FCFF Valuation!I30`

## rw2_dam_fcffgen (damodaran: `fcffgen.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Stock Price=', in the sheet 'Option Valuation'?
  - answer: `84`; cell `Option Valuation!C13`
  - read: Option Valuation!A13 = 'Stock Price='

- **q2** (trace) Consider the cell The Valuation of Amazon!C98 (in the row labelled '- COGS'). List the cells its formula reads directly (not indirectly).
  - answer: `['The Valuation of Amazon!C96', 'The Valuation of Amazon!C97', 'The Valuation of Amazon!D61', 'The Valuation of Amazon!E45']`; cell `The Valuation of Amazon!C98`
  - formula: `=IF($E$45<C96,0,C97*$D61)`

- **q3** (trace) Consider the cell The Valuation of Amazon!L105 (in the row labelled '- Chg. Working Capital'). List the cells its formula reads directly (not indirectly).
  - answer: `['The Valuation of Amazon!E45', 'The Valuation of Amazon!G70', 'The Valuation of Amazon!K97', 'The Valuation of Amazon!L96', 'The Valuation of Amazon!L97']`; cell `The Valuation of Amazon!L105`
  - formula: `=IF($E$45<L96,0,(L97-K97)*$G70)`

- **q4** (impact) Suppose the number in The Valuation of Amazon!F87 (in the row labelled 'If no, enter capital expenditures as % of depreciation in steady state:') were 10% higher. List every other cell whose value would change.
  - answer: `10 cells, e.g. ['Sheet1!C11', 'Sheet1!D11', 'Sheet1!D12']`; cell `The Valuation of Amazon!F87`

- **q5** (hardcode) Consider the range The Valuation of Amazon!B69:G69. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['The Valuation of Amazon!C69']`; cell `The Valuation of Amazon!B69`

## rw2_dam_fcffvsfcfe (damodaran: `fcffvsfcfe.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Reinvestment rate', column headed 'Terminal Year', in the sheet 'Sheet1'?
  - answer: `0.5`; cell `Sheet1!H13`
  - read: Sheet1!A13 = 'Reinvestment rate'; Sheet1!H11 = 'Terminal Year'

- **q2** (trace) Consider the cell Sheet1!G14 (in the row labelled 'EBIT'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!C3', 'Sheet1!F14']`; cell `Sheet1!G14`
  - formula: `=F14*(1+$C$3)`

- **q3** (trace) Consider the cell Sheet1!H18 (in the row labelled 'FCFF'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!H16', 'Sheet1!H17']`; cell `Sheet1!H18`
  - formula: `=H16-H17`

- **q4** (impact) Suppose the number in Sheet1!E11 were 10% higher. List every other cell whose value would change.
  - answer: `31 cells, e.g. ['Sheet1!B21', 'Sheet1!B22', 'Sheet1!B23']`; cell `Sheet1!E11`

- **q5** (hardcode) Consider the range Sheet1!F11:F18. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Sheet1!F11']`; cell `Sheet1!F11`

## rw2_dam_growthbreakdown (damodaran: `growthbreakdown.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Automotive', column headed 'Market Debt/Capital', in the sheet 'Industry averages'?
  - answer: `0.57367970143265`; cell `Industry averages!L7`
  - read: Industry averages!A7 = 'Automotive'; Industry averages!L1 = 'Market Debt/Capital'

- **q2** (address) Which cell holds the value in the row labelled 'Chemical (Basic)', column headed 'Std deviation in stock prices', in the sheet 'Industry averages'? Give its cell address.
  - answer: `Industry averages!J14`; cell `Industry averages!J14`
  - read: Industry averages!A14 = 'Chemical (Basic)'; Industry averages!J1 = 'Std deviation in stock prices'

- **q3** (trace) Consider the cell Cost of capital worksheet!C39 (in the row labelled 'Weight in Cost of Capital'). List the cells its formula reads directly (not indirectly).
  - answer: `['Cost of capital worksheet!C38', 'Cost of capital worksheet!E38']`; cell `Cost of capital worksheet!C39`
  - formula: `=C38/$E$38`

- **q4** (trace) Consider the cell Input page!L45 (in the row labelled 'FCFF'). List the cells its formula reads directly (not indirectly).
  - answer: `['Input page!L43', 'Input page!L44']`; cell `Input page!L45`
  - formula: `=L43-L44`

- **q5** (impact) Suppose the number in Cost of capital worksheet!B5 (in the row labelled 'Current Market Price per share =') were 10% higher. List every other cell whose value would change.
  - answer: `['Cost of capital worksheet!B38', 'Cost of capital worksheet!B39', 'Cost of capital worksheet!B40', 'Cost of capital worksheet!C35', 'Cost of capital worksheet!C39', 'Cost of capital worksheet!E38', 'Cost of capital worksheet!E40']`; cell `Cost of capital worksheet!B5`

- **q6** (hardcode) Consider the range Input page!H42:H46. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Input page!H44']`; cell `Input page!H42`

## rw2_dam_higrowth (damodaran: `higrowth.xlsx`)

- **q1** (address) Which cell holds the value in the row labelled 'Electric Util. (Central)', column headed 'Market Debt/Capital', in the sheet 'Industry Averages'? Give its cell address.
  - answer: `Industry Averages!G24`; cell `Industry Averages!G24`
  - read: Industry Averages!A24 = 'Electric Util. (Central)'; Industry Averages!G1 = 'Market Debt/Capital'

- **q2** (trace) Consider the cell DCFValuation!G6 (in the row labelled 'Taxes'). List the cells its formula reads directly (not indirectly).
  - answer: `['DCFValuation!F12', 'DCFValuation!G5', 'Input Sheet(assumtion)!B17']`; cell `DCFValuation!G6`
  - formula: `=IF(G5<0,0,IF(F12>G5,0,(G5-F12)*'Input Sheet(assumtion)'!$B$17))`

- **q3** (trace) Consider the cell Other Expenses to Capitalize!C34. List the cells its formula reads directly (not indirectly).
  - answer: `['Other Expenses to Capitalize!A34', 'Other Expenses to Capitalize!F6']`; cell `Other Expenses to Capitalize!C34`
  - formula: `=IF(A34<0,($F$6+A34)/$F$6,0)`

- **q4** (impact) Suppose the number in R&D!F6 (in the row labelled 'Over how many years do you want to amortize R&D expenses') were 10% higher. List every other cell whose value would change.
  - answer: `19 cells, e.g. ['R&D!A14', 'R&D!A28', 'R&D!C25']`; cell `R&D!F6`

- **q5** (hardcode) Consider the range Revenue Growth Numbers!B3:B13 (the column of 'Expected Growth Rate'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `10 cells, e.g. ['Revenue Growth Numbers!B10', 'Revenue Growth Numbers!B11', 'Revenue Growth Numbers!B12']`; cell `Revenue Growth Numbers!B3`

## rw2_dam_macrodur (damodaran: `macrodur.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'FURNITURE & FIXTURES MFRS', column headed 'Currency', in the sheet 'Bottom up Estimator'?
  - answer: `-0.106140354757438`; cell `Bottom up Estimator!O34`
  - read: Bottom up Estimator!K34 = 'FURNITURE & FIXTURES MFRS'; Bottom up Estimator!O9 = 'Currency'

- **q2** (address) Which cell holds the value in the row labelled 'Cyclicality of firm's assets =', column headed 'Based on Firm Value', in the sheet 'Duration Calculator'? Give its cell address.
  - answer: `Duration Calculator!C6`; cell `Duration Calculator!C6`
  - read: Duration Calculator!A6 = "Cyclicality of firm's assets ="; Duration Calculator!C3 = 'Based on Firm Value'

- **q3** (trace) Consider the cell Annual Data!C16. List the cells its formula reads directly (not indirectly).
  - answer: `['Annual Data!B16', 'Annual Data!B17']`; cell `Annual Data!C16`
  - formula: `=(B16-B17)/(1+B17)`

- **q4** (trace) Consider the cell Annual Data!I14. List the cells its formula reads directly (not indirectly).
  - answer: `['Annual Data!H14', 'Annual Data!H15']`; cell `Annual Data!I14`
  - formula: `=(H14-H15)/H15`

- **q5** (impact) Suppose the number in Quarterly Data!P71 were 10% higher. List every other cell whose value would change.
  - answer: `['Quarterly Data!Q70', 'Quarterly Data!Q71']`; cell `Quarterly Data!P71`

- **q6** (hardcode) Consider the range Quarterly Data!A91:I91. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Quarterly Data!A91', 'Quarterly Data!B91', 'Quarterly Data!D91', 'Quarterly Data!F91', 'Quarterly Data!H91']`; cell `Quarterly Data!A91`

## rw2_dam_normearn (damodaran: `normearn.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Chemical (Diversified)', column headed 'MV Debt to Capital Ratio', in the sheet 'Industry averages'?
  - answer: `0.21457200226403`; cell `Industry averages!G20`
  - read: Industry averages!A20 = 'Chemical (Diversified)'; Industry averages!G1 = 'MV Debt to Capital Ratio'

- **q2** (address) Which cell holds the value in the row labelled 'Semiconductor', in the sheet 'R&D converter'? Give its cell address.
  - answer: `R&D converter!B128`; cell `R&D converter!B128`
  - read: R&D converter!A128 = 'Semiconductor'

- **q3** (trace) Consider the cell R&D converter!D33. List the cells its formula reads directly (not indirectly).
  - answer: `['R&D converter!B33', 'R&D converter!C33']`; cell `R&D converter!D33`
  - formula: `=B33*C33`

- **q4** (trace) Consider the cell R&D converter!C30. List the cells its formula reads directly (not indirectly).
  - answer: `['R&D converter!A30', 'R&D converter!F6']`; cell `R&D converter!C30`
  - formula: `=IF(A30<0,($F$6+A30)/$F$6,0)`

- **q5** (impact) Suppose the number in Operating lease converter!B8 were 10% higher. List every other cell whose value would change.
  - answer: `['Operating lease converter!B26', 'Operating lease converter!C26', 'Operating lease converter!C30', 'Operating lease converter!F33', 'Operating lease converter!F34', 'Operating lease converter!F35']`; cell `Operating lease converter!B8`

- **q6** (hardcode) Consider the range Earnings Normalizer & Output!B19:G19 (the row of 'Revenues'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Earnings Normalizer & Output!B19', 'Earnings Normalizer & Output!C19', 'Earnings Normalizer & Output!D19', 'Earnings Normalizer & Output!E19', 'Earnings Normalizer & Output!F19']`; cell `Earnings Normalizer & Output!B19`

## rw2_dam_r_dconv (damodaran: `R&DConv.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Operating income', column headed 'With capitalizing', in the sheet 'R&D capitalizer'?
  - answer: `7880.8`; cell `R&D capitalizer!C30`
  - read: R&D capitalizer!A30 = 'Operating income'; R&D capitalizer!C29 = 'With capitalizing'

- **q2** (address) Which cell holds the value in the row labelled 'Auto Parts (Replacement)', column headed 'Amortization Period', in the sheet 'Amortizable Lives Look-up Table'? Give its cell address.
  - answer: `Amortizable Lives Look-up Table!B9`; cell `Amortizable Lives Look-up Table!B9`
  - read: Amortizable Lives Look-up Table!A9 = 'Auto Parts (Replacement)'; Amortizable Lives Look-up Table!B1 = 'Amortization Period'

- **q3** (trace) Consider the cell R&D capitalizer!C34 (in the row labelled 'Invested Capital'). List the cells its formula reads directly (not indirectly).
  - answer: `['R&D capitalizer!B34', 'R&D capitalizer!D24']`; cell `R&D capitalizer!C34`
  - formula: `=B34+D24`

- **q4** (trace) Consider the cell R&D capitalizer!E20. List the cells its formula reads directly (not indirectly).
  - answer: `['Inputs!F17', 'R&D capitalizer!A20', 'R&D capitalizer!B20']`; cell `R&D capitalizer!E20`
  - formula: `=IF(A20<0,B20/Inputs!$F$17,0)`

- **q5** (impact) Suppose the number in Inputs!B12 (in the row labelled 'Book value of debt') were 10% higher. List every other cell whose value would change.
  - answer: `['R&D capitalizer!B34', 'R&D capitalizer!B36', 'R&D capitalizer!C34', 'R&D capitalizer!C36']`; cell `Inputs!B12`

- **q6** (hardcode) Consider the range Inputs!A22:A41 (the column of 'Year'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Inputs!A22']`; cell `Inputs!A22`

## rw2_dam_returncalculator (damodaran: `returncalculator.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Water Utility', in the sheet 'R&D Converter'?
  - answer: `10`; cell `R&D Converter!B142`
  - read: R&D Converter!A142 = 'Water Utility'

- **q2** (address) Which cell holds the value in the row labelled 'Medical Services', in the sheet 'R&D Converter'? Give its cell address.
  - answer: `R&D Converter!B105`; cell `R&D Converter!B105`
  - read: R&D Converter!A105 = 'Medical Services'

- **q3** (trace) Consider the cell Accounting Return Output!B19 (in the row labelled '+ Goodwill add back'). List the cells its formula reads directly (not indirectly).
  - answer: `['Input Sheet!B11', 'Input Sheet!B29', 'Input Sheet!B30']`; cell `Accounting Return Output!B19`
  - formula: `=IF('Input Sheet'!B29="Yes",0,'Input Sheet'!B30*'Input Sheet'!B11)`

- **q4** (trace) Consider the cell Accounting Return Output!B20 (in the row labelled '+ Cash add back'). List the cells its formula reads directly (not indirectly).
  - answer: `['Input Sheet!B10', 'Input Sheet!B33', 'Input Sheet!B34']`; cell `Accounting Return Output!B20`
  - formula: `=IF('Input Sheet'!B33="Yes",0,'Input Sheet'!B34*'Input Sheet'!B10)`

- **q5** (impact) Suppose the number in R&D Converter!B11 were 10% higher. List every other cell whose value would change.
  - answer: `['R&D Converter!B25', 'R&D Converter!D25', 'R&D Converter!D35', 'R&D Converter!D37', 'R&D Converter!D39', 'R&D Converter!E25', 'R&D Converter!E35']`; cell `R&D Converter!B11`

- **q6** (hardcode) Consider the range R&D Converter!A11:A20 (the column of 'Year'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['R&D Converter!A11']`; cell `R&D Converter!A11`

## rw2_dam_reval (damodaran: `reval.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Inflation rate for real estate taxes =', column headed 'In terminal year', in the sheet 'Inputs & Property valuation'?
  - answer: `0.03`; cell `Inputs & Property valuation!C7`
  - read: Inputs & Property valuation!A7 = 'Inflation rate for real estate taxes ='; Inputs & Property valuation!C2 = 'In terminal year'

- **q2** (address) Which cell holds the value in the row labelled 'Depreciation', column headed 'Terminal year', in the sheet 'Inputs & Property valuation'? Give its cell address.
  - answer: `Inputs & Property valuation!H32`; cell `Inputs & Property valuation!H32`
  - read: Inputs & Property valuation!A32 = 'Depreciation'; Inputs & Property valuation!H14 = 'Terminal year'

- **q3** (trace) Consider the cell Inputs & Property valuation!D31 (in the row labelled 'Operating income before depreciation'). List the cells its formula reads directly (not indirectly).
  - answer: `['Inputs & Property valuation!D22', 'Inputs & Property valuation!D29']`; cell `Inputs & Property valuation!D31`
  - formula: `=D22-D29`

- **q4** (trace) Consider the cell Inputs & Property valuation!C21 (in the row labelled 'Credit Loss'). List the cells its formula reads directly (not indirectly).
  - answer: `['Inputs & Property valuation!B21', 'Inputs & Property valuation!C18']`; cell `Inputs & Property valuation!C21`
  - formula: `=C18*$B$21`

- **q5** (impact) Suppose the number in Inputs & Property valuation!E14 were 10% higher. List every other cell whose value would change.
  - answer: `74 cells, e.g. ['Equity valuation!B2', 'Equity valuation!B31', 'Equity valuation!C19']`; cell `Inputs & Property valuation!E14`

- **q6** (hardcode) Consider the range Inputs & Property valuation!G14:G22. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Inputs & Property valuation!G14']`; cell `Inputs & Property valuation!G14`

## rw2_dam_risk (damodaran: `risk.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Number of periods of data=', in the sheet 'Risk&RetWS'?
  - answer: `53`; cell `Risk&RetWS!C2`
  - read: Risk&RetWS!A2 = 'Number of periods of data='

- **q2** (address) Which cell holds the value in the row labelled 'Current riskfree rate =', in the sheet 'Risk&RetWS'? Give its cell address.
  - answer: `Risk&RetWS!C1`; cell `Risk&RetWS!C1`
  - read: Risk&RetWS!A1 = 'Current riskfree rate ='

- **q3** (trace) Consider the cell Risk&RetWS!G59. List the cells its formula reads directly (not indirectly).
  - answer: `['Risk&RetWS!B59', 'Risk&RetWS!C58', 'Risk&RetWS!C59', 'Risk&RetWS!D59', 'Risk&RetWS!E59']`; cell `Risk&RetWS!G59`
  - formula: `=((C59*E59-C58+D59*E59)/C58)*B59`

- **q4** (trace) Consider the cell Risk&RetWS!B54. List the cells its formula reads directly (not indirectly).
  - answer: `['Risk&RetWS!A54', 'Risk&RetWS!C2']`; cell `Risk&RetWS!B54`
  - formula: `=IF(A54>$C2,0,1)`

- **q5** (impact) Suppose the number in Risk&RetWS!C44 were 10% higher. List every other cell whose value would change.
  - answer: `120 cells, e.g. ['Risk&RetWS!D67', 'Risk&RetWS!D68', 'Risk&RetWS!D69']`; cell `Risk&RetWS!C44`

- **q6** (hardcode) Consider the range Risk&RetWS!E56:K56. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Risk&RetWS!E56', 'Risk&RetWS!F56']`; cell `Risk&RetWS!E56`

## rw2_enron_andy_zipper (enron: `andy_zipper__154__ICE - Mar28 Power & Gas VOL.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Wade Hicks', column headed 'Total Volume', in the sheet 'DD-EGL'?
  - answer: `25000`; cell `DD-EGL!C10`
  - read: DD-EGL!A10 = 'Wade Hicks'; DD-EGL!C9 = 'Total Volume'

- **q2** (address) Which cell holds the value in the row labelled 'Susan Pereira', column headed 'Notional Volume', in the sheet 'Enron Activity - Dynegy Direct'? Give its cell address.
  - answer: `Enron Activity - Dynegy Direct!D18`; cell `Enron Activity - Dynegy Direct!D18`
  - read: Enron Activity - Dynegy Direct!B18 = 'Susan Pereira'; Enron Activity - Dynegy Direct!D10 = 'Notional Volume'

- **q3** (trace) Consider the cell DD-EGL!C322 (in the row labelled '#N/A'). List the cells its formula reads directly (not indirectly).
  - answer: `['DD-EGL!B322', 'DD-EGL!W322']`; cell `DD-EGL!C322`
  - formula: `=B322*W322`

- **q4** (trace) Consider the cell DD-EPM!F109 (in the row labelled '#N/A'). List the cells its formula reads directly (not indirectly).
  - answer: `['DD-EPM!AA109', 'DD-EPM!E109']`; cell `DD-EPM!F109`
  - formula: `=E109*AA109`

- **q5** (hardcode) Consider the range DD-EPM!A27:F27. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `DD-EPM!A27`

## rw2_enron_benjamin_rogers (enron: `benjamin_rogers__1024__TLR Analysis.xlsx`)

- **q1** (lookup) What is the value in the row labelled '2c', column headed 'Number of Incidents', in the sheet 'Sept'?
  - answer: `2`; cell `Sept!C8`
  - read: Sept!B8 = '2c'; Sept!C4 = 'Number of Incidents'

- **q2** (address) Which cell holds the value in the row labelled '2a', column headed 'Number of Incidents', in the sheet 'Sept'? Give its cell address.
  - answer: `Sept!C6`; cell `Sept!C6`
  - read: Sept!B6 = '2a'; Sept!C4 = 'Number of Incidents'

- **q3** (trace) Consider the cell Summary!D16 (in the row labelled 'Annual Totals'). List the cells its formula reads directly (not indirectly).
  - answer: `12 cells, e.g. ['Summary!D10', 'Summary!D11', 'Summary!D12']`; cell `Summary!D16`
  - formula: `=SUM(D4:D15)`

- **q4** (trace) Consider the cell Summary!I5 (in the row labelled 'Feb'). List the cells its formula reads directly (not indirectly).
  - answer: `['Summary!C5', 'Summary!D5', 'Summary!E5', 'Summary!F5', 'Summary!G5', 'Summary!H5']`; cell `Summary!I5`
  - formula: `=SUM(C5:H5)`

- **q5** (impact) Suppose the number in Jul!C7 (in the row labelled '2b') were 10% higher. List every other cell whose value would change.
  - answer: `9 cells, e.g. ['Jul!C13', 'Summary!E10', 'Summary!E16']`; cell `Jul!C7`

- **q6** (hardcode) Consider the range Nov!C5:C13 (the column of 'Number of Incidents'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Nov!C10', 'Nov!C11', 'Nov!C12', 'Nov!C5', 'Nov!C6', 'Nov!C7', 'Nov!C8', 'Nov!C9']`; cell `Nov!C5`

## rw2_enron_chris_germany (enron: `chris_germany__1745__allegheny.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'CGLF Index December 1999', in the sheet 'Sheet1'?
  - answer: `2.11`; cell `Sheet1!F145`
  - read: Sheet1!A145 = 'CGLF Index  December 1999'

- **q2** (address) Which cell holds the value in the row labelled 'CGLF Index August 1999', in the sheet 'Sheet1'? Give its cell address.
  - answer: `Sheet1!F61`; cell `Sheet1!F61`
  - read: Sheet1!A61 = 'CGLF Index  August 1999'

- **q3** (trace) Consider the cell Sheet1!C202 (in the row labelled 'Fuel Price'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!C201', 'Sheet1!E196', 'Sheet1!F189']`; cell `Sheet1!C202`
  - formula: `=ROUND((F189+E196)/(1-C201)-(F189+E196),4)`

- **q4** (trace) Consider the cell Sheet1!C152 (in the row labelled 'Transport'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!C148', 'Sheet1!C149', 'Sheet1!C150', 'Sheet1!F145']`; cell `Sheet1!C152`
  - formula: `=(ROUND(+F145/(1-C150)-F145,4)+C148+C149)`

- **q5** (impact) Suppose the number in Sheet1!C149 (in the row labelled 'Aca') were 10% higher. List every other cell whose value would change.
  - answer: `['Sheet1!C152', 'Sheet1!E152', 'Sheet1!E162', 'Sheet1!F163']`; cell `Sheet1!C149`

- **q6** (hardcode) Consider the range Sheet1!C127:C131. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Sheet1!C127', 'Sheet1!C128', 'Sheet1!C129']`; cell `Sheet1!C127`

## rw2_enron_daren_farmer (enron: `daren_farmer__6595__HPL-Feb.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Total Available', column headed 'Month to Date', in the sheet 'Feb 00'?
  - answer: `5391735`; cell `Feb 00!AB23`
  - read: Feb 00!A23 = 'Total Available'; Feb 00!AB5 = 'Month to Date'

- **q2** (address) Which cell holds the value in the row labelled 'HPL Points', column headed 'Month to Date', in the sheet 'Feb 00'? Give its cell address.
  - answer: `Feb 00!AB10`; cell `Feb 00!AB10`
  - read: Feb 00!C10 = 'HPL  Points'; Feb 00!AB5 = 'Month to Date'

- **q3** (trace) Consider the cell Feb 00!U33 (in the row labelled 'Subtotal'). List the cells its formula reads directly (not indirectly).
  - answer: `['Feb 00!U28', 'Feb 00!U29', 'Feb 00!U30', 'Feb 00!U31', 'Feb 00!U32']`; cell `Feb 00!U33`
  - formula: `=SUM(U28:U32)`

- **q4** (trace) Consider the cell Feb 00!I15 (in the row labelled 'Total HPL'). List the cells its formula reads directly (not indirectly).
  - answer: `['Feb 00!I10', 'Feb 00!I11', 'Feb 00!I12', 'Feb 00!I13', 'Feb 00!I14']`; cell `Feb 00!I15`
  - formula: `=SUM(I10:I14)`

- **q5** (impact) Suppose the number in Feb 00!Y51 (in the row labelled 'Lufkin Diboll') were 10% higher. List every other cell whose value would change.
  - answer: `13 cells, e.g. ['Feb 00!AB13', 'Feb 00!AB15', 'Feb 00!AB23']`; cell `Feb 00!Y51`

- **q6** (hardcode) Consider the range Feb 00!S40:S46. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Feb 00!S40', 'Feb 00!S41', 'Feb 00!S42', 'Feb 00!S44', 'Feb 00!S45', 'Feb 00!S46']`; cell `Feb 00!S40`

## rw2_enron_james_steffes (enron: `james_steffes__12835__PX Values.xlsx`)

- **q1** (address) Which cell holds the value in the row labelled 'March 1 to April 1', column headed 'kWh Sales', in the sheet 'compare'? Give its cell address.
  - answer: `compare!L23`; cell `compare!L23`
  - read: compare!H23 = 'March 1 to April 1'; compare!L16 = 'kWh Sales'

- **q2** (trace) Consider the cell PG&E tables!D38 (in the row labelled 'Subtotal'). List the cells its formula reads directly (not indirectly).
  - answer: `['PG&E tables!D33', 'PG&E tables!D34', 'PG&E tables!D35', 'PG&E tables!D36', 'PG&E tables!D37']`; cell `PG&E tables!D38`
  - formula: `=SUM(D33:D37)`

- **q3** (trace) Consider the cell PG&E tables!E38 (in the row labelled 'Subtotal'). List the cells its formula reads directly (not indirectly).
  - answer: `['PG&E tables!E33', 'PG&E tables!E34', 'PG&E tables!E35', 'PG&E tables!E36', 'PG&E tables!E37']`; cell `PG&E tables!E38`
  - formula: `=SUM(E33:E37)`

- **q4** (impact) Suppose the number in PG&E tables!D20 (in the row labelled 'May 27 3-cent surcharge') were 10% higher. List every other cell whose value would change.
  - answer: `16 cells, e.g. ['PG&E tables!E20', 'PG&E tables!E21', 'PG&E tables!E24']`; cell `PG&E tables!D20`

- **q5** (hardcode) Consider the range PG&E tables!D33:D39 (the column of '$/MWh'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['PG&E tables!D33', 'PG&E tables!D34', 'PG&E tables!D35', 'PG&E tables!D36', 'PG&E tables!D37', 'PG&E tables!D39']`; cell `PG&E tables!D33`

## rw2_enron_jonathan_mckay (enron: `jonathan_mckay__16929__grandview buy.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'November', column headed 'Rate 11 Total', in the sheet 'Enron Direct Deal Sheet'?
  - answer: `806`; cell `Enron Direct Deal Sheet!G25`
  - read: Enron Direct Deal Sheet!B25 = 'November'; Enron Direct Deal Sheet!G13 = 'Rate 11 Total'

- **q2** (trace) Consider the cell Enron Direct Deal Sheet!F28 (in the row labelled 'TOTAL:'). List the cells its formula reads directly (not indirectly).
  - answer: `12 cells, e.g. ['Enron Direct Deal Sheet!F15', 'Enron Direct Deal Sheet!F16', 'Enron Direct Deal Sheet!F17']`; cell `Enron Direct Deal Sheet!F28`
  - formula: `=SUM(F15:F26)`

- **q3** (trace) Consider the cell Enron Direct Deal Sheet!E16 (in the row labelled 'February'). List the cells its formula reads directly (not indirectly).
  - answer: `['Enron Direct Deal Sheet!B10', 'Enron Direct Deal Sheet!C16']`; cell `Enron Direct Deal Sheet!E16`
  - formula: `=ROUND(C16*$B$10,0)`

- **q4** (impact) Suppose the number in Enron Direct Deal Sheet!C19 (in the row labelled 'May') were 10% higher. List every other cell whose value would change.
  - answer: `['Enron Direct Deal Sheet!C28', 'Enron Direct Deal Sheet!D28', 'Enron Direct Deal Sheet!G19', 'Enron Direct Deal Sheet!G28']`; cell `Enron Direct Deal Sheet!C19`

- **q5** (hardcode) Consider the range Enron Direct Deal Sheet!G15:G26 (the column of 'Rate 11 Total'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `Enron Direct Deal Sheet!G15`

## rw2_enron_kevin_presto (enron: `kevin_presto__19901__10-24 1000 Report.xlsx`)

- **q1** (trace) Consider the cell PJM!C18 (in the row labelled 'Chalk Point'). List the cells its formula reads directly (not indirectly).
  - answer: `9 cells, e.g. ['PJM!H10', 'PJM!H11', 'PJM!H12']`; cell `PJM!C18`
  - formula: `=SUM(H10:H18)`

- **q2** (trace) Consider the cell NPCC!C18 (in the row labelled 'Manchester Street'). List the cells its formula reads directly (not indirectly).
  - answer: `['NPCC!H16', 'NPCC!H17', 'NPCC!H18']`; cell `NPCC!C18`
  - formula: `=SUM(H16:H18)`

- **q3** (impact) Suppose the number in PJM!H25 (in the row labelled 'Coal') were 10% higher. List every other cell whose value would change.
  - answer: `['PJM!C25', 'PJM!C48']`; cell `PJM!H25`

- **q4** (hardcode) Consider the range NPCC!G17:L17 (the row of 'Gas'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['NPCC!G17', 'NPCC!H17']`; cell `NPCC!G17`

## rw2_enron_lisa_gang (enron: `lisa_gang__22393__Hanson Scheduling Model_4_16.xlsx`)

- **q1** (address) Which cell holds the value in the row labelled 'Preschedule Quantity for Tuesday', column headed 'Total', in the sheet 'Scheduling'? Give its cell address.
  - answer: `Scheduling!AA16`; cell `Scheduling!AA16`
  - read: Scheduling!B16 = 'Preschedule Quantity for Tuesday'; Scheduling!AA10 = 'Total'

- **q2** (trace) Consider the cell Scheduling!E26 (in the row labelled 'Real Time Decremental Quantity (Hanson needs to sell) for Tuesday'). List the cells its formula reads directly (not indirectly).
  - answer: `['Scheduling!AJ5', 'Scheduling!E20', 'Scheduling!E23']`; cell `Scheduling!E26`
  - formula: `=IF($AJ$5=6,"",(E20-E23))`

- **q3** (trace) Consider the cell Scheduling!O20 (in the row labelled 'Total Decremental Quantity (Hanson needs to sell) for Tuesday'). List the cells its formula reads directly (not indirectly).
  - answer: `['Scheduling!AJ5', 'Scheduling!O12', 'Scheduling!O14']`; cell `Scheduling!O20`
  - formula: `=IF($AJ$5=6,"",ROUND(IF(O14>O12,0,O14-O12),0))`

- **q4** (impact) Suppose the number in Scheduling!H14 (in the row labelled 'Expected Usage for Tuesday') were 10% higher. List every other cell whose value would change.
  - answer: `['Scheduling!AA14', 'Scheduling!AA16', 'Scheduling!H16', 'Scheduling!H18', 'Scheduling!H24']`; cell `Scheduling!H14`

- **q5** (hardcode) Consider the range Scheduling!M16:M27 (the column of 'HE'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `Scheduling!M16`

## rw2_enron_lynn_blair (enron: `lynn_blair__24402__JKnight Gathering Imb thru 4-01.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Total of all OBA's:', column headed 'DOLLAR VALUE **', in the sheet 'Conf. Letter Imb. Comparison'?
  - answer: `-2123900.63`; cell `Conf. Letter Imb. Comparison!H32`
  - read: Conf. Letter Imb. Comparison!B32 = "        Total of all OBA's:"; Conf. Letter Imb. Comparison!H7 = 'DOLLAR VALUE **'

- **q2** (address) Which cell holds the value in the row labelled 'Total of all OBA's:', column headed 'QTY BALANCE', in the sheet 'Conf. Letter Imb. Comparison'? Give its cell address.
  - answer: `Conf. Letter Imb. Comparison!F32`; cell `Conf. Letter Imb. Comparison!F32`
  - read: Conf. Letter Imb. Comparison!B32 = "        Total of all OBA's:"; Conf. Letter Imb. Comparison!F7 = 'QTY BALANCE'

- **q3** (trace) Consider the cell Original OBA's!I86 (in the row labelled '25781 - Pleasant Valley'). List the cells its formula reads directly (not indirectly).
  - answer: `["Original OBA's!G86", "Original OBA's!H86"]`; cell `Original OBA's!I86`
  - formula: `=H86-G86`

- **q4** (trace) Consider the cell Ellis-Woodward-Clark!P11. List the cells its formula reads directly (not indirectly).
  - answer: `['Ellis-Woodward-Clark!P10', 'Ellis-Woodward-Clark!P8', 'Ellis-Woodward-Clark!P9']`; cell `Ellis-Woodward-Clark!P11`
  - formula: `=SUM(P8:P10)`

- **q5** (impact) Suppose the number in Original OBA's!G56 (in the row labelled '51 - Finney 1') were 10% higher. List every other cell whose value would change.
  - answer: `["Original OBA's!G63", "Original OBA's!I56", "Original OBA's!I63"]`; cell `Original OBA's!G56`

- **q6** (hardcode) Consider the range Original OBA's!AS28:AS34 (the column of 'Variance'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `["Original OBA's!AS28", "Original OBA's!AS29", "Original OBA's!AS30", "Original OBA's!AS31", "Original OBA's!AS33"]`; cell `Original OBA's!AS28`

## rw2_enron_mary_hain (enron: `mary_hain__25858__EnronMarch2001.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'ADMINISTRATIVE CHARGE', in the sheet 'MAR7'?
  - answer: `41.4491`; cell `MAR7!AG93`
  - read: MAR7!AF93 = 'ADMINISTRATIVE CHARGE'

- **q2** (address) Which cell holds the value in the row labelled 'Financial', in the sheet 'MAR7'? Give its cell address.
  - answer: `MAR7!E5`; cell `MAR7!E5`
  - read: MAR7!B5 = 'Financial'

- **q3** (trace) Consider the cell MAR7!X69. List the cells its formula reads directly (not indirectly).
  - answer: `['MAR7!AA63', 'MAR7!AA64', 'MAR7!AA65', 'MAR7!AA66', 'MAR7!AA67', 'MAR7!AA68']`; cell `MAR7!X69`
  - formula: `=SUM(AA63:AA68)`

- **q4** (trace) Consider the cell MAR7!AA69. List the cells its formula reads directly (not indirectly).
  - answer: `['MAR7!AD63', 'MAR7!AD64', 'MAR7!AD65', 'MAR7!AD66', 'MAR7!AD67', 'MAR7!AD68']`; cell `MAR7!AA69`
  - formula: `=SUM(AD63:AD68)`

- **q5** (impact) Suppose the number in MAR7!AB39 were 10% higher. List every other cell whose value would change.
  - answer: `10 cells, e.g. ['MAR7!AB40', 'MAR7!AB42', 'MAR7!AG40']`; cell `MAR7!AB39`

- **q6** (hardcode) Consider the range MAR7!Q84:Q88. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['MAR7!Q85']`; cell `MAR7!Q84`

## rw2_enron_phillip_allen (enron: `phillip_allen__28908__version 12_17.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Tax @ 40%', in the sheet 'Proforma'?
  - answer: `-24307.043974524626`; cell `Proforma!Y61`
  - read: Proforma!Q61 = 'Tax @ 40%'

- **q2** (address) Which cell holds the value in the row labelled 'Builder's Risk', column headed '% Tcost', in the sheet 'Initial Mix'? Give its cell address.
  - answer: `Initial Mix!D11`; cell `Initial Mix!D11`
  - read: Initial Mix!B11 = "Builder's Risk"; Initial Mix!D6 = '% Tcost'

- **q3** (trace) Consider the cell Initial Mix!AC93 (in the row labelled 'Parking & Drives'). List the cells its formula reads directly (not indirectly).
  - answer: `['Initial Mix!AB7', 'Initial Mix!AB93']`; cell `Initial Mix!AC93`
  - formula: `=+AB93/AB$7`

- **q4** (trace) Consider the cell UCost Final!AC153 (in the row labelled 'Less Defferred C. Profit'). List the cells its formula reads directly (not indirectly).
  - answer: `['UCost Final!AB153', 'UCost Final!AB9']`; cell `UCost Final!AC153`
  - formula: `=+AB153/AB$9`

- **q5** (impact) Suppose the number in UCost Final!N94 (in the row labelled 'Lump Sum') were 10% higher. List every other cell whose value would change.
  - answer: `['UCost Final!O110', 'UCost Final!O124', 'UCost Final!O125', 'UCost Final!O94', 'UCost Final!P110', 'UCost Final!P124', 'UCost Final!P125', 'UCost Final!P94']`; cell `UCost Final!N94`

- **q6** (hardcode) Consider the range UCost Final!AP26:AP40 (the column of 'Estimate Totals'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['UCost Final!AP28', 'UCost Final!AP32', 'UCost Final!AP34']`; cell `UCost Final!AP26`

## rw2_enron_phillip_platter (enron: `phillip_platter__31383__EES_Schedule.xlsx`)

- **q1** (trace) Consider the cell day 4!H108 (in the row labelled 'EES/EEMC(PGES)'). List the cells its formula reads directly (not indirectly).
  - answer: `['day 4!H106', 'day 4!H107']`; cell `day 4!H108`
  - formula: `=H106+H107`

- **q2** (trace) Consider the cell EES-Schedule day 1!J14 (in the row labelled 'EEMC (PGES)'). List the cells its formula reads directly (not indirectly).
  - answer: `['EES-Schedule day 1!J11', 'EES-Schedule day 1!J12', 'EES-Schedule day 1!J13']`; cell `EES-Schedule day 1!J14`
  - formula: `=SUM(J11:J13)`

- **q3** (impact) Suppose the number in EES-Schedule day 1!F104 (in the row labelled 'EES') were 10% higher. List every other cell whose value would change.
  - answer: `['EES-Schedule day 1!D104', 'EES-Schedule day 1!D107', 'EES-Schedule day 1!D108', 'EES-Schedule day 1!D130', 'EES-Schedule day 1!F107', 'EES-Schedule day 1!F108', 'EES-Schedule day 1!F130']`; cell `EES-Schedule day 1!F104`

- **q4** (hardcode) Consider the range day 4!U7:U19. List the cells that hold typed-in numbers rather than formulas.
  - answer: `10 cells, e.g. ['day 4!U10', 'day 4!U11', 'day 4!U12']`; cell `day 4!U7`

## rw2_enron_rick_buy (enron: `rick_buy__32818__NP Daily Marks.xlsx`)

- **q1** (lookup) What is the value in the row labelled 'Enron North America Corp.', column headed 'Net Exp.', in the sheet 'COB 091701'?
  - answer: `56160711`; cell `COB 091701!E9`
  - read: COB 091701!A9 = 'Enron North America Corp.'; COB 091701!E7 = 'Net Exp.'

- **q2** (address) Which cell holds the value in the row labelled 'Enron North America Corp.', column headed 'Net Exp.', in the sheet 'COB 100101'? Give its cell address.
  - answer: `COB 100101!G9`; cell `COB 100101!G9`
  - read: COB 100101!A9 = 'Enron North America Corp.'; COB 100101!G7 = 'Net Exp.'

- **q3** (trace) Consider the cell Breakdown!AA18 (in the row labelled 'Total Exposure'). List the cells its formula reads directly (not indirectly).
  - answer: `['Breakdown!Y18', 'Breakdown!Z18']`; cell `Breakdown!AA18`
  - formula: `=Y18-Z18`

- **q4** (trace) Consider the cell Breakdown!AG16 (in the row labelled 'Total Power'). List the cells its formula reads directly (not indirectly).
  - answer: `['Breakdown!AG13', 'Breakdown!AG14', 'Breakdown!AG15']`; cell `Breakdown!AG16`
  - formula: `=SUM(AG13:AG15)`

- **q5** (impact) Suppose the number in COB 082801!D8 (in the row labelled 'Enron Energy Services, Inc.') were 10% higher. List every other cell whose value would change.
  - answer: `['COB 082801!D11', 'COB 082801!E11', 'COB 082801!E8', 'COB 082801!G11', 'COB 082801!G8', 'Daily Change Graph!C4', 'Daily Change Graph!C5', 'Daily Change Graph!C8']`; cell `COB 082801!D8`

- **q6** (hardcode) Consider the range Breakdown!AJ14:AN14 (the row of 'Power Purchases'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Breakdown!AJ14', 'Breakdown!AK14', 'Breakdown!AL14', 'Breakdown!AN14']`; cell `Breakdown!AJ14`

## rw2_enron_thomas_martin (enron: `thomas_martin__39741__6th floorplan 10.03c.xlsx`)

- **q1** (trace) Consider the cell Floor Plan!I28 (in the row labelled 'Arora'). List the cells its formula reads directly (not indirectly).
  - answer: `['Floor Plan!G28', 'Floor Plan!H28']`; cell `Floor Plan!I28`
  - formula: `=SUM(G28:H28)`

- **q2** (trace) Consider the cell Floor Plan!C84 (in the row labelled 'Total'). List the cells its formula reads directly (not indirectly).
  - answer: `['Floor Plan!C80', 'Floor Plan!C81', 'Floor Plan!C82', 'Floor Plan!C83']`; cell `Floor Plan!C84`
  - formula: `=SUM(C80:C83)`

- **q3** (impact) Suppose the number in Floor Plan!AC94 (in the row labelled 'Forney') were 10% higher. List every other cell whose value would change.
  - answer: `['Floor Plan!AA94', 'Floor Plan!AB94', 'Floor Plan!Y94', 'Floor Plan!Z94']`; cell `Floor Plan!AC94`

- **q4** (hardcode) Consider the range Floor Plan!K68:P68. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Floor Plan!P68']`; cell `Floor Plan!K68`

## rw2_enron_vkaminski (enron: `vkaminski__40703__STORAGE-PRC-27.xlsx`)

- **q1** (lookup) What is the value in the row labelled '2M', column headed 'Risk Metrics', in the sheet 'components'?
  - answer: `1475877.75064424`; cell `components!J2`
  - read: components!I2 = '2M'; components!J1 = 'Risk Metrics'

- **q2** (trace) Consider the cell VOLS!AD12 (in the row labelled 'NG'). List the cells its formula reads directly (not indirectly).
  - answer: `['VOLS!AB11', 'VOLS!AB12', 'VOLS!AC12', 'VOLS!Z11', 'VOLS!Z12']`; cell `VOLS!AD12`
  - formula: `=(((Z12)^2*AB12)-((Z11)^2*AB11))/AC12`

- **q3** (trace) Consider the cell VOLS!W9 (in the row labelled 'NG'). List the cells its formula reads directly (not indirectly).
  - answer: `['VOLS!V7', 'VOLS!V8']`; cell `VOLS!W9`
  - formula: `=V8-V7`

- **q4** (impact) Suppose the number in components!G41 were 10% higher. List every other cell whose value would change.
  - answer: `125 cells, e.g. ['components!H41', 'components!J20', 'covariance!BK43']`; cell `components!G41`

- **q5** (hardcode) Consider the range components!E14:H14. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['components!E14', 'components!F14', 'components!G14']`; cell `components!E14`

