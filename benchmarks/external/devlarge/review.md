# Review record (Tier 2 real-world set)

Every question was made by the rules in `external/realworld2.py` and its answer computed from the file. Each needs two readers, one of them human, before Tier 2 runs: check that the wording names the cell it says and that the answer is right. Mark a bad question here; it is dropped by rule, never rewritten after a model has seen it.

## dev_apv (damodaran: `dam_apv.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Aaa/AAA', column headed 'Interest rate', in the sheet 'Adjusted Present Value'?
  - answer: `0.028`; cell `Adjusted Present Value!G87`
  - read: Adjusted Present Value!F87 = 'Aaa/AAA'; Adjusted Present Value!G71 = 'Interest rate'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Funds/Debt', column headed 'D', in the sheet 'Adjusted Present Value'? Give its cell address.
  - answer: `Adjusted Present Value!C64`; cell `Adjusted Present Value!C64`
  - read: Adjusted Present Value!A64 = 'Funds/Debt'; Adjusted Present Value!C40 = 'D'

- [ ] **q3** (trace) Consider the cell Adjusted Present Value!C50 (in the row labelled 'Beta'). List the cells its formula reads directly (not indirectly).
  - answer: `['Adjusted Present Value!B50', 'Adjusted Present Value!C48', 'Adjusted Present Value!C68']`; cell `Adjusted Present Value!C50`
  - formula: `=$B50*(1+(1-C68)*C48)`

- [ ] **q4** (trace) Consider the cell Adjusted Present Value!H87 (in the row labelled 'Aaa/AAA'). List the cells its formula reads directly (not indirectly).
  - answer: `['Default Spreads and Ratios!E29', 'Default Spreads and Ratios!E49', 'Inputs!B29']`; cell `Adjusted Present Value!H87`
  - formula: `=IF(Inputs!$B$29=1,'Default Spreads and Ratios'!E29,'Default Spreads and Ratios'!E49)`

- [ ] **q5** (impact) Suppose the number in Default Spreads and Ratios!B49 were 10% higher. List every other cell whose value would change.
  - answer: `['Adjusted Present Value!E27', 'Adjusted Present Value!E87']`; cell `Default Spreads and Ratios!B49`

- [ ] **q6** (hardcode) Consider the range Country ERP!C132:F132 (the row of 'Aaa'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Country ERP!C132', 'Country ERP!E132', 'Country ERP!F132']`; cell `Country ERP!C132`

## dev_ddm3st (damodaran: `dam_ddm3st.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Beta', column headed 'Growth Rate', in the sheet 'ddm3st.xls'?
  - answer: `1.1`; cell `ddm3st.xls!D108`
  - read: ddm3st.xls!B108 = 'Beta'; ddm3st.xls!D88 = 'Growth Rate'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Current Earnings per share=', in the sheet 'ddm3st.xls'? Give its cell address.
  - answer: `ddm3st.xls!D85`; cell `ddm3st.xls!D85`
  - read: ddm3st.xls!B85 = 'Current Earnings per share='

- [ ] **q3** (trace) Consider the cell ddm3st.xls!L99 (in the row labelled 'Dividends'). List the cells its formula reads directly (not indirectly).
  - answer: `['ddm3st.xls!D92', 'ddm3st.xls!E33', 'ddm3st.xls!K99', 'ddm3st.xls!L97']`; cell `ddm3st.xls!L99`
  - formula: `=IF($E$33<L97," ",K99*(1+$D$92))`

- [ ] **q4** (trace) Consider the cell ddm3st.xls!E107 (in the row labelled 'Dividends'). List the cells its formula reads directly (not indirectly).
  - answer: `['ddm3st.xls!E105', 'ddm3st.xls!E106', 'ddm3st.xls!E64']`; cell `ddm3st.xls!E107`
  - formula: `=IF($E$64<3," ",E106*E105)`

- [ ] **q5** (impact) Suppose the number in ddm3st.xls!E33 (in the row labelled 'Enter length of extraordinary growth period =') were 10% higher. List every other cell whose value would change.
  - answer: `36 cells, e.g. ['ddm3st.xls!C103', 'ddm3st.xls!C106', 'ddm3st.xls!C107']`; cell `ddm3st.xls!E33`

- [ ] **q6** (hardcode) Consider the range ddm3st.xls!L97:L100. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `ddm3st.xls!L97`

## dev_divginzu (damodaran: `dam_divginzu.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Advertising', column headed 'Unlevered Beta', in the sheet 'US Industry averages'?
  - answer: `1.00800989034213`; cell `US Industry averages!G2`
  - read: US Industry averages!A2 = 'Advertising'; US Industry averages!G1 = 'Unlevered Beta'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Business & Consumer Services', column headed 'Net Cap Ex as % of Revenues', in the sheet 'US Industry averages'? Give its cell address.
  - answer: `US Industry averages!V15`; cell `US Industry averages!V15`
  - read: US Industry averages!A15 = 'Business & Consumer Services'; US Industry averages!V1 = 'Net Cap Ex as % of Revenues'

- [ ] **q3** (trace) Consider the cell Country ERP!D108 (in the row labelled 'Aaa'). List the cells its formula reads directly (not indirectly).
  - answer: `['Country ERP!B1', 'Country ERP!E108']`; cell `Country ERP!D108`
  - formula: `=$B$1+E108`

- [ ] **q4** (trace) Consider the cell Country ERP!D145 (in the row labelled 'A2'). List the cells its formula reads directly (not indirectly).
  - answer: `['Country ERP!B1', 'Country ERP!E145']`; cell `Country ERP!D145`
  - formula: `=$B$1+E145`

- [ ] **q5** (impact) Suppose the number in Country ERP!E209 (in the row labelled 'Western Europe') were 10% higher. List every other cell whose value would change.
  - answer: `75 cells, e.g. ['Country ERP!B209', 'ERP calculator!C26', 'ERP calculator!E26']`; cell `Country ERP!E209`

- [ ] **q6** (hardcode) Consider the range Country ERP!C72:F72 (the row of 'Aaa'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Country ERP!C72', 'Country ERP!E72', 'Country ERP!F72']`; cell `Country ERP!C72`

## dev_dividends (damodaran: `dividends.xls`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Enter dividends paid in the most recent year =', column headed 'Return on market', in the sheet 'Inputs'?
  - answer: `1324`; cell `Inputs!E64`
  - read: Inputs!A64 = 'Enter dividends paid in the most recent year ='; Inputs!E40 = 'Return on market'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Enter non-cash working capital as a percent of revenues', column headed 'Return on market', in the sheet 'Inputs'? Give its cell address.
  - answer: `Inputs!E59`; cell `Inputs!E59`
  - read: Inputs!A59 = 'Enter non-cash working capital as a percent of revenues'; Inputs!E40 = 'Return on market'

- [ ] **q3** (trace) Consider the cell Analysis of past dividends!C23 (in the row labelled 'ROE - Cost of Equity'). List the cells its formula reads directly (not indirectly).
  - answer: `['Analysis of past dividends!C2', 'Analysis of past dividends!C21', 'Analysis of past dividends!C22']`; cell `Analysis of past dividends!C23`
  - formula: `=IF(C2>0,C21-C22," ")`

- [ ] **q4** (trace) Consider the cell Analysis of past dividends!F9 (in the row labelled 'Free CF to Equity (target debt ratio)'). List the cells its formula reads directly (not indirectly).
  - answer: `['Analysis of past dividends!F2', 'Analysis of past dividends!F3', 'Analysis of past dividends!F4', 'Analysis of past dividends!F5', 'Inputs!E3', 'Inputs!E4', 'Inputs!E5']`; cell `Analysis of past dividends!F9`
  - formula: `=IF(F2>0,IF(Inputs!$E$4="Yes",F3-(F4+F5)*(1-Inputs!$E$5),F3-(F4+F5)*(1-Inputs!$E$3)),0)`

- [ ] **q5** (impact) Suppose the number in Inputs!D13 were 10% higher. List every other cell whose value would change.
  - answer: `18 cells, e.g. ['Analysis of past dividends!B38', 'Analysis of past dividends!B39', 'Analysis of past dividends!B40']`; cell `Inputs!D13`

- [ ] **q6** (hardcode) Consider the range Inputs!F9:F18 (the column of 'Net Debt Issued'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Inputs!F12']`; cell `Inputs!F9`

## dev_fcfe3st (damodaran: `dam_fcfe3st.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Growth Rate', column headed 'Earnings g', in the sheet 'NewFCFE3Stage'?
  - answer: `0.17`; cell `NewFCFE3Stage!E144`
  - read: NewFCFE3Stage!B144 = 'Growth Rate'; NewFCFE3Stage!E130 = 'Earnings g'

- [ ] **q2** (address) Which cell holds the value in the row labelled '(CapEx-Depreciation)*(1-DR)', column headed 'Terminal Year', in the sheet 'NewFCFE3Stage'? Give its cell address.
  - answer: `NewFCFE3Stage!N147`; cell `NewFCFE3Stage!N147`
  - read: NewFCFE3Stage!B147 = '(CapEx-Depreciation)*(1-DR)'; NewFCFE3Stage!N143 = 'Terminal Year'

- [ ] **q3** (trace) Consider the cell NewFCFE3Stage!K150 (in the row labelled 'Beta'). List the cells its formula reads directly (not indirectly).
  - answer: `['NewFCFE3Stage!D34', 'NewFCFE3Stage!D35', 'NewFCFE3Stage!D36', 'NewFCFE3Stage!E157', 'NewFCFE3Stage!E73', 'NewFCFE3Stage!F75', 'NewFCFE3Stage!F76', 'NewFCFE3Stage!J150']`; cell `NewFCFE3Stage!K150`
  - formula: `=IF($E$73<8," ",(IF($F$75="Yes",J150-($D$34-($E$157-$D$35)/$D$36)/$E$73,$F$76)))`

- [ ] **q4** (trace) Consider the cell NewFCFE3Stage!F128 (in the row labelled 'Earnings g'). List the cells its formula reads directly (not indirectly).
  - answer: `['NewFCFE3Stage!C90', 'NewFCFE3Stage!E155', 'NewFCFE3Stage!F85']`; cell `NewFCFE3Stage!F128`
  - formula: `=IF(F85="Yes",E155,C90)`

- [ ] **q5** (impact) Suppose the number in NewFCFE3Stage!E69 (in the row labelled 'Outside Prediction of Growth =') were 10% higher. List every other cell whose value would change.
  - answer: `109 cells, e.g. ['NewFCFE3Stage!D124', 'NewFCFE3Stage!D128', 'NewFCFE3Stage!D129']`; cell `NewFCFE3Stage!E69`

- [ ] **q6** (hardcode) Consider the range NewFCFE3Stage!D23:D29. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['NewFCFE3Stage!D23', 'NewFCFE3Stage!D24', 'NewFCFE3Stage!D25', 'NewFCFE3Stage!D26', 'NewFCFE3Stage!D27', 'NewFCFE3Stage!D29']`; cell `NewFCFE3Stage!D23`

## dev_fcfeginzu (damodaran: `fcfeginzu.xls`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Computer Services', column headed 'Equity Reinvestment Rate', in the sheet 'Global Industry averages'?
  - answer: `0.530889362771159`; cell `Global Industry averages!Z21`
  - read: Global Industry averages!A21 = 'Computer Services'; Global Industry averages!Z1 = 'Equity Reinvestment Rate'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Air Transport', column headed 'Sales/Capital', in the sheet 'Global Industry averages'? Give its cell address.
  - answer: `Global Industry averages!N4`; cell `Global Industry averages!N4`
  - read: Global Industry averages!A4 = 'Air Transport'; Global Industry averages!N1 = 'Sales/Capital'

- [ ] **q3** (trace) Consider the cell Country ERP!D111 (in the row labelled 'NR'). List the cells its formula reads directly (not indirectly).
  - answer: `['Country ERP!B1', 'Country ERP!E111']`; cell `Country ERP!D111`
  - formula: `=$B$1+E111`

- [ ] **q4** (trace) Consider the cell Beta calculator!D10. List the cells its formula reads directly (not indirectly).
  - answer: `['Beta calculator!B10', 'Beta calculator!C10']`; cell `Beta calculator!D10`
  - formula: `=B10*C10`

- [ ] **q5** (impact) Suppose the number in R&D converter!B11 were 10% higher. List every other cell whose value would change.
  - answer: `['R&D converter!B25', 'R&D converter!D25', 'R&D converter!D35', 'R&D converter!D37', 'R&D converter!D39', 'R&D converter!E25', 'R&D converter!E35']`; cell `R&D converter!B11`

- [ ] **q6** (hardcode) Consider the range Country ERP!B216:E216 (the row of 'Latin America & Caribbean'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Country ERP!C216', 'Country ERP!D216']`; cell `Country ERP!B216`

## dev_fcffginzulambda (damodaran: `dam_fcffginzulambda.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Tax Rate for computing income=', column headed 'Forever', in the sheet 'Valuation Model'?
  - answer: `0.275`; cell `Valuation Model!E26`
  - read: Valuation Model!B26 = 'Tax Rate for computing income='; Valuation Model!E17 = 'Forever'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Electric Utility (East)', in the sheet 'R&D converter'? Give its cell address.
  - answer: `R&D converter!B75`; cell `R&D converter!B75`
  - read: R&D converter!A75 = 'Electric Utility (East)'

- [ ] **q3** (trace) Consider the cell Historical Numbers!D13 (in the row labelled 'Reinvestment Rate'). List the cells its formula reads directly (not indirectly).
  - answer: `['Historical Numbers!D12', 'Historical Numbers!D2']`; cell `Historical Numbers!D13`
  - formula: `=D12/D2`

- [ ] **q4** (trace) Consider the cell Cross Holdings Valuation!C9 (in the row labelled 'Hyundai Samho'). List the cells its formula reads directly (not indirectly).
  - answer: `['Cross Holdings Valuation!B9', 'Cross Holdings Valuation!D9']`; cell `Cross Holdings Valuation!C9`
  - formula: `=D9/B9`

- [ ] **q5** (impact) Suppose the number in Earnings Normalizer!C26 (in the row labelled 'Inventory') were 10% higher. List every other cell whose value would change.
  - answer: `['Earnings Normalizer!B33', 'Earnings Normalizer!B35', 'Earnings Normalizer!C24', 'Earnings Normalizer!G24']`; cell `Earnings Normalizer!C26`

- [ ] **q6** (hardcode) Consider the range Terminal Value!C11:C16 (the column of 'Reinvestment Rate'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Terminal Value!C11']`; cell `Terminal Value!C11`

## dev_fcffneg (damodaran: `dam_fcffneg.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'EBITDA', column headed 'Terminal Year', in the sheet 'Valuation'?
  - answer: `4095.99512316295`; cell `Valuation!M101`
  - read: Valuation!B101 = 'EBITDA'; Valuation!M98 = 'Terminal Year'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Term. Year', column headed 'EBIT', in the sheet 'Summary'? Give its cell address.
  - answer: `Summary!E12`; cell `Summary!E12`
  - read: Summary!A12 = 'Term. Year'; Summary!E1 = 'EBIT'

- [ ] **q3** (trace) Consider the cell Valuation!G102 (in the row labelled '- Depreciation'). List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation!E46', 'Valuation!F102', 'Valuation!F66', 'Valuation!G98']`; cell `Valuation!G102`
  - formula: `=IF($E$46<G98,0,F102*(1+$F66))`

- [ ] **q4** (trace) Consider the cell Valuation!L107 (in the row labelled '- Capital Spending'). List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation!E46', 'Valuation!E71', 'Valuation!K107', 'Valuation!L98']`; cell `Valuation!L107`
  - formula: `=IF($E$46<L98,0,K107*(1+$E71))`

- [ ] **q5** (impact) Suppose the number in Valuation!C65 were 10% higher. List every other cell whose value would change.
  - answer: `145 cells, e.g. ['Summary!B10', 'Summary!B11', 'Summary!B12']`; cell `Valuation!C65`

- [ ] **q6** (hardcode) Consider the range Valuation!D62:D71 (the column of 'EBITDA/Revenue'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Valuation!D62', 'Valuation!D63', 'Valuation!D64', 'Valuation!D65', 'Valuation!D66']`; cell `Valuation!D62`

## dev_histretsp (damodaran: `dam_histretSP.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled '75th percentile', column headed 'Stocks', in the sheet 'Nominal vs Real Data'?
  - answer: `0.2597`; cell `Nominal vs Real Data!P11`
  - read: Nominal vs Real Data!O11 = '75th percentile'; Nominal vs Real Data!P1 = 'Stocks'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'S&P 500 minus Lowest Decile', column headed '3-month T. Bill (Real)', in the sheet 'Returns by year'? Give its cell address.
  - answer: `Returns by year!X126`; cell `Returns by year!X126`
  - read: Returns by year!Q126 = 'S&P 500 minus Lowest Decile'; Returns by year!X121 = '3-month T. Bill (Real)'

- [ ] **q3** (trace) Consider the cell Returns by year!K101. List the cells its formula reads directly (not indirectly).
  - answer: `['Returns by year!D101', 'Returns by year!K100']`; cell `Returns by year!K101`
  - formula: `=K100*(1+D101)`

- [ ] **q4** (trace) Consider the cell Returns by year!AH36. List the cells its formula reads directly (not indirectly).
  - answer: `['Returns by year!AA36', 'Returns by year!AH35']`; cell `Returns by year!AH36`
  - formula: `=AH35*(1+AA36)`

- [ ] **q5** (impact) Suppose the number in Nominal vs Real Data!F39 were 10% higher. List every other cell whose value would change.
  - answer: `61 cells, e.g. ['Nominal vs Real Data!K39', 'Nominal vs Real Data!K40', 'Nominal vs Real Data!K41']`; cell `Nominal vs Real Data!F39`

- [ ] **q6** (hardcode) Consider the range Nominal vs Real Data!A13:K13. List the cells that hold typed-in numbers rather than formulas.
  - answer: `9 cells, e.g. ['Nominal vs Real Data!A13', 'Nominal vs Real Data!B13', 'Nominal vs Real Data!C13']`; cell `Nominal vs Real Data!A13`

## dev_riskchecker (damodaran: `dam_riskchecker.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Euro', column headed 'Average riskfree rate - last 2 years', in the sheet 'Past T.Bill rates'?
  - answer: `0.0025`; cell `Past T.Bill rates!B3`
  - read: Past T.Bill rates!A3 = 'Euro'; Past T.Bill rates!B1 = 'Average riskfree rate - last 2 years'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Grand Total', column headed 'Default Spread (Weighted average)', in the sheet 'Regional Risk Premiums'? Give its cell address.
  - answer: `Regional Risk Premiums!B12`; cell `Regional Risk Premiums!B12`
  - read: Regional Risk Premiums!A12 = 'Grand Total'; Regional Risk Premiums!B1 = 'Default Spread (Weighted average)'

- [ ] **q3** (trace) Consider the cell ERP calculator!D9 (in the row labelled 'Chile'). List the cells its formula reads directly (not indirectly).
  - answer: `['ERP calculator!B17', 'ERP calculator!B9']`; cell `ERP calculator!D9`
  - formula: `=B9/$B$17`

- [ ] **q4** (trace) Consider the cell ERP calculator!D32 (in the row labelled 'North America'). List the cells its formula reads directly (not indirectly).
  - answer: `['ERP calculator!B32', 'ERP calculator!B34']`; cell `ERP calculator!D32`
  - formula: `=B32/$B$34`

- [ ] **q5** (impact) Suppose the number in Check numbers!B8 (in the row labelled 'Past Riskfree rate (Annual)') were 10% higher. List every other cell whose value would change.
  - answer: `['Check numbers!B11', 'Check numbers!B12', 'Check numbers!B13']`; cell `Check numbers!B8`

- [ ] **q6** (hardcode) Consider the range ERP calculator!B8:E8 (the row of 'Brazil'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['ERP calculator!B8']`; cell `ERP calculator!B8`

