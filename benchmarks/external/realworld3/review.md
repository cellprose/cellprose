# Review record (Tier 2 real-world set)

Every question was made by the rules in `external/realworld2.py` and its answer computed from the file. Each needs two readers, one of them human, before Tier 2 runs: check that the wording names the cell it says and that the answer is right. Mark a bad question here; it is dropped by rule, never rewritten after a model has seen it.

## rw3_enron_andrea_ring (enron: `andrea_ring__7__IFERCJan.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'TRANSCO 45', column headed 'Volume', in the sheet 'February 2000'?
  - answer: `5`; cell `February 2000!C43`
  - read: February 2000!A43 = 'TRANSCO 45'; February 2000!C41 = 'Volume'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'TRANSCO 65', column headed 'Price', in the sheet 'February 2000'? Give its cell address.
  - answer: `February 2000!B22`; cell `February 2000!B22`
  - read: February 2000!A22 = 'TRANSCO 65'; February 2000!B20 = 'Price'

- [ ] **q3** (trace) Consider the cell February 2000!D26. List the cells its formula reads directly (not indirectly).
  - answer: `['February 2000!C26', 'February 2000!C40']`; cell `February 2000!D26`
  - formula: `=C26/$C$40`

- [ ] **q4** (trace) Consider the cell February 2000!D52. List the cells its formula reads directly (not indirectly).
  - answer: `['February 2000!C52', 'February 2000!C55']`; cell `February 2000!D52`
  - formula: `=C52/$C$55`

- [ ] **q5** (impact) Suppose the number in February 2000!C30 were 10% higher. List every other cell whose value would change.
  - answer: `38 cells, e.g. ['February 2000!C40', 'February 2000!D22', 'February 2000!D23']`; cell `February 2000!C30`

- [ ] **q6** (hardcode) Consider the range February 2000!B61:E61. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['February 2000!B61', 'February 2000!C61']`; cell `February 2000!B61`

## rw3_enron_craig_dean (enron: `craig_dean__4356__11-9act.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'PV Unit 1', column headed 'Difference:', in the sheet 'Preschedule'?
  - answer: `171`; cell `Preschedule!Y95`
  - read: Preschedule!A95 = 'PV Unit 1'; Preschedule!Y88 = 'Difference:'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'GT 1', column headed 'Capacity', in the sheet 'Preschedule'? Give its cell address.
  - answer: `Preschedule!Z44`; cell `Preschedule!Z44`
  - read: Preschedule!A44 = 'GT 1'; Preschedule!Z40 = 'Capacity'

- [ ] **q3** (trace) Consider the cell Economics!F32 (in the row labelled 'PV Unit 3'). List the cells its formula reads directly (not indirectly).
  - answer: `['Economics!H32', 'Economics!I32']`; cell `Economics!F32`
  - formula: `=H32*I32`

- [ ] **q4** (trace) Consider the cell Balancing!H26. List the cells its formula reads directly (not indirectly).
  - answer: `['Balancing!F26', 'Balancing!G26']`; cell `Balancing!H26`
  - formula: `=G26*F26`

- [ ] **q5** (impact) Suppose the number in Deals!L73 (in the row labelled '4C') were 10% higher. List every other cell whose value would change.
  - answer: `['Economics!B17', 'Preschedule!H25']`; cell `Deals!L73`

- [ ] **q6** (hardcode) Consider the range Preschedule!Q94:Q115 (the column of '#REF!'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Preschedule!Q102', 'Preschedule!Q106', 'Preschedule!Q111', 'Preschedule!Q96', 'Preschedule!Q99']`; cell `Preschedule!Q94`

## rw3_enron_danny_mccarty (enron: `danny_mccarty__4661__XTRANSCO - Economics.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Idling : Hours', column headed 'Maximum', in the sheet 'Basic Calculations'?
  - answer: `0.4444444444444444`; cell `Basic Calculations!C6`
  - read: Basic Calculations!B6 = 'Idling : Hours'; Basic Calculations!C1 = 'Maximum'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Gross Idling capacity utlization', column headed 'Minimum', in the sheet 'Capacity'? Give its cell address.
  - answer: `Capacity!E22`; cell `Capacity!E22`
  - read: Capacity!A22 = 'Gross Idling capacity utlization'; Capacity!E1 = 'Minimum'

- [ ] **q3** (trace) Consider the cell Revenue!E3 (in the row labelled 'Number'). List the cells its formula reads directly (not indirectly).
  - answer: `['Revenue!C3', 'Revenue!D3']`; cell `Revenue!E3`
  - formula: `=D3*(1-$C$3)`

- [ ] **q4** (trace) Consider the cell CF!I59 (in the row labelled 'Marginal contribution'). List the cells its formula reads directly (not indirectly).
  - answer: `['CF!I3', 'CF!I7']`; cell `CF!I59`
  - formula: `=I7/I$3`

- [ ] **q5** (impact) Suppose the number in Revenue!D14 (in the row labelled 'Units') were 10% higher. List every other cell whose value would change.
  - answer: `47 cells, e.g. ['Costs!E19', 'Costs!F19', 'Costs!G19']`; cell `Revenue!D14`

- [ ] **q6** (hardcode) Consider the range Costs!M47:M55. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Costs!M53']`; cell `Costs!M47`

## rw3_enron_david_delainey (enron: `david_delainey__8089__2000group expenses.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Energy Operations', column headed 'ENA', in the sheet 'Sheet1'?
  - answer: `38.9`; cell `Sheet1!T8`
  - read: Sheet1!N8 = 'Energy Operations'; Sheet1!T7 = 'ENA'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'TOTAL', column headed 'Savings', in the sheet 'Sheet1'? Give its cell address.
  - answer: `Sheet1!S19`; cell `Sheet1!S19`
  - read: Sheet1!O19 = 'TOTAL'; Sheet1!S7 = 'Savings'

- [ ] **q3** (trace) Consider the cell Sheet1!U13 (in the row labelled 'Transaction Support'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!R13', 'Sheet1!S13']`; cell `Sheet1!U13`
  - formula: `=+S13/R13`

- [ ] **q4** (trace) Consider the cell Sheet1!E10. List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!C10', 'Sheet1!D10']`; cell `Sheet1!E10`
  - formula: `=+D10/C10`

- [ ] **q5** (impact) Suppose the number in Sheet1!C24 were 10% higher. List every other cell whose value would change.
  - answer: `['Sheet1!E24', 'Sheet1!R19', 'Sheet1!R9', 'Sheet1!T19', 'Sheet1!T9', 'Sheet1!U19', 'Sheet1!U9']`; cell `Sheet1!C24`

- [ ] **q6** (hardcode) Consider the range Sheet1!B108:E108. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Sheet1!B108', 'Sheet1!C108', 'Sheet1!D108']`; cell `Sheet1!B108`

## rw3_enron_errol_mclaughlin_jr (enron: `errol_mclaughlin_jr__10270__Access Trades.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'F1', column headed 'NET', in the sheet 'Transfer'?
  - answer: `-40`; cell `Transfer!F5`
  - read: Transfer!B5 = 'F1'; Transfer!F3 = 'NET'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Price', column headed 'TOTAL LONG', in the sheet 'Access Trades'? Give its cell address.
  - answer: `Access Trades!G9`; cell `Access Trades!G9`
  - read: Access Trades!E9 = 'Price'; Access Trades!G8 = 'TOTAL LONG'

- [ ] **q3** (trace) Consider the cell Transfer!F15 (in the row labelled 'X1'). List the cells its formula reads directly (not indirectly).
  - answer: `['Transfer!C15', 'Transfer!D15']`; cell `Transfer!F15`
  - formula: `=C15-D15`

- [ ] **q4** (trace) Consider the cell Transfer!F12 (in the row labelled 'Q1'). List the cells its formula reads directly (not indirectly).
  - answer: `['Transfer!C12', 'Transfer!D12']`; cell `Transfer!F12`
  - formula: `=C12-D12`

- [ ] **q5** (impact) Suppose the number in Access Trades!C10 were 10% higher. List every other cell whose value would change.
  - answer: `['Access Trades!C103', 'Access Trades!J9', 'Transfer!D4', 'Transfer!D40', 'Transfer!F4']`; cell `Access Trades!C10`

- [ ] **q6** (hardcode) Consider the range Access Trades!E10:E30 (the column of 'Price'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `11 cells, e.g. ['Access Trades!E10', 'Access Trades!E11', 'Access Trades!E12']`; cell `Access Trades!E10`

## rw3_enron_holden_salisbury (enron: `holden_salisbury__12296__$ Calculator.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Price for 8 LLH =', column headed 'You Call It !', in the sheet 'You Call It'?
  - answer: `13.25`; cell `You Call It!D14`
  - read: You Call It!C14 = 'Price for 8 LLH ='; You Call It!D9 = 'You Call It !'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'FLAT', column headed 'Q3-99', in the sheet 'Calculator'? Give its cell address.
  - answer: `Calculator!P29`; cell `Calculator!P29`
  - read: Calculator!M29 = 'FLAT'; Calculator!P26 = 'Q3-99'

- [ ] **q3** (trace) Consider the cell You Call It!G5 (in the row labelled 'Price for LLH ='). List the cells its formula reads directly (not indirectly).
  - answer: `['You Call It!D5', 'You Call It!E5', 'You Call It!F5']`; cell `You Call It!G5`
  - formula: `=((D5+E5)*F5)+(D5+E5)`

- [ ] **q4** (trace) Consider the cell Bal of Month!M9 (in the row labelled 'Buy'). List the cells its formula reads directly (not indirectly).
  - answer: `['Bal of Month!M4', 'Bal of Month!M6']`; cell `Bal of Month!M9`
  - formula: `=ABS(M4-M6)`

- [ ] **q5** (impact) Suppose the number in Calculator!N15 (in the row labelled 'HLH') were 10% higher. List every other cell whose value would change.
  - answer: `['Calculator!M43', 'Calculator!R27']`; cell `Calculator!N15`

- [ ] **q6** (hardcode) Consider the range You Call It!D4:G4 (the row of 'Price for HLH ='). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['You Call It!D4', 'You Call It!E4', 'You Call It!F4']`; cell `You Call It!D4`

## rw3_enron_john_arnold (enron: `john_arnold__15200__AppalachiaGas2.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Average Daily Nominal Volume (CNG)', in the sheet 'Volumes'?
  - answer: `5619.480073662205`; cell `Volumes!D4`
  - read: Volumes!A4 = 'Average Daily Nominal Volume (CNG)'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Total Nominal Volume (CNG+TCO)', in the sheet 'Volumes'? Give its cell address.
  - answer: `Volumes!D1`; cell `Volumes!D1`
  - read: Volumes!A1 = 'Total Nominal Volume (CNG+TCO)'

- [ ] **q3** (trace) Consider the cell Volumes!R12. List the cells its formula reads directly (not indirectly).
  - answer: `['Curves!B3', 'Volumes!Q12']`; cell `Volumes!R12`
  - formula: `=Q12*Curves!B3`

- [ ] **q4** (trace) Consider the cell Volumes!S73. List the cells its formula reads directly (not indirectly).
  - answer: `['Volumes!A73', 'Volumes!R73']`; cell `Volumes!S73`
  - formula: `=R73*A73`

- [ ] **q5** (impact) Suppose the number in Curves!B80 were 10% higher. List every other cell whose value would change.
  - answer: `['Volumes!D2', 'Volumes!G9', 'Volumes!G90', 'Volumes!H90', 'Volumes!R9', 'Volumes!R90', 'Volumes!S90']`; cell `Curves!B80`

- [ ] **q6** (hardcode) Consider the range Volumes!E58:H58. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Volumes!E58']`; cell `Volumes!E58`

## rw3_enron_john_hodge (enron: `john_hodge__16246__Tricia Roome.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Summer 05', column headed 'Transco Z5', in the sheet 'Sheet1'?
  - answer: `0.41999999999999993`; cell `Sheet1!L17`
  - read: Sheet1!J17 = 'Summer 05'; Sheet1!L12 = 'Transco Z5'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Summer 03', column headed 'Transco Z5', in the sheet 'Sheet1'? Give its cell address.
  - answer: `Sheet1!L15`; cell `Sheet1!L15`
  - read: Sheet1!J15 = 'Summer 03'; Sheet1!L12 = 'Transco Z5'

- [ ] **q3** (trace) Consider the cell Sheet1!H50. List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!F50', 'Sheet1!G50']`; cell `Sheet1!H50`
  - formula: `=F50+G50`

- [ ] **q4** (trace) Consider the cell Sheet1!K5 (in the row labelled 'Winter 01'). List the cells its formula reads directly (not indirectly).
  - answer: `['Sheet1!E5', 'Sheet1!E6', 'Sheet1!E7', 'Sheet1!E8', 'Sheet1!E9']`; cell `Sheet1!K5`
  - formula: `=AVERAGE(E5:E9)`

- [ ] **q5** (impact) Suppose the number in Sheet1!D24 were 10% higher. List every other cell whose value would change.
  - answer: `['Sheet1!E24', 'Sheet1!K14']`; cell `Sheet1!D24`

- [ ] **q6** (hardcode) Consider the range Sheet1!B7:H7. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Sheet1!C7', 'Sheet1!D7', 'Sheet1!F7', 'Sheet1!G7']`; cell `Sheet1!B7`

## rw3_enron_john_lavorato (enron: `john_lavorato__16532__Turbine Position Report 111601.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'GRAND TOTALS', column headed 'SCHEDULED CONTRACT PYMTS TO DATE', in the sheet 'Summary by Region'?
  - answer: `391.6189440000001`; cell `Summary by Region!H26`
  - read: Summary by Region!F26 = 'GRAND TOTALS'; Summary by Region!H6 = 'SCHEDULED CONTRACT PYMTS TO DATE'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Total Tentative', column headed 'CONTRACT COST', in the sheet 'Summary by Status'? Give its cell address.
  - answer: `Summary by Status!H15`; cell `Summary by Status!H15`
  - read: Summary by Status!F15 = 'Total Tentative'; Summary by Status!H6 = 'CONTRACT COST'

- [ ] **q3** (trace) Consider the cell Cost Cancel Details!AT7 (in the row labelled '% Cancellation'). List the cells its formula reads directly (not indirectly).
  - answer: `['Cost Cancel Details!AS8', 'Cost Cancel Details!AT8']`; cell `Cost Cancel Details!AT7`
  - formula: `=AT8-AS8`

- [ ] **q4** (trace) Consider the cell Cost Cancel Details!AH14 (in the row labelled '% Cumulative Progress Payments'). List the cells its formula reads directly (not indirectly).
  - answer: `['Cost Cancel Details!AG14', 'Cost Cancel Details!AH13']`; cell `Cost Cancel Details!AH14`
  - formula: `=+AG14+AH13`

- [ ] **q5** (impact) Suppose the number in Cost Cancel Details!AI64 (in the row labelled '% Cumulative Cancellation') were 10% higher. List every other cell whose value would change.
  - answer: `['Cost Cancel Details!AI120', 'Cost Cancel Details!AI124', 'Cost Cancel Details!AI125', 'Cost Cancel Details!AI129', 'Cost Cancel Details!AI130', 'Cost Cancel Details!AI63', 'Cost Cancel Details!AI67', 'Cost Cancel Details!AJ63']`; cell `Cost Cancel Details!AI64`

- [ ] **q6** (hardcode) Consider the range Cost Cancel Details!AE101:AE104. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Cost Cancel Details!AE101', 'Cost Cancel Details!AE103']`; cell `Cost Cancel Details!AE101`

## rw3_enron_kimberly_watson (enron: `kimberly_watson__20561__Index-Indexmarginanalysissummaryunwind.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Nov. '02 - Dec. '02', column headed 'Margin', in the sheet 'I to I Summary'?
  - answer: `1350845`; cell `I to I Summary!F9`
  - read: I to I Summary!C9 = "Nov. '02 - Dec. '02"; I to I Summary!F3 = 'Margin'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Calendar 2002', column headed 'on Unwind', in the sheet 'I to I Summary'? Give its cell address.
  - answer: `I to I Summary!O10`; cell `I to I Summary!O10`
  - read: I to I Summary!C10 = 'Calendar 2002'; I to I Summary!O3 = 'on Unwind'

- [ ] **q3** (trace) Consider the cell I to I Summary!K18 (in the row labelled 'Totals'). List the cells its formula reads directly (not indirectly).
  - answer: `['I to I Summary!K11', 'I to I Summary!K16', 'I to I Summary!K6']`; cell `I to I Summary!K18`
  - formula: `=K6+K11+K16`

- [ ] **q4** (trace) Consider the cell I to I Summary!I18 (in the row labelled 'Totals'). List the cells its formula reads directly (not indirectly).
  - answer: `['I to I Summary!I11', 'I to I Summary!I16', 'I to I Summary!I6']`; cell `I to I Summary!I18`
  - formula: `=I6+I11+I16`

- [ ] **q5** (impact) Suppose the number in I to I Summary!F16 were 10% higher. List every other cell whose value would change.
  - answer: `['I to I Summary!F18', 'I to I Summary!G16', 'I to I Summary!G18']`; cell `I to I Summary!F16`

- [ ] **q6** (hardcode) Consider the range I to I Summary!D15:J15 (the row of 'Calendar 2003'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['I to I Summary!D15', 'I to I Summary!E15', 'I to I Summary!F15', 'I to I Summary!H15', 'I to I Summary!I15']`; cell `I to I Summary!D15`

## rw3_enron_mark_haedicke (enron: `mark_haedicke__24593__2001BUDGET-102049 ns.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Regular - USE INPUT AREA BELOW', column headed 'MAR', in the sheet 'Detail'?
  - answer: `87256`; cell `Detail!G21`
  - read: Detail!B21 = 'Regular - USE INPUT AREA BELOW'; Detail!G9 = 'MAR'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'BENEFITS - CALCULATED, U.S. EMPLOYEES', column headed 'SEP', in the sheet 'Detail'? Give its cell address.
  - answer: `Detail!M32`; cell `Detail!M32`
  - read: Detail!B32 = 'BENEFITS - CALCULATED, U.S. EMPLOYEES'; Detail!M9 = 'SEP'

- [ ] **q3** (trace) Consider the cell Detail!F216 (in the row labelled 'Employee 5'). List the cells its formula reads directly (not indirectly).
  - answer: `['Detail!E216', 'Detail!F188']`; cell `Detail!F216`
  - formula: `=+F188+E216`

- [ ] **q4** (trace) Consider the cell Detail!O235 (in the row labelled 'Employee 24'). List the cells its formula reads directly (not indirectly).
  - answer: `['Detail!N235', 'Detail!O207']`; cell `Detail!O235`
  - formula: `=+O207+N235`

- [ ] **q5** (impact) Suppose the number in Headcount!M8 (in the row labelled 'Full Time') were 10% higher. List every other cell whose value would change.
  - answer: `['Headcount!M13', 'Headcount!M15', 'Headcount!M28', 'Headcount!M33', 'Headcount!M35']`; cell `Headcount!M8`

- [ ] **q6** (hardcode) Consider the range Detail!C154:S154 (the row of 'Other'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `14 cells, e.g. ['Detail!C154', 'Detail!D154', 'Detail!E154']`; cell `Detail!C154`

## rw3_enron_mark_whitt (enron: `mark_whitt__25262__11-5-01 Hot List.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Gas supply support', column headed 'Q4', in the sheet 'West Gas Hot List'?
  - answer: `2002`; cell `West Gas Hot List!E47`
  - read: West Gas Hot List!C47 = 'Gas supply support'; West Gas Hot List!E46 = 'Q4'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Q4', column headed 'Orig Amount', in the sheet 'Sheet2'? Give its cell address.
  - answer: `Sheet2!B5`; cell `Sheet2!B5`
  - read: Sheet2!A5 = 'Q4'; Sheet2!B1 = 'Orig Amount'

- [ ] **q3** (trace) Consider the cell West Gas Hot List!I48 (in the row labelled 'N'). List the cells its formula reads directly (not indirectly).
  - answer: `['West Gas Hot List!G48', 'West Gas Hot List!H48']`; cell `West Gas Hot List!I48`
  - formula: `=G48*H48`

- [ ] **q4** (trace) Consider the cell West Gas Hot List!I15 (in the row labelled 'N'). List the cells its formula reads directly (not indirectly).
  - answer: `['West Gas Hot List!G15', 'West Gas Hot List!H15']`; cell `West Gas Hot List!I15`
  - formula: `=G15*H15`

- [ ] **q5** (impact) Suppose the number in West Gas Hot List!H59 (in the row labelled 'Q4') were 10% higher. List every other cell whose value would change.
  - answer: `['Sheet2!B5', 'West Gas Hot List!I11', 'West Gas Hot List!I59', 'West Gas Hot List!I66']`; cell `West Gas Hot List!H59`

- [ ] **q6** (hardcode) Consider the range West Gas Hot List!I30:I36 (the column of 'Expected Value'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['West Gas Hot List!I34', 'West Gas Hot List!I35', 'West Gas Hot List!I36']`; cell `West Gas Hot List!I30`

## rw3_enron_mary_fischer (enron: `mary_fischer__25634__31Q.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'TOT_SHARE_EQU', column headed 'DR (CR)', in the sheet 'E31.XLS'?
  - answer: `-13304252`; cell `E31.XLS!O23`
  - read: E31.XLS!C23 = 'TOT_SHARE_EQU'; E31.XLS!O11 = 'DR (CR)'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'JV Gain/Loss', column headed '2ND QTR', in the sheet 'E20.XLS'? Give its cell address.
  - answer: `E20.XLS!E16`; cell `E20.XLS!E16`
  - read: E20.XLS!A16 = 'JV Gain/Loss'; E20.XLS!E11 = '2ND QTR'

- [ ] **q3** (trace) Consider the cell E8.XLS!M19. List the cells its formula reads directly (not indirectly).
  - answer: `['E8.XLS!C19', 'E8.XLS!D19', 'E8.XLS!E19', 'E8.XLS!F19', 'E8.XLS!G19', 'E8.XLS!H19', 'E8.XLS!I19']`; cell `E8.XLS!M19`
  - formula: `=SUM(C19:I19)`

- [ ] **q4** (trace) Consider the cell E20.XLS!K30. List the cells its formula reads directly (not indirectly).
  - answer: `['E20.XLS!C30', 'E20.XLS!D30', 'E20.XLS!E30', 'E20.XLS!F30', 'E20.XLS!G30', 'E20.XLS!H30', 'E20.XLS!I30']`; cell `E20.XLS!K30`
  - formula: `=SUM(C30:I30)`

- [ ] **q5** (impact) Suppose the number in E20.XLS!C16 (in the row labelled 'JV Gain/Loss') were 10% higher. List every other cell whose value would change.
  - answer: `['E20.XLS!C41', 'E20.XLS!K16', 'E20.XLS!K41']`; cell `E20.XLS!C16`

- [ ] **q6** (hardcode) Consider the range E8.XLS!M34:M45 (the column of 'ENDING BALANCE'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `E8.XLS!M34`

## rw3_enron_paul_y_barbo (enron: `paul_y'barbo__28521__Eco Inventory.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Working Inventory', in the sheet '96%'?
  - answer: `145921.5`; cell `96%!D3`
  - read: 96%!B3 = 'Working Inventory'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Tank Shell Capacity', in the sheet '90%'? Give its cell address.
  - answer: `90%!D1`; cell `90%!D1`
  - read: 90%!B1 = 'Tank Shell Capacity'

- [ ] **q3** (trace) Consider the cell 13 wk outtage!E378. List the cells its formula reads directly (not indirectly).
  - answer: `['13 wk outtage!B378', '13 wk outtage!D3']`; cell `13 wk outtage!E378`
  - formula: `=$D$3-B378`

- [ ] **q4** (trace) Consider the cell 13 wk outtage!E302. List the cells its formula reads directly (not indirectly).
  - answer: `['13 wk outtage!B302', '13 wk outtage!D3']`; cell `13 wk outtage!E302`
  - formula: `=$D$3-B302`

- [ ] **q5** (impact) Suppose the number in 13 wk outtage!D421 were 10% higher. List every other cell whose value would change.
  - answer: `295 cells, e.g. ['13 wk outtage!B422', '13 wk outtage!B423', '13 wk outtage!B424']`; cell `13 wk outtage!D421`

- [ ] **q6** (hardcode) Consider the range 13 wk outtage!J171:J188. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `13 wk outtage!J171`

## rw3_enron_ryan_slinger (enron: `ryan_slinger__33681__6_21act.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'NEWMAN 2 (25-78)', column headed 'Capacity', in the sheet 'Preschedule'?
  - answer: `78`; cell `Preschedule!Z42`
  - read: Preschedule!A42 = 'NEWMAN 2           (25-78)'; Preschedule!Z40 = 'Capacity'

- [ ] **q2** (address) Which cell holds the value in the row labelled '1/1-12/31/98 price not given (SJ)', column headed 'Volume', in the sheet 'Fuel'? Give its cell address.
  - answer: `Fuel!E39`; cell `Fuel!E39`
  - read: Fuel!B39 = '1/1-12/31/98 price not given (SJ)'; Fuel!E37 = 'Volume'

- [ ] **q3** (trace) Consider the cell Preschedule!E62 (in the row labelled 'Palo Verde 510'). List the cells its formula reads directly (not indirectly).
  - answer: `12 cells, e.g. ['Preschedule!E12', 'Preschedule!E13', 'Preschedule!E14']`; cell `Preschedule!E62`
  - formula: `=-SUM(E12:E15,E29:E32,E22) + SUM(E53:E55)`

- [ ] **q4** (trace) Consider the cell Preschedule!C29 (in the row labelled 'PV PRESCHEDULED'). List the cells its formula reads directly (not indirectly).
  - answer: `['Deals!G71', 'Deals!G77']`; cell `Preschedule!C29`
  - formula: `=Deals!G71+Deals!G77`

- [ ] **q5** (impact) Suppose the number in Preschedule!Z50 (in the row labelled 'RIO GRANDE 6 (20-48)') were 10% higher. List every other cell whose value would change.
  - answer: `22 cells, e.g. ['Preschedule!C67', 'Preschedule!D67', 'Preschedule!E67']`; cell `Preschedule!Z50`

- [ ] **q6** (hardcode) Consider the range Deals!AB14:AF14 (the row of 'PV'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Deals!AB14', 'Deals!AC14']`; cell `Deals!AB14`

