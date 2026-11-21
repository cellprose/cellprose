# Review record (Tier 2 real-world set)

Every question was made by the rules in `external/realworld2.py` and its answer computed from the file. Each needs two readers, one of them human, before Tier 2 runs: check that the wording names the cell it says and that the answer is right. Mark a bad question here; it is dropped by rule, never rewritten after a model has seen it.

## dev_e_052101_weather_difference_forecast_compa (enron: `chris_stokley__3949__052101 Weather Difference Forecast Compare.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Week', column headed 'Daily Total', in the sheet 'Report'?
  - answer: `76.42474313624425`; cell `Report!B8`
  - read: Report!A8 = 'Week'; Report!B7 = 'Daily Total'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'PGE', in the sheet 'Report'? Give its cell address.
  - answer: `Report!P8`; cell `Report!P8`
  - read: Report!F8 = 'PGE'

- [ ] **q3** (trace) Consider the cell Differences!Q31. List the cells its formula reads directly (not indirectly).
  - answer: `['ActualWeather050701-051301!Q31', 'ForecastedWeather050701-051301!Q31']`; cell `Differences!Q31`
  - formula: `='ForecastedWeather050701-051301'!Q31-'ActualWeather050701-051301'!Q31`

- [ ] **q4** (trace) Consider the cell Summary!N8. List the cells its formula reads directly (not indirectly).
  - answer: `['Differences!N32', 'Differences!N8']`; cell `Summary!N8`
  - formula: `=Differences!N8+Differences!N32`

- [ ] **q5** (impact) Suppose the number in ForecastedWeather050701-051301!O48 were 10% higher. List every other cell whose value would change.
  - answer: `12 cells, e.g. ['Differences!AA48', 'Differences!AB48', 'Differences!AC48']`; cell `ForecastedWeather050701-051301!O48`

- [ ] **q6** (hardcode) Consider the range Summary!F2:F25. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Summary!F10', 'Summary!F18', 'Summary!F2']`; cell `Summary!F2`

## dev_e_2000wk12final (enron: `jeff_dasovich__14113__2000WK12final.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Prentice', column headed 'New Total', in the sheet 'Week #12'?
  - answer: `900`; cell `Week #12!F26`
  - read: Week #12!B26 = 'Prentice'; Week #12!F6 = 'New Total'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Nancy', column headed 'Weekly Total', in the sheet 'Week #12'? Give its cell address.
  - answer: `Week #12!G30`; cell `Week #12!G30`
  - read: Week #12!B30 = 'Nancy'; Week #12!G6 = 'Weekly Total'

- [ ] **q3** (trace) Consider the cell Week #12!AQ30 (in the row labelled 'Nancy'). List the cells its formula reads directly (not indirectly).
  - answer: `['Week #12!AJ30', 'Week #12!AL30', 'Week #12!G30']`; cell `Week #12!AQ30`
  - formula: `=$G30+$AJ30+AL30`

- [ ] **q4** (trace) Consider the cell Week #12!AN16 (in the row labelled 'Donna'). List the cells its formula reads directly (not indirectly).
  - answer: `['Week #12!AI16', 'Week #12!AK16', 'Week #12!G16']`; cell `Week #12!AN16`
  - formula: `=$G16+$AI16+AK16`

- [ ] **q5** (impact) Suppose the number in Week #12!AJ29 (in the row labelled 'WAM') were 10% higher. List every other cell whose value would change.
  - answer: `['Week #12!AJ33', 'Week #12!AJ34', 'Week #12!AM29', 'Week #12!AP29', 'Week #12!AQ29']`; cell `Week #12!AJ29`

- [ ] **q6** (hardcode) Consider the range Week #12!AL11:AQ11 (the row of 'JAM'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Week #12!AL11']`; cell `Week #12!AL11`

## dev_e_5th_floorplan_0130 (enron: `stacey_white__39145__5th floorplan 0130.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled '3513d', column headed 'ECS location', in the sheet 'IT Tab'?
  - answer: `541`; cell `IT Tab!E26`
  - read: IT Tab!D26 = '3513d'; IT Tab!E1 = 'ECS location'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Stacey', in the sheet 'IT Tab'? Give its cell address.
  - answer: `IT Tab!C222`; cell `IT Tab!C222`
  - read: IT Tab!B222 = 'Stacey'

- [ ] **q3** (trace) Consider the cell Floor Plan Changes!I7 (in the row labelled 'Beck'). List the cells its formula reads directly (not indirectly).
  - answer: `['Floor Plan Changes!G7', 'Floor Plan Changes!H7']`; cell `Floor Plan Changes!I7`
  - formula: `=SUM(G7:H7)`

- [ ] **q4** (trace) Consider the cell 5th floor analysis!F16 (in the row labelled 'Frazier'). List the cells its formula reads directly (not indirectly).
  - answer: `['5th floor analysis!D16', '5th floor analysis!E16']`; cell `5th floor analysis!F16`
  - formula: `=SUM(D16:E16)`

- [ ] **q5** (impact) Suppose the number in Floor Plan Changes!Q112 were 10% higher. List every other cell whose value would change.
  - answer: `['Floor Plan Changes!B97', 'Floor Plan Changes!B99', 'Floor Plan Changes!G28', 'Floor Plan Changes!H28', 'Floor Plan Changes!Q116']`; cell `Floor Plan Changes!Q112`

- [ ] **q6** (hardcode) Consider the range Floor Plan Changes!K87:O87. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Floor Plan Changes!O87']`; cell `Floor Plan Changes!K87`

## dev_e_correlations (enron: `monika_causholli__28173__Correlations.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled '3 month lag', column headed 'Formbond', in the sheet 'Regressions'?
  - answer: `0.3617503405957818`; cell `Regressions!AG11`
  - read: Regressions!AD11 = '3 month lag'; Regressions!AG6 = 'Formbond'

- [ ] **q2** (address) Which cell holds the value in the row labelled '2 month lag', column headed '80 lb. + Sheets', in the sheet 'Regressions'? Give its cell address.
  - answer: `Regressions!AH10`; cell `Regressions!AH10`
  - read: Regressions!AD10 = '2 month lag'; Regressions!AH6 = '  80 lb. + Sheets'

- [ ] **q3** (trace) Consider the cell Regressions!V142. List the cells its formula reads directly (not indirectly).
  - answer: `['Regressions!H141', 'Regressions!H142']`; cell `Regressions!V142`
  - formula: `=H142-H141`

- [ ] **q4** (trace) Consider the cell Regressions!T18. List the cells its formula reads directly (not indirectly).
  - answer: `['Regressions!F17', 'Regressions!F18']`; cell `Regressions!T18`
  - formula: `=F18-F17`

- [ ] **q5** (impact) Suppose the number in simplecorr!E65 were 10% higher. List every other cell whose value would change.
  - answer: `14 cells, e.g. ['simplecorr!Q10', 'simplecorr!Q11', 'simplecorr!Q12']`; cell `simplecorr!E65`

- [ ] **q6** (hardcode) Consider the range Regressions!Q155:AA155. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `Regressions!Q155`

## dev_e_counterparty_tracking_report (enron: `elizabeth_sager__9495__Counterparty Tracking Report.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Yes', column headed 'Written Contact Made to Counterparty', in the sheet 'Mission Critical Counterparties'?
  - answer: `1`; cell `Mission Critical Counterparties!P20`
  - read: Mission Critical Counterparties!J20 = 'Yes'; Mission Critical Counterparties!P3 = 'Written Contact Made to Counterparty'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Financial - US Total', column headed 'Unsatisfactory', in the sheet 'Tier 2 Counterparties'? Give its cell address.
  - answer: `Tier 2 Counterparties!W18`; cell `Tier 2 Counterparties!W18`
  - read: Tier 2 Counterparties!D18 = 'Financial - US Total'; Tier 2 Counterparties!W3 = 'Unsatisfactory'

- [ ] **q3** (trace) Consider the cell Mission Critical Counterparties!U99. List the cells its formula reads directly (not indirectly).
  - answer: `['Mission Critical Counterparties!P98', 'Mission Critical Counterparties!U98']`; cell `Mission Critical Counterparties!U99`
  - formula: `=ROUND(U98/$P$98,3)`

- [ ] **q4** (trace) Consider the cell Tier 2 Counterparties!U60. List the cells its formula reads directly (not indirectly).
  - answer: `['Tier 2 Counterparties!P59', 'Tier 2 Counterparties!U59']`; cell `Tier 2 Counterparties!U60`
  - formula: `=ROUND(U59/$P$59,3)`

- [ ] **q5** (impact) Suppose the number in Tier 2 Counterparties!S15 (in the row labelled 'Satisfactory') were 10% higher. List every other cell whose value would change.
  - answer: `['Tier 2 Counterparties!S18', 'Tier 2 Counterparties!S19', 'Tier 2 Counterparties!S74', 'Tier 2 Counterparties!S75']`; cell `Tier 2 Counterparties!S15`

- [ ] **q6** (hardcode) Consider the range Tier 2 Counterparties!P20:P34 (the column of 'Written Contact Made to Counterparty'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `14 cells, e.g. ['Tier 2 Counterparties!P20', 'Tier 2 Counterparties!P21', 'Tier 2 Counterparties!P22']`; cell `Tier 2 Counterparties!P20`

## dev_e_epe_april_2001 (enron: `steven_merriss__39340__EPE_APRIL_2001.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'PNM TAG 11206', column headed 'FOR THE DAY', in the sheet 'APRIL (9)'?
  - answer: `20555`; cell `APRIL (9)!D11`
  - read: APRIL (9)!C11 = 'PNM TAG 11206'; APRIL (9)!D8 = 'FOR THE DAY'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'SDGE TAG 2474', column headed 'FOR THE DAY', in the sheet 'APRIL (9)'? Give its cell address.
  - answer: `APRIL (9)!F11`; cell `APRIL (9)!F11`
  - read: APRIL (9)!E11 = 'SDGE TAG 2474'; APRIL (9)!F8 = 'FOR THE DAY'

- [ ] **q3** (trace) Consider the cell APRIL (5)!I34. List the cells its formula reads directly (not indirectly).
  - answer: `['APRIL (5)!C34', 'APRIL (5)!D34', 'APRIL (5)!E34', 'APRIL (5)!F34', 'APRIL (5)!G34', 'APRIL (5)!H34']`; cell `APRIL (5)!I34`
  - formula: `=SUM(C34:H34)`

- [ ] **q4** (trace) Consider the cell APRIL (5)!I17. List the cells its formula reads directly (not indirectly).
  - answer: `['APRIL (5)!C17', 'APRIL (5)!D17', 'APRIL (5)!E17', 'APRIL (5)!F17', 'APRIL (5)!G17', 'APRIL (5)!H17']`; cell `APRIL (5)!I17`
  - formula: `=SUM(C17:H17)`

- [ ] **q5** (impact) Suppose the number in APRIL (1)!K21 were 10% higher. List every other cell whose value would change.
  - answer: `['APRIL (1)!K39', 'APRIL (1)!K41', 'APRIL (1)!Q21', 'APRIL (1)!Q39', 'APRIL (1)!Q41']`; cell `APRIL (1)!K21`

- [ ] **q6** (hardcode) Consider the range APRIL (6)!A26:G26. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['APRIL (6)!A26', 'APRIL (6)!B26', 'APRIL (6)!C26', 'APRIL (6)!D26', 'APRIL (6)!E26', 'APRIL (6)!F26']`; cell `APRIL (6)!A26`

## dev_e_ercot_pvsgas1_7_30 (enron: `louise_kitchen__22604__ERCOT_PvsGAS1_7-30.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Cal 09', column headed 'Ercot', in the sheet 'Snapshot'?
  - answer: `38.05`; cell `Snapshot!B9`
  - read: Snapshot!A9 = 'Cal 09'; Snapshot!B2 = 'Ercot'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Cal 06', column headed 'Ercot', in the sheet 'Snapshot'? Give its cell address.
  - answer: `Snapshot!B6`; cell `Snapshot!B6`
  - read: Snapshot!A6 = 'Cal 06'; Snapshot!B2 = 'Ercot'

- [ ] **q3** (trace) Consider the cell Historical!E5. List the cells its formula reads directly (not indirectly).
  - answer: `['Historical!B5', 'Historical!C5']`; cell `Historical!E5`
  - formula: `=B5/C5`

- [ ] **q4** (trace) Consider the cell Historical!D196. List the cells its formula reads directly (not indirectly).
  - answer: `['Historical!B196', 'Historical!C196']`; cell `Historical!D196`
  - formula: `=B196-C196`

- [ ] **q5** (impact) Suppose the number in Historical!B106 were 10% higher. List every other cell whose value would change.
  - answer: `['Historical!D106', 'Historical!E106', 'Historical!I2']`; cell `Historical!B106`

- [ ] **q6** (hardcode) Consider the range Historical!B173:E173. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Historical!B173', 'Historical!C173']`; cell `Historical!B173`

## dev_e_erec_ic_10_19 (enron: `tracy_geaccone__40195__EREC IC 10-19.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'EES', in the sheet 'ICFeb correction'?
  - answer: `18`; cell `ICFeb correction!AR13`
  - read: ICFeb correction!C13 = 'EES'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Enron Europe Originations', column headed '****** move to 011', in the sheet 'ICFeb correction'? Give its cell address.
  - answer: `ICFeb correction!AP18`; cell `ICFeb correction!AP18`
  - read: ICFeb correction!C18 = 'Enron Europe Originations'; ICFeb correction!AP14 = '****** move to 011'

- [ ] **q3** (trace) Consider the cell ICAprest!AD13 (in the row labelled 'EES'). List the cells its formula reads directly (not indirectly).
  - answer: `['ICAprest!AC13', 'ICAprest!AC25', 'ICAprest!AD25']`; cell `ICAprest!AD13`
  - formula: `=(AC13/AC$25)*AD$25`

- [ ] **q4** (trace) Consider the cell ICAprest!G20 (in the row labelled 'Global Products Trading'). List the cells its formula reads directly (not indirectly).
  - answer: `['ICAprest!E20', 'ICAprest!F20']`; cell `ICAprest!G20`
  - formula: `=SUM(E20:F20)`

- [ ] **q5** (impact) Suppose the number in ICAprest!Q22 (in the row labelled '34K') were 10% higher. List every other cell whose value would change.
  - answer: `34 cells, e.g. ['ICAprest!AG22', 'ICAprest!AG25', 'ICAprest!AH10']`; cell `ICAprest!Q22`

- [ ] **q6** (hardcode) Consider the range ICFeb correction!M8:M20 (the column of 'Primary Costs'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `11 cells, e.g. ['ICFeb correction!M10', 'ICFeb correction!M12', 'ICFeb correction!M13']`; cell `ICFeb correction!M8`

## dev_e_july2001pricinggriffithprelim2_jc (enron: `jane_tholt__13115__July2001pricinggriffithprelim2_jc.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled '(Ln14)', column headed '(Ln14D+Ln32E)', in the sheet 'July 17 Supply Price'?
  - answer: `-0.18757499999999983`; cell `July 17 Supply Price!G20`
  - read: July 17 Supply Price!C20 = '(Ln14)'; July 17 Supply Price!G16 = '(Ln14D+Ln32E)'

- [ ] **q2** (address) Which cell holds the value in the row labelled '(Ln1-Ln20)', column headed '(D)', in the sheet 'July 17 Supply Price'? Give its cell address.
  - answer: `July 17 Supply Price!D24`; cell `July 17 Supply Price!D24`
  - read: July 17 Supply Price!C24 = '(Ln1-Ln20)'; July 17 Supply Price!D2 = '(D)'

- [ ] **q3** (trace) Consider the cell Sales!D704. List the cells its formula reads directly (not indirectly).
  - answer: `['Sales!B704', 'Sales!C9']`; cell `Sales!D704`
  - formula: `=B704/(1-$C$9)`

- [ ] **q4** (trace) Consider the cell Sales!D817. List the cells its formula reads directly (not indirectly).
  - answer: `['Sales!B817', 'Sales!C9']`; cell `Sales!D817`
  - formula: `=B817/(1-$C$9)`

- [ ] **q5** (impact) Suppose the number in Sales!K35 were 10% higher. List every other cell whose value would change.
  - answer: `['Sales!L35', 'Sales!M35', 'Sales!O35', 'Sales!P35', 'Sales!S35', 'Sales!V35']`; cell `Sales!K35`

- [ ] **q6** (hardcode) Consider the range Sales!O22:V22. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Sales!Q22']`; cell `Sales!O22`

## dev_e_markets_enron_online_3_1 (enron: `harry_arora__12179__Markets Enron Online 3.1.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'EOL Share Cash Flow', column headed 'GDP NUMBERS * POTENTIAL TURNS * COMMODITIZATION SPEED * ADDRESSABLE %', in the sheet 'VAS CF'?
  - answer: `1532918.6184401524`; cell `VAS CF!D53`
  - read: VAS CF!A53 = 'EOL Share Cash Flow'; VAS CF!D47 = 'GDP NUMBERS * POTENTIAL TURNS * COMMODITIZATION SPEED * ADDR'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Natural Gas', column headed 'Lump Sum for Brand ($'000)', in the sheet 'Private Label Ass'? Give its cell address.
  - answer: `Private Label Ass!C44`; cell `Private Label Ass!C44`
  - read: Private Label Ass!A44 = '     Natural Gas'; Private Label Ass!C41 = "Lump Sum for Brand          ($'000)"

- [ ] **q3** (trace) Consider the cell Expenses!C92 (in the row labelled 'Conferences & Training'). List the cells its formula reads directly (not indirectly).
  - answer: `['Expenses!B92', 'Total Market Size!C136']`; cell `Expenses!C92`
  - formula: `=+B92*(1+'Total Market Size'!C$136)`

- [ ] **q4** (trace) Consider the cell Cash Flow!B15 (in the row labelled 'Total Operating Expenses'). List the cells its formula reads directly (not indirectly).
  - answer: `['Cash Flow!B10', 'Cash Flow!B11', 'Cash Flow!B12', 'Cash Flow!B13', 'Cash Flow!B14']`; cell `Cash Flow!B15`
  - formula: `=SUM(B10:B14)`

- [ ] **q5** (impact) Suppose the number in Liquids!D8 (in the row labelled 'Eastern Europe & Former USSR') were 10% higher. List every other cell whose value would change.
  - answer: `395 cells, e.g. [' Volume Assumptions!B79', ' Volume Assumptions!B90', ' Volume Assumptions!C79']`; cell `Liquids!D8`

- [ ] **q6** (hardcode) Consider the range Many to Many Revenue!J23:J36. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Many to Many Revenue!J23']`; cell `Many to Many Revenue!J23`

## dev_e_mastersocal (enron: `monique_sanchez__28312__mastersocal..xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Cornudas West', in the sheet 'FLOWS'?
  - answer: `1650`; cell `FLOWS!D84`
  - read: FLOWS!B84 = 'Cornudas West'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'La Paloma II', column headed 'GAS', in the sheet 'PLANTS'? Give its cell address.
  - answer: `PLANTS!E15`; cell `PLANTS!E15`
  - read: PLANTS!A15 = 'La Paloma II'; PLANTS!E1 = 'GAS'

- [ ] **q3** (trace) Consider the cell PLANTS!AX63. List the cells its formula reads directly (not indirectly).
  - answer: `['PLANTS!A63', 'PLANTS!AW30', 'PLANTS!AW31', 'PLANTS!AY63']`; cell `PLANTS!AX63`
  - formula: `=IF($A63>=AW$30,AW$31*AY63,0)`

- [ ] **q4** (trace) Consider the cell PLANTS!AL68. List the cells its formula reads directly (not indirectly).
  - answer: `['PLANTS!A68', 'PLANTS!AK30', 'PLANTS!AK31', 'PLANTS!AM68']`; cell `PLANTS!AL68`
  - formula: `=IF($A68>=AK$30,AK$31*AM68,0)`

- [ ] **q5** (impact) Suppose the number in FLOWS!BI56 were 10% higher. List every other cell whose value would change.
  - answer: `12 cells, e.g. ['FLOWS!AA56', 'FLOWS!AB56', 'FLOWS!AE56']`; cell `FLOWS!BI56`

- [ ] **q6** (hardcode) Consider the range FLOWS!B53:K53. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['FLOWS!C53', 'FLOWS!D53', 'FLOWS!I53', 'FLOWS!K53']`; cell `FLOWS!B53`

## dev_e_ontario_0301gl (enron: `phillip_m_love__30132__Ontario 0301GL.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Total Flash to Actual Variance', column headed 'Total', in the sheet 'Ontario'?
  - answer: `21189639`; cell `Ontario!V7`
  - read: Ontario!A7 = 'Total Flash to Actual Variance '; Ontario!V6 = 'Total'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Miscellaneous variances', in the sheet 'Ontario'? Give its cell address.
  - answer: `Ontario!R31`; cell `Ontario!R31`
  - read: Ontario!C31 = 'Miscellaneous variances'

- [ ] **q3** (trace) Consider the cell Ontario!I84 (in the row labelled 'Unexplained Variance'). List the cells its formula reads directly (not indirectly).
  - answer: `['Ontario!I7', 'Ontario!I82']`; cell `Ontario!I84`
  - formula: `=+I7-I82`

- [ ] **q4** (trace) Consider the cell Ontario!L84 (in the row labelled 'Unexplained Variance'). List the cells its formula reads directly (not indirectly).
  - answer: `['Ontario!L7', 'Ontario!L82']`; cell `Ontario!L84`
  - formula: `=+L7-L82`

- [ ] **q5** (impact) Suppose the number in Ontario!E12 (in the row labelled 'PMA's') were 10% higher. List every other cell whose value would change.
  - answer: `['Ontario!E14', 'Ontario!E82', 'Ontario!E84', 'Ontario!V12', 'Ontario!V14', 'Ontario!V82', 'Ontario!V84']`; cell `Ontario!E12`

- [ ] **q6** (hardcode) Consider the range Ontario!O71:R71 (the row of 'Enron Canada purchase variances - Deals ECC doesn't recognize'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Ontario!Q71', 'Ontario!R71']`; cell `Ontario!O71`

## dev_e_peak2001_1_18_10yr_for_rfp (enron: `dan_hyvl__4805__PEAK2001 1-18 10yr for RFP.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Ten Year UST', column headed 'Factor', in the sheet 'Seller's's PP Calc'?
  - answer: `0.051`; cell `Seller's's PP Calc!W8`
  - read: Seller's's PP Calc!V8 = 'Ten Year UST'; Seller's's PP Calc!W6 = 'Factor'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Swap Spread', column headed 'Factor', in the sheet 'Seller's's PP Calc'? Give its cell address.
  - answer: `Seller's's PP Calc!W9`; cell `Seller's's PP Calc!W9`
  - read: Seller's's PP Calc!V9 = 'Swap Spread'; Seller's's PP Calc!W6 = 'Factor'

- [ ] **q3** (trace) Consider the cell Seller's's PP Calc!C90. List the cells its formula reads directly (not indirectly).
  - answer: `["Seller's's PP Calc!A12", "Seller's's PP Calc!B90"]`; cell `Seller's's PP Calc!C90`
  - formula: `=+B90-$A$12`

- [ ] **q4** (trace) Consider the cell Purchasers!C41. List the cells its formula reads directly (not indirectly).
  - answer: `['Purchasers!A41', 'Purchasers!A42']`; cell `Purchasers!C41`
  - formula: `=+A42-A41`

- [ ] **q5** (impact) Suppose the number in Purchasers!R131 were 10% higher. List every other cell whose value would change.
  - answer: `45 cells, e.g. ['Purchasers!AB131', 'Purchasers!AB133', 'Purchasers!AC131']`; cell `Purchasers!R131`

- [ ] **q6** (hardcode) Consider the range Purchasers!E34:P34. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Purchasers!E34', 'Purchasers!G34', 'Purchasers!I34', 'Purchasers!K34', 'Purchasers!M34']`; cell `Purchasers!E34`

## dev_e_pos_check (enron: `matt_motley__26384__Pos_Check.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Total', column headed 'Total 2007', in the sheet 'THURS_Peak_Pos_TieOut'?
  - answer: `-843753.75`; cell `THURS_Peak_Pos_TieOut!CG2`
  - read: THURS_Peak_Pos_TieOut!C2 = 'Total'; THURS_Peak_Pos_TieOut!CG1 = 'Total 2007'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Total', column headed 'Total 2001', in the sheet 'THURS_Peak_Pos_TieOut'? Give its cell address.
  - answer: `THURS_Peak_Pos_TieOut!G2`; cell `THURS_Peak_Pos_TieOut!G2`
  - read: THURS_Peak_Pos_TieOut!C2 = 'Total'; THURS_Peak_Pos_TieOut!G1 = 'Total 2001'

- [ ] **q3** (trace) Consider the cell THURS_Peak_Pos_TieOut!BV36 (in the row labelled 'SP15'). List the cells its formula reads directly (not indirectly).
  - answer: `['THURS_Peak_Pos_TieOut!BV28', 'THURS_Peak_Pos_TieOut!BV6']`; cell `THURS_Peak_Pos_TieOut!BV36`
  - formula: `=BV6-BV28`

- [ ] **q4** (trace) Consider the cell THURS_Peak_Pos_TieOut!HP34 (in the row labelled 'NP15'). List the cells its formula reads directly (not indirectly).
  - answer: `['THURS_Peak_Pos_TieOut!HP26', 'THURS_Peak_Pos_TieOut!HP4']`; cell `THURS_Peak_Pos_TieOut!HP34`
  - formula: `=HP4-HP26`

- [ ] **q5** (impact) Suppose the number in THURS_Peak_Pos_TieOut!AR14 (in the row labelled 'WSCC-N') were 10% higher. List every other cell whose value would change.
  - answer: `['THURS_Peak_Pos_TieOut!AR29', 'THURS_Peak_Pos_TieOut!AR37']`; cell `THURS_Peak_Pos_TieOut!AR14`

- [ ] **q6** (hardcode) Consider the range THURS_Peak_Pos_TieOut!EU25:EU30. List the cells that hold typed-in numbers rather than formulas.
  - answer: `[]`; cell `THURS_Peak_Pos_TieOut!EU25`

## dev_e_presentation (enron: `gstorey__12007__Presentation.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled '*Others', column headed 'Current Inventory', in the sheet 'Storage'?
  - answer: `-29.032451172598307`; cell `Storage!C7`
  - read: Storage!A7 = '*Others'; Storage!C2 = 'Current Inventory'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Aitken Creek', column headed '% Full 28-March-01', in the sheet 'Storage'? Give its cell address.
  - answer: `Storage!D23`; cell `Storage!D23`
  - read: Storage!A23 = 'Aitken Creek'; Storage!D16 = '% Full 28-March-01'

- [ ] **q3** (trace) Consider the cell Locations!P63. List the cells its formula reads directly (not indirectly).
  - answer: `['Locations!B63', 'Locations!J63']`; cell `Locations!P63`
  - formula: `=B63-J63`

- [ ] **q4** (trace) Consider the cell FR!D581. List the cells its formula reads directly (not indirectly).
  - answer: `['FR!C216', 'FR!C581']`; cell `FR!D581`
  - formula: `=C581-C216`

- [ ] **q5** (impact) Suppose the number in FR!B267 were 10% higher. List every other cell whose value would change.
  - answer: `120 cells, e.g. ['FR!C267', 'FR!C268', 'FR!C269']`; cell `FR!B267`

- [ ] **q6** (hardcode) Consider the range Forecast!C31:N31. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Forecast!K31']`; cell `Forecast!C31`

## dev_e_reliant (enron: `michelle_lokay__26675__Reliant.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'Difference to Model Calculation', in the sheet 'Deal'?
  - answer: `81326.86651950433`; cell `Deal!O48`
  - read: Deal!M48 = 'Difference to Model Calculation'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Commodity Costs per CBS', in the sheet 'Max Rates'? Give its cell address.
  - answer: `Max Rates!O47`; cell `Max Rates!O47`
  - read: Max Rates!M47 = 'Commodity Costs per CBS'

- [ ] **q3** (trace) Consider the cell Deal!G34. List the cells its formula reads directly (not indirectly).
  - answer: `['Deal!B34', 'Deal!C34', 'Deal!D34', 'Deal!E34', 'Deal!F34']`; cell `Deal!G34`
  - formula: `=(B34-C34-D34-E34)*F34`

- [ ] **q4** (trace) Consider the cell Deal!O37. List the cells its formula reads directly (not indirectly).
  - answer: `['Deal!L37', 'Deal!M37']`; cell `Deal!O37`
  - formula: `=M37*L37`

- [ ] **q5** (impact) Suppose the number in Deal!M28 were 10% higher. List every other cell whose value would change.
  - answer: `['Deal!O28', 'Deal!O38', 'Deal!O46', 'Deal!O48', 'Deal!Q28', 'Deal!Q38']`; cell `Deal!M28`

- [ ] **q6** (hardcode) Consider the range Deal!B7:J7. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Deal!B7', 'Deal!C7', 'Deal!E7', 'Deal!F7', 'Deal!H7', 'Deal!I7']`; cell `Deal!B7`

## dev_e_rfp_loadprofiles_193_151_202_141_113_110 (enron: `kim_ward__20771__RFP_loadprofiles_193_151_202_141_113_110.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'La Mirada, CA', column headed 'Total', in the sheet 'Load Profiles'?
  - answer: `807200`; cell `Load Profiles!P29`
  - read: Load Profiles!A29 = 'La Mirada, CA'; Load Profiles!P28 = 'Total '

- [ ] **q2** (address) Which cell holds the value in the row labelled 'GTF-3D', column headed 'Total', in the sheet 'Load Profiles'? Give its cell address.
  - answer: `Load Profiles!P53`; cell `Load Profiles!P53`
  - read: Load Profiles!C53 = 'GTF-3D'; Load Profiles!P51 = 'Total '

- [ ] **q3** (trace) Consider the cell Load Profiles!P10 (in the row labelled 'GTF3D'). List the cells its formula reads directly (not indirectly).
  - answer: `12 cells, e.g. ['Load Profiles!D10', 'Load Profiles!E10', 'Load Profiles!F10']`; cell `Load Profiles!P10`
  - formula: `=SUM(D10:O10)`

- [ ] **q4** (trace) Consider the cell Load Profiles!D13 (in the row labelled 'Total'). List the cells its formula reads directly (not indirectly).
  - answer: `10 cells, e.g. ['Load Profiles!D10', 'Load Profiles!D11', 'Load Profiles!D12']`; cell `Load Profiles!D13`
  - formula: `=SUM(D3:D12)`

- [ ] **q5** (impact) Suppose the number in Load Profiles!M3 (in the row labelled 'GTF3D') were 10% higher. List every other cell whose value would change.
  - answer: `['Load Profiles!M13', 'Load Profiles!M58', 'Load Profiles!P13', 'Load Profiles!P3', 'Load Profiles!P58']`; cell `Load Profiles!M3`

- [ ] **q6** (hardcode) Consider the range Load Profiles!D45:P45 (the row of 'GT-I'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `12 cells, e.g. ['Load Profiles!D45', 'Load Profiles!E45', 'Load Profiles!F45']`; cell `Load Profiles!D45`

## dev_e_tsc_calculator_2000_11 (enron: `larry_campbell__21439__TSC Calculator 2000 11.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'ASTORIA 5-9____', column headed 'PJM $/Mwhr', in the sheet 'Summary'?
  - answer: `4.49`; cell `Summary!F24`
  - read: Summary!B24 = 'ASTORIA 5-9____        '; Summary!F1 = 'PJM $/Mwhr'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'ALBANY___3', column headed 'OH $/Mwhr', in the sheet 'Summary'? Give its cell address.
  - answer: `Summary!E15`; cell `Summary!E15`
  - read: Summary!B15 = 'ALBANY___3             '; Summary!E1 = 'OH $/Mwhr'

- [ ] **q3** (trace) Consider the cell Calculator!F15 (in the row labelled 'NYPA'). List the cells its formula reads directly (not indirectly).
  - answer: `['Calculator!D15', 'Calculator!F2']`; cell `Calculator!F15`
  - formula: `=-D15*$F$2`

- [ ] **q4** (trace) Consider the cell Stripped!I258 (in the row labelled 'NIAGARA MOHAWK'). List the cells its formula reads directly (not indirectly).
  - answer: `['Stripped!F258', 'Stripped!H258']`; cell `Stripped!I258`
  - formula: `=+H258*F258`

- [ ] **q5** (impact) Suppose the number in Stripped!G256 (in the row labelled 'NYPA') were 10% higher. List every other cell whose value would change.
  - answer: `['Calculator!D11', 'Calculator!D16', 'Stripped!G277']`; cell `Stripped!G256`

- [ ] **q6** (hardcode) Consider the range Stripped!F256:I256 (the row of 'NYPA'). List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Stripped!F256', 'Stripped!G256', 'Stripped!H256']`; cell `Stripped!F256`

## dev_e_twftctrcs9_17_01 (enron: `shelley_corman__38742__TWFTCtrcs9-17-01.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'SJ', column headed 'Ctrc #', in the sheet 'ROFR Criteria'?
  - answer: `27496`; cell `ROFR Criteria!F10`
  - read: ROFR Criteria!D10 = 'SJ'; ROFR Criteria!F8 = 'Ctrc #'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Reliant', in the sheet 'WOT by Month with Red Rock'? Give its cell address.
  - answer: `WOT by Month with Red Rock!C39`; cell `WOT by Month with Red Rock!C39`
  - read: WOT by Month with Red Rock!B39 = 'Reliant'

- [ ] **q3** (trace) Consider the cell WOT by Month with Red Rock!AW81 (in the row labelled 'Subscribed Capacity'). List the cells its formula reads directly (not indirectly).
  - answer: `['WOT by Month with Red Rock!AW52', 'WOT by Month with Red Rock!AW69']`; cell `WOT by Month with Red Rock!AW81`
  - formula: `=AW69+AW52`

- [ ] **q4** (trace) Consider the cell WOT by Month with Red Rock!R69 (in the row labelled 'SUBSCRIBED RED ROCK'). List the cells its formula reads directly (not indirectly).
  - answer: `9 cells, e.g. ['WOT by Month with Red Rock!R59', 'WOT by Month with Red Rock!R60', 'WOT by Month with Red Rock!R61']`; cell `WOT by Month with Red Rock!R69`
  - formula: `=SUM(R59:R67)`

- [ ] **q5** (impact) Suppose the number in WOT by Month with Red Rock!AY10 (in the row labelled 'yes') were 10% higher. List every other cell whose value would change.
  - answer: `11 cells, e.g. ['WOT by Month with Red Rock!AY46', 'WOT by Month with Red Rock!AY48', 'WOT by Month with Red Rock!AY52']`; cell `WOT by Month with Red Rock!AY10`

- [ ] **q6** (hardcode) Consider the range WOT by Month!AM43:AM46. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['WOT by Month!AM43', 'WOT by Month!AM44', 'WOT by Month!AM45']`; cell `WOT by Month!AM43`

## dev_e_weekly_price_sheet_01_03_02 (enron: `mike_swerzbin__28058__Weekly Price Sheet 01 03 02.xlsx`)

- [ ] **q1** (lookup) What is the value in the row labelled 'This Week's Peak Power Prices', column headed 'SoCal + 0.41', in the sheet 'Term Prices'?
  - answer: `3.1950000000000003`; cell `Term Prices!BI10`
  - read: Term Prices!AJ10 = "This Week's Peak Power Prices"; Term Prices!BI2 = 'SoCal + 0.41'

- [ ] **q2** (address) Which cell holds the value in the row labelled 'Rockies', column headed 'Malin', in the sheet 'Term Prices'? Give its cell address.
  - answer: `Term Prices!BF20`; cell `Term Prices!BF20`
  - read: Term Prices!AJ20 = 'Rockies'; Term Prices!BF2 = 'Malin'

- [ ] **q3** (trace) Consider the cell Term Prices!BE201. List the cells its formula reads directly (not indirectly).
  - answer: `['Term Prices!AW201', 'Term Prices!AX201', 'Term Prices!BE1']`; cell `Term Prices!BE201`
  - formula: `=$AW201+$AX201+$BE$1`

- [ ] **q4** (trace) Consider the cell Term Prices!BE89. List the cells its formula reads directly (not indirectly).
  - answer: `['Term Prices!AW89', 'Term Prices!AX89', 'Term Prices!BE1']`; cell `Term Prices!BE89`
  - formula: `=$AW89+$AX89+$BE$1`

- [ ] **q5** (impact) Suppose the number in Term Prices!AP14 (in the row labelled 'COB') were 10% higher. List every other cell whose value would change.
  - answer: `['Term Prices!Q14', 'Term Prices!Q25', 'Term Prices!R14', 'Term Prices!R25']`; cell `Term Prices!AP14`

- [ ] **q6** (hardcode) Consider the range Term Prices!AO37:AO45. List the cells that hold typed-in numbers rather than formulas.
  - answer: `['Term Prices!AO38', 'Term Prices!AO39', 'Term Prices!AO40', 'Term Prices!AO41', 'Term Prices!AO42', 'Term Prices!AO43', 'Term Prices!AO44', 'Term Prices!AO45']`; cell `Term Prices!AO37`

