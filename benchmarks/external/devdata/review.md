# Review record (Tier 2 real-world set)

Every question was made by the rules in `external/realworld2.py` and its answer computed from the file. Each needs two readers, one of them human, before Tier 2 runs: check that the wording names the cell it says and that the answer is right. Mark a bad question here; it is dropped by rule, never rewritten after a model has seen it.

## dev_d_20001_05_flash_report_62601 (enron: `stacey_white__38830__20001 05 flash Report 62601 .xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Offsets 2001 04 acctg variance.', in the sheet 'Var. Rpt EPMI'?
  - answer: `-42000`; cell `Var. Rpt EPMI!J431`
  - read: Var. Rpt EPMI!E431 = 'Offsets 2001 04 acctg variance.'

- [ ] **q2** (address) Which cell holds the value in the row labelled '605393.1 and 605550.1 both deals PMA's not flashed, pulled through Unify', in the sheet 'Var. Rpt EPMI'? Give its cell address.
  - answer: `Var. Rpt EPMI!J88`; cell `Var. Rpt EPMI!J88`
  - read: Var. Rpt EPMI!E88 = "605393.1 and 605550.1 both deals PMA's not flashed, pulled t"

- [ ] **q3** (trace) Consider the cell Var. Rpt EPMI!K41 (in the row labelled 'Financial Liquidations'). List the cells its formula reads directly (not indirectly).
  - answer: `['Var. Rpt EPMI!E41', 'Var. Rpt EPMI!H41']`; cell `Var. Rpt EPMI!K41`
  - formula: `=H41-E41`

- [ ] **q4** (trace) Consider the cell Var. Rpt EPMI!K45 (in the row labelled 'OTC & EXCHG - PV'). List the cells its formula reads directly (not indirectly).
  - answer: `['Var. Rpt EPMI!E45', 'Var. Rpt EPMI!H45']`; cell `Var. Rpt EPMI!K45`
  - formula: `=H45-E45`

- [ ] **q5** (impact) Suppose the number in Var. Rpt EPMI!J113 (in the row labelled '566035.1 - Vol adjustments to 10 MIN Spinning Reserves. Index settled for April ') were 10% higher. List every other cell whose value would change.
  - answer: `['Var. Rpt EPMI!K141', 'Var. Rpt EPMI!K733']`; cell `Var. Rpt EPMI!J113`

- [ ] **q6** (hardcode) Consider the range reconciliation!D11:I11 (the row of 'Russ's file'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['reconciliation!D11', 'reconciliation!F11', 'reconciliation!G11']`; cell `reconciliation!D11`

## dev_d_aga_storage (enron: `joe_parks__14611__AGA_STORAGE.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Mar', column headed 'Week', in the sheet 'CONSUMING EAST'?
  - answer: `10`; cell `CONSUMING EAST!B11`
  - read: CONSUMING EAST!A11 = 'Mar'; CONSUMING EAST!B1 = 'Week'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Jan', column headed 'Week', in the sheet 'CONSUMING EAST'? Give its cell address.
  - answer: `CONSUMING EAST!B2`; cell `CONSUMING EAST!B2`
  - read: CONSUMING EAST!A2 = 'Jan'; CONSUMING EAST!B1 = 'Week'

- [ ] **q3** (trace) Consider the cell PRODUCING!V44. List the cells its formula reads directly (not indirectly).
  - answer: `['PRODUCING!K43', 'PRODUCING!K44']`; cell `PRODUCING!V44`
  - formula: `=K44-K43`

- [ ] **q4** (trace) Consider the cell WEST!V26. List the cells its formula reads directly (not indirectly).
  - answer: `['WEST!K25', 'WEST!K26']`; cell `WEST!V26`
  - formula: `=K26-K25`

- [ ] **q5** (impact) Suppose the number in WEST!K37 (in the row labelled 'Sep') were 10% higher. List every other cell whose value would change.
  - answer: `['WEST!V37', 'WEST!V38']`; cell `WEST!K37`

- [ ] **q6** (hardcode) Consider the range CONSUMING EAST!O25:V25. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['CONSUMING EAST!O25', 'CONSUMING EAST!P25', 'CONSUMING EAST!Q25', 'CONSUMING EAST!R25', 'CONSUMING EAST!S25', 'CONSUMING EAST!T25', 'CONSUMING EAST!U25']`; cell `CONSUMING EAST!O25`

## dev_d_corpcontr_00_analysis (enron: `richard_shapiro__32164__CorpContr'00 analysis.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Key Dist', column headed '% of Total Contrib', in the sheet 'Breakouts'?
  - answer: `0.05369`; cell `Breakouts!E19`
  - read: Breakouts!B19 = 'Key Dist'; Breakouts!E7 = '% of Total Contrib'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Key Dist', column headed '# of Contribs', in the sheet 'Breakouts'? Give its cell address.
  - answer: `Breakouts!C19`; cell `Breakouts!C19`
  - read: Breakouts!B19 = 'Key Dist'; Breakouts!C7 = '# of Contribs'

- [ ] **q3** (trace) Consider the cell CorpContr_00!K158 (in the row labelled 'Unassigned Total'). List the cells its formula reads directly (not indirectly).
  - answer: `['CorpContr_00!K151', 'CorpContr_00!K152', 'CorpContr_00!K153']`; cell `CorpContr_00!K158`
  - formula: `=SUM(K151:K153)`

- [ ] **q4** (trace) Consider the cell CorpContr_00!K157 (in the row labelled 'Sub.'). List the cells its formula reads directly (not indirectly).
  - answer: `['CorpContr_00!K155', 'CorpContr_00!K156']`; cell `CorpContr_00!K157`
  - formula: `=SUM(K156,K155)`

- [ ] **q5** (impact) Suppose the number in CorpContr_00!K78 (in the row labelled 'Tim Aron') were 10% higher. List every other cell whose value would change.
  - answer: `['CorpContr_00!K156', 'CorpContr_00!K157', 'CorpContr_00!K159']`; cell `CorpContr_00!K78`

- [ ] **q6** (hardcode) Consider the range CorpContr_00!K155:K159. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `CorpContr_00!K155`

## dev_d_eol_customers (enron: `hunter_shively__12726__EOL Customers.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Bruno, Marshall, Stevens', in the sheet 'Lists'?
  - answer: `3`; cell `Lists!I110`
  - read: Lists!H110 = 'Bruno, Marshall, Stevens'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'TECO', in the sheet 'Lists'? Give its cell address.
  - answer: `Lists!F142`; cell `Lists!F142`
  - read: Lists!E142 = 'TECO'

- [ ] **q3** (trace) Consider the cell All Customers by Region!K386 (in the row labelled 'Bellweather'). List the cells its formula reads directly (not indirectly).
  - answer: `['All Customers by Region!E386', 'All Customers by Region!F386', 'All Customers by Region!G386', 'All Customers by Region!H386', 'All Customers by Region!I386', 'All Customers by Region!J386']`; cell `All Customers by Region!K386`
  - formula: `=COUNT(E386:J386)`

- [ ] **q4** (trace) Consider the cell All Customers by Region!K326 (in the row labelled 'PHILLIPS PETROLEUM COMPANY'). List the cells its formula reads directly (not indirectly).
  - answer: `['All Customers by Region!E326', 'All Customers by Region!F326', 'All Customers by Region!G326', 'All Customers by Region!H326', 'All Customers by Region!I326', 'All Customers by Region!J326']`; cell `All Customers by Region!K326`
  - formula: `=COUNT(E326:J326)`

- [ ] **q5** (impact) Suppose the number in Lists!C102 (in the row labelled 'Alberta Energy Corp') were 10% higher. List every other cell whose value would change.
  - answer: `['All Customers by Region!F253', 'All Customers by Region!F4', 'All Customers by Region!F5', 'Lists!C2', 'Lists!C5']`; cell `Lists!C102`

- [ ] **q6** (hardcode) Consider the range All Customers by Region!E32:P32 (the row of 'X'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['All Customers by Region!L32', 'All Customers by Region!M32', 'All Customers by Region!N32', 'All Customers by Region!O32', 'All Customers by Region!P32']`; cell `All Customers by Region!E32`

## dev_d_epe_may_2001 (enron: `geir_solberg__11249__EPE_MAY_2001.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Time', column headed 'FROM WESCO', in the sheet 'MAY(5)'?
  - answer: `310`; cell `MAY(5)!M7`
  - read: MAY(5)!B7 = 'Time'; MAY(5)!M6 = 'FROM WESCO'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Time', column headed 'FROM AEP', in the sheet 'MAY(3)'? Give its cell address.
  - answer: `MAY(3)!L7`; cell `MAY(3)!L7`
  - read: MAY(3)!B7 = 'Time'; MAY(3)!L6 = 'FROM AEP'

- [ ] **q3** (trace) Consider the cell MAY(13)!J39 (in the row labelled 'PDT TOTAL'). List the cells its formula reads directly (not indirectly).
  - answer: `['MAY(13)!C39', 'MAY(13)!D39', 'MAY(13)!E39', 'MAY(13)!F39', 'MAY(13)!G39', 'MAY(13)!H39', 'MAY(13)!I39']`; cell `MAY(13)!J39`
  - formula: `=SUM(C39:I39)`

- [ ] **q4** (trace) Consider the cell MAY(6)!J17. List the cells its formula reads directly (not indirectly).
  - answer: `['MAY(6)!C17', 'MAY(6)!D17', 'MAY(6)!E17', 'MAY(6)!F17', 'MAY(6)!G17', 'MAY(6)!H17', 'MAY(6)!I17']`; cell `MAY(6)!J17`
  - formula: `=SUM(C17:I17)`

- [ ] **q5** (impact) Suppose the number in MAY(9)!H29 were 10% higher. List every other cell whose value would change.
  - answer: `['MAY(9)!H37', 'MAY(9)!H39', 'MAY(9)!V29', 'MAY(9)!V37', 'MAY(9)!V39']`; cell `MAY(9)!H29`

- [ ] **q6** (hardcode) Consider the range MAY(8)!A26:T26. List the cells that hold typed-in numbers rather than formulas.
  - answer: `19 cells, e.g. ['MAY(8)!A26', 'MAY(8)!B26', 'MAY(8)!C26']`; cell `MAY(8)!A26`

## dev_d_homework_set_one (enron: `jeffrey_a_shankman__13990__Homework set one.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'A.2.', column headed 'Loan Amount', in the sheet 'Sheet1'?
  - answer: `18978.632509184445`; cell `Sheet1!H2`
  - read: Sheet1!F2 = 'A.2.'; Sheet1!H1 = 'Loan Amount'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Part A', in the sheet 'Sheet1'? Give its cell address.
  - answer: `Sheet1!G1`; cell `Sheet1!G1`
  - read: Sheet1!F1 = 'Part A'

- [ ] **q3** (trace) Consider the cell Sheet1!K50. List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!I50', 'Sheet1!K49']`; cell `Sheet1!K50`
  - formula: `=K49-I50`

- [ ] **q4** (trace) Consider the cell Sheet1!K12. List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!I12', 'Sheet1!K11']`; cell `Sheet1!K12`
  - formula: `=K11-I12`

- [ ] **q5** (impact) Suppose the number in Sheet1!A6 were 10% higher. List every other cell whose value would change.
  - answer: `119 cells, e.g. ['Sheet1!A10', 'Sheet1!A100', 'Sheet1!A101']`; cell `Sheet1!A6`

- [ ] **q6** (hardcode) Consider the range Sheet1!G6:K6. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Sheet1!G6']`; cell `Sheet1!G6`

## dev_d_pgtfuel (enron: `barry_tycholiz__882__PGTfuel.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'column', column headed 'calc', in the sheet 'filings'?
  - answer: `476.293808675396`; cell `filings!Y2`
  - read: filings!B2 = 'column'; filings!Y1 = 'calc'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'slope', column headed 'sum(y^2)', in the sheet 'regr'? Give its cell address.
  - answer: `regr!D108`; cell `regr!D108`
  - read: regr!B108 = 'slope'; regr!D105 = 'sum(y^2)'

- [ ] **q3** (trace) Consider the cell daily!D87. List the cells its formula reads directly (not indirectly).
  - answer: `['daily!A87', 'filings!D87']`; cell `daily!D87`
  - formula: `=filings!$D87/daily!$A87`

- [ ] **q4** (trace) Consider the cell daily!Q46. List the cells its formula reads directly (not indirectly).
  - answer: `['daily!A46', 'filings!R46']`; cell `daily!Q46`
  - formula: `=filings!R46/daily!$A46`

- [ ] **q5** (impact) Suppose the number in filings!C42 were 10% higher. List every other cell whose value would change.
  - answer: `11 cells, e.g. ['daily!C42', 'daily!J42', 'daily!K42']`; cell `filings!C42`

- [ ] **q6** (hardcode) Consider the range filings!AK98:AZ98 (the row of '#N/A'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['filings!AN98', 'filings!AO98']`; cell `filings!AK98`

## dev_d_rpt_pma_log_gas_three_rm (enron: `jason_wolfe__13350__Rpt PMA Log Gas Three RM.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Broker Fees: $18,338 on g/l for Dec00 vs $17,118 in risk p&l', column headed 'Risk', in the sheet 'JAN'?
  - answer: `-1220`; cell `JAN!F20`
  - read: JAN!E20 = 'Broker Fees: $18,338 on g/l for Dec00 vs $17,118 in risk p&l'; JAN!F4 = 'Risk'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Book Admin: Bruce Mills', column headed 'Risk', in the sheet 'JAN'? Give its cell address.
  - answer: `JAN!F25`; cell `JAN!F25`
  - read: JAN!E25 = 'Book Admin:  Bruce Mills'; JAN!F4 = 'Risk'

- [ ] **q3** (trace) Consider the cell MGWST AUG00!K5 (in the row labelled 'BASIS SWAP'). List the cells its formula reads directly (not indirectly).
  - answer: `['MGWST AUG00!D5', 'MGWST AUG00!J5']`; cell `MGWST AUG00!K5`
  - formula: `=D5-J5`

- [ ] **q4** (trace) Consider the cell MGWST AUG00!K16 (in the row labelled 'BASIS SWAP'). List the cells its formula reads directly (not indirectly).
  - answer: `['MGWST AUG00!D16', 'MGWST AUG00!J16']`; cell `MGWST AUG00!K16`
  - formula: `=D16-J16`

- [ ] **q5** (impact) Suppose the number in MGWST AUG00!F11 (in the row labelled 'BASIS SWAP') were 10% higher. List every other cell whose value would change.
  - answer: `['MGWST AUG00!F46', 'MGWST AUG00!J11', 'MGWST AUG00!J46', 'MGWST AUG00!K11', 'MGWST AUG00!K46']`; cell `MGWST AUG00!F11`

- [ ] **q6** (hardcode) Consider the range JAN!F15:F18 (the column of 'Risk'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['JAN!F15', 'JAN!F16', 'JAN!F17']`; cell `JAN!F15`

## dev_d_scores99 (enron: `jeff_dasovich__14092__Scores99.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'T 5', column headed 'Min', in the sheet 'Week #3'?
  - answer: `10`; cell `Week #3!AD13`
  - read: Week #3!C13 = 'T  5'; Week #3!AD5 = 'Min'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Donna*', column headed 'New Total', in the sheet 'Week #3'? Give its cell address.
  - answer: `Week #3!F9`; cell `Week #3!F9`
  - read: Week #3!B9 = 'Donna*'; Week #3!F5 = 'New Total'

- [ ] **q3** (trace) Consider the cell Week #5!F11 (in the row labelled 'T 4'). List the cells its formula reads directly (not indirectly).
  - answer: `['Week #5!E11', 'Week #5!G11']`; cell `Week #5!F11`
  - formula: `=G11+E11`

- [ ] **q4** (trace) Consider the cell Week #5!F17 (in the row labelled 'T18'). List the cells its formula reads directly (not indirectly).
  - answer: `['Week #5!E17', 'Week #5!G17']`; cell `Week #5!F17`
  - formula: `=G17+E17`

- [ ] **q5** (impact) Suppose the number in Week #4!AF11 (in the row labelled 'T 4') were 10% higher. List every other cell whose value would change.
  - answer: `['Week #4!AF27', 'Week #4!AF28', 'Week #4!AL11']`; cell `Week #4!AF11`

- [ ] **q6** (hardcode) Consider the range Total!E15:I15 (the row of 'T 11'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Total!F15', 'Total!G15', 'Total!H15', 'Total!I15']`; cell `Total!E15`

## dev_d_txrrc_stg (enron: `jim_schwieger__14385__TXRRC_STG.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Palo Pinto', column headed 'RRC 1/31/00', in the sheet 'History By Facility'?
  - answer: `325`; cell `History By Facility!G135`
  - read: History By Facility!D135 = 'Palo Pinto'; History By Facility!G118 = 'RRC 1/31/00'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Wharton', column headed 'RRC 3/31/01', in the sheet 'History By Facility'? Give its cell address.
  - answer: `History By Facility!K256`; cell `History By Facility!K256`
  - read: History By Facility!D256 = 'Wharton'; History By Facility!K249 = 'RRC 3/31/01'

- [ ] **q3** (trace) Consider the cell History By Facility!T217 (in the row labelled 'Salt Domes'). List the cells its formula reads directly (not indirectly).
  - answer: `12 cells, e.g. ['History By Facility!T205', 'History By Facility!T206', 'History By Facility!T207']`; cell `History By Facility!T217`
  - formula: `=SUM(T205:T216)`

- [ ] **q4** (trace) Consider the cell Sheet1!N14 (in the row labelled 'Denton'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!K14', 'Sheet1!M14']`; cell `Sheet1!N14`
  - formula: `=M14+K14`

- [ ] **q5** (impact) Suppose the number in History By Facility!I241 (in the row labelled 'Wharton') were 10% higher. List every other cell whose value would change.
  - answer: `['History By Facility!AE241', 'History By Facility!AE247', 'History By Facility!I247']`; cell `History By Facility!I241`

- [ ] **q6** (hardcode) Consider the range History By Facility!E89:E112 (the column of 'WORKING TOP GAS'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `23 cells, e.g. ['History By Facility!E100', 'History By Facility!E101', 'History By Facility!E102']`; cell `History By Facility!E89`

