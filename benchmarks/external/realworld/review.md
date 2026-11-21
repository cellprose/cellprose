# Review record

Every question below was read against the cells around its answer by one reviewer (Claude) in one pass, after the builder's own checks passed (unique key, usable answer, ground truth computed from the file). `labels` are the cells that name the row and column. Limits: one reviewer, no second pass, no domain expert for the Damodaran models.

## rw_irs_soi

- **q1** (lookup) In IRS Table 1.1 (sheet TBL11), how many 'All returns' (number of returns) are in the '$50,000 under $75,000' size of adjusted gross income class?
  - answer: `22602996`; cell `TBL11!B20`
  - read: TBL11!A20 = '$50,000 under $75,000'; TBL11!B4 = 'Number\nof\nreturns'; TBL11!B3 = 'All returns'

- **q2** (lookup) In IRS Table 1.1 (sheet TBL11), what is the taxable income amount for the '$100,000 under $200,000' size of adjusted gross income class?
  - answer: `2458885718`; cell `TBL11!L22`
  - read: TBL11!A22 = '$100,000 under $200,000'; TBL11!K4 = 'Taxable income'; TBL11!L5 = 'Amount'

- **q3** (address) Which cell holds the average total income tax (dollars) for the '$10,000,000 or more' size of adjusted gross income class (first block of the table, 'Size of adjusted gross income')? Give its cell address.
  - answer: `TBL11!U29`; cell `TBL11!U29`
  - read: TBL11!A29 = '$10,000,000 or more'; TBL11!U5 = 'Average\ntotal income \ntax (dollars)'

- **q4** (trace) Consider the average total income tax (dollars) for the '$2,000,000 under $5,000,000' class. List the cells its formula reads directly (not indirectly).
  - answer: `['TBL11!G27', 'TBL11!Q27']`; cell `TBL11!U27`
  - read: TBL11!A27 = '$2,000,000 under $5,000,000'; TBL11!U5 = 'Average\ntotal income \ntax (dollars)'

- **q5** (impact) Suppose the number of taxable returns in the '$1,500,000 under $2,000,000' class were 10% higher. List every other cell whose value would change.
  - answer: `['TBL11!U26']`; cell `TBL11!G26`
  - read: TBL11!A26 = '$1,500,000 under $2,000,000'; TBL11!G4 = 'Number\nof\nreturns'

## rw_census_nrc

- **q1** (lookup) In the sheet 'Table 1 - Permits', Table 1a (seasonally adjusted annual rate, thousands of units), what is the United States total for March 2023?
  - answer: `1437`; cell `Table 1 - Permits!B14`
  - read: Table 1 - Permits!A11 = '2023'; Table 1 - Permits!A14 = 'March . . . . . . . . . . . . . . . . . . . . . . . . . . . '; Table 1 - Permits!A4 = 'Table 1a - Seasonally adjusted annual rate'; Table 1 - Permits!B5 = 'United States'; Table 1 - Permits!B6 = 'Total'

- **q2** (lookup) In the sheet 'Table 3 - Starts', Table 3a (seasonally adjusted annual rate), how many 1-unit housing units were started in the South in February 2023?
  - answer: `514`; cell `Table 3 - Starts!K13`
  - read: Table 3 - Starts!A11 = '2023'; Table 3 - Starts!A13 = 'February . . . . . . . . . . . . . . . . . . . . . . . . . .'; Table 3 - Starts!J5 = 'South'; Table 3 - Starts!K6 = '1 unit'

- **q3** (address) In the sheet 'Table 1 - Permits', Table 1a, which cell holds the West total for May 2023? Give its cell address.
  - answer: `Table 1 - Permits!L16`; cell `Table 1 - Permits!L16`
  - read: Table 1 - Permits!A16 = 'May . . . . . . . . . . . . . . . . . . . . . . . . . . . . '; Table 1 - Permits!L5 = 'West'; Table 1 - Permits!L6 = 'Total'

- **q4** (lookup) In the sheet 'Table 1 - Permits', Table 1a, how many permits for 5 units or more were issued in the United States in April 2023?
  - answer: `503`; cell `Table 1 - Permits!E15`
  - read: Table 1 - Permits!A15 = 'April . . . . . . . . . . . . . . . . . . . . . . . . . . . '; Table 1 - Permits!E5 = 'None'; Table 1 - Permits!E6 = '5 units\n or more'

- **q5** (lookup) In the sheet 'Table 1 - Permits', under Percent Change, what is the United States total change of December 2023 from December 2022 (as the decimal fraction stored in the cell)?
  - answer: `0.061`; cell `Table 1 - Permits!B29`
  - read: Table 1 - Permits!A29 = 'Dec. 2023 from Dec. 2022 . . . . . . . . . . . . . . . . . .'; Table 1 - Permits!B5 = 'United States'; Table 1 - Permits!B6 = 'Total'

## rw_bea_gdp

- **q1** (lookup) In BEA Table 1 (Real Gross Domestic Product: percent change), what is the percent change for Gross domestic product (GDP), line 1, in the 2022 column?
  - answer: `2.1`; cell `Table 1!E5`
  - read: Table 1!B5 = 'Gross domestic product (GDP)'; Table 1!E2 = '2022 r'

- **q2** (lookup) In BEA Table 1, what is the percent change in Residential fixed investment (line 13) for 2021?
  - answer: `10.7`; cell `Table 1!D17`
  - read: Table 1!B17 = 'Residential'; Table 1!D2 = '2021'

- **q3** (lookup) In BEA Table 1, what is the 2022 percent change for exports of services (line 18, the Services row under Exports)?
  - answer: `8.7`; cell `Table 1!E22`
  - read: Table 1!B22 = 'Services'; Table 1!E2 = '2022 r'; Table 1!B20 = 'Exports'

- **q4** (address) In BEA Table 1, which cell holds the seasonally adjusted annual rate for Personal consumption expenditures (line 2) in the second quarter of 2020? Give its cell address.
  - answer: `Table 1!K6`; cell `Table 1!K6`
  - read: Table 1!B6 = 'Personal consumption expenditures'; Table 1!J3 = '2020'; Table 1!K4 = 'Q2'

## rw_worldbank_gdp

- **q1** (lookup) In the 'Data' sheet, what is GDP (current US$) for Germany in 2022?
  - answer: `4201021706478.62`; cell `Data!BO60`
  - read: Data!A60 = 'Germany'; Data!BO4 = '2022'

- **q2** (lookup) In the 'Data' sheet, what is GDP (current US$) for Japan in 2021?
  - answer: `5225933520753.1`; cell `Data!BN124`
  - read: Data!A124 = 'Japan'; Data!BN4 = '2021'

- **q3** (address) Which cell holds GDP (current US$) for India in 2023 in the 'Data' sheet? Give its cell address.
  - answer: `Data!BP114`; cell `Data!BP114`
  - read: Data!A114 = 'India'; Data!BP4 = '2023'

- **q4** (lookup) In the 'Data' sheet, what is GDP (current US$) for Kenya in 2022?
  - answer: `114448978152.637`; cell `Data!BO126`
  - read: Data!A126 = 'Kenya'; Data!BO4 = '2022'

## rw_dam_fcffginzu

- **q1** (lookup) In the sheet 'Valuation Model', what is the 'Value of equity per share'?
  - answer: `377.1402170197516`; cell `Valuation Model!F71`
  - read: Valuation Model!B71 = 'Value of equity per share ='

- **q2** (lookup) In the sheet 'Valuation Model', what is the 'Cost of Capital in Stable Phase'?
  - answer: `0.08300988545867843`; cell `Valuation Model!D58`
  - read: Valuation Model!B58 = 'Cost of Capital in Stable Phase ='

- **q3** (address) In the sheet 'Valuation Model', which cell holds the present value of the terminal value of the firm (the row that starts 'Present Value of Terminal Value')? Give its cell address.
  - answer: `Valuation Model!F62`; cell `Valuation Model!F62`
  - read: Valuation Model!B62 = 'Present Value of Terminal Value of Firm ='

- **q4** (trace) Consider 'Market Value of Equity =' in the sheet 'Valuation Model'. List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation Model!F65', 'Valuation Model!F66', 'Valuation Model!F67']`; cell `Valuation Model!F68`
  - read: Valuation Model!B68 = 'Market Value of Equity ='

- **q5** (trace) Consider '% Under or Over valued =' in the sheet 'Valuation Model'. List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation Model!F71', 'Valuation Model!F72']`; cell `Valuation Model!F73`
  - read: Valuation Model!B73 = '% Under or Over valued ='

- **q6** (impact) Suppose the number of shares outstanding in 'Master Inputs Start here' (cell B32) were 10% higher. List every other cell whose value would change.
  - answer: `68 cells, e.g. ['Cost of capital worksheet!B38', 'Cost of capital worksheet!B39', 'Cost of capital worksheet!B4']`; cell `Master Inputs Start here!B32`
  - read: Master Inputs Start here!A32 = 'Number of shares outstanding ='

## rw_dam_fcffsimpleginzu

- **q1** (lookup) In the sheet 'Valuation output', what is the 'Estimated value /share'?
  - answer: `7.187840270062114`; cell `Valuation output!B33`
  - read: Valuation output!A33 = 'Estimated value /share'

- **q2** (lookup) In the sheet 'Valuation output', what is 'PV (CF over next 10 years)'?
  - answer: `16394.53892909532`; cell `Valuation output!B20`
  - read: Valuation output!A20 = 'PV (CF over next 10 years)'

- **q3** (address) In the sheet 'Valuation output', which cell holds 'Value of equity in common stock'? Give its cell address.
  - answer: `Valuation output!B31`; cell `Valuation output!B31`
  - read: Valuation output!A31 = 'Value of equity in common stock'

- **q4** (trace) Consider 'Value of equity' in the sheet 'Valuation output'. List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation output!B24', 'Valuation output!B25', 'Valuation output!B26', 'Valuation output!B27', 'Valuation output!B28']`; cell `Valuation output!B29`
  - read: Valuation output!A29 = 'Value of equity'

- **q5** (trace) Consider 'Price as % of value' in the sheet 'Valuation output'. List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation output!B33', 'Valuation output!B34']`; cell `Valuation output!B35`
  - read: Valuation output!A35 = 'Price as % of value'

- **q6** (impact) Suppose the number of shares outstanding in 'Input sheet' (cell B18) were 10% higher. List every other cell whose value would change.
  - answer: `102 cells, e.g. ['Cost of capital worksheet!B13', 'Cost of capital worksheet!B18', 'Cost of capital worksheet!B60']`; cell `Input sheet!B21`
  - read: Input sheet!A21 = 'Number of shares outstanding ='

## rw_dam_fcffsimpleginzucorona

- **q1** (lookup) In the sheet 'Valuation output', what is the 'Estimated value /share'?
  - answer: `88.68783748258801`; cell `Valuation output!B33`
  - read: Valuation output!A33 = 'Estimated value /share'

- **q2** (lookup) In the sheet 'Valuation output', what is the 'Value of operating assets'?
  - answer: `68699.31601514481`; cell `Valuation output!B24`
  - read: Valuation output!A24 = 'Value of operating assets ='

- **q3** (address) In the sheet 'Valuation output', which cell holds the 'Terminal value'? Give its cell address.
  - answer: `Valuation output!B18`; cell `Valuation output!B18`
  - read: Valuation output!A18 = 'Terminal value'

- **q4** (trace) Consider 'Terminal value' in the sheet 'Valuation output'. List the cells its formula reads directly (not indirectly).
  - answer: `['Valuation output!B16', 'Valuation output!B17', 'Valuation output!M2']`; cell `Valuation output!B18`
  - read: Valuation output!A18 = 'Terminal value'

- **q5** (impact) Suppose the number of shares outstanding in 'Input sheet' (cell B18) were 10% higher. List every other cell whose value would change.
  - answer: `98 cells, e.g. ['Cost of capital worksheet!B48', 'Cost of capital worksheet!B49', 'Cost of capital worksheet!B50']`; cell `Input sheet!B18`
  - read: Input sheet!A18 = 'Number of shares outstanding ='

## rw_dam_capstru

- **q1** (lookup) In the sheet 'Optimal CS Worksheet', what is the current WACC (the 'Current' column of the row labelled WACC)?
  - answer: `0.09567120276370804`; cell `Optimal CS Worksheet!E19`
  - read: Optimal CS Worksheet!C19 = 'WACC'; Optimal CS Worksheet!E11 = 'Current'

- **q2** (lookup) In the sheet 'Optimal CS Worksheet', what is the optimal enterprise value (the 'Optimal' column of the row labelled 'Enterprise value')?
  - answer: `218233.40818955714`; cell `Optimal CS Worksheet!F21`
  - read: Optimal CS Worksheet!C21 = 'Enterprise value '; Optimal CS Worksheet!F11 = 'Optimal'

- **q3** (address) In the sheet 'Optimal CS Worksheet', which cell holds the current 'Rating on Debt'? Give its cell address.
  - answer: `Optimal CS Worksheet!E16`; cell `Optimal CS Worksheet!E16`
  - read: Optimal CS Worksheet!C16 = 'Rating on Debt'; Optimal CS Worksheet!E11 = 'Current'

- **q4** (trace) Consider the current 'Cost of Equity' in the sheet 'Optimal CS Worksheet'. List the cells its formula reads directly (not indirectly).
  - answer: `['Optimal CS Worksheet!C8', 'Optimal CS Worksheet!F4', 'Optimal CS Worksheet!F7']`; cell `Optimal CS Worksheet!E15`
  - read: Optimal CS Worksheet!C15 = 'Cost of Equity    ='

- **q5** (trace) Consider the 'Change' column of the 'D/(D+E) Ratio' row in the sheet 'Optimal CS Worksheet'. List the cells its formula reads directly (not indirectly).
  - answer: `['Optimal CS Worksheet!E12', 'Optimal CS Worksheet!F12']`; cell `Optimal CS Worksheet!G12`
  - read: Optimal CS Worksheet!C12 = 'D/(D+E) Ratio ='; Optimal CS Worksheet!G11 = 'Change'

## rw_ogl00_rail_codes

- **q1** (lookup) In the sheet 'Sheet2', for the row where 'Name' is 'Coleraine', what is the value of 'Easting'?
  - answer: `285370`; cell `Sheet2!H16`
  - read: Sheet2!E16 = 'Coleraine'; Sheet2!H16 = '285370'; Sheet2!H1 = 'Easting'

- **q2** (lookup) In the sheet 'Sheet2', for the row where 'Name' is 'Lisburn', what is the value of 'Northing'?
  - answer: `364591`; cell `Sheet2!I39`
  - read: Sheet2!E39 = 'Lisburn'; Sheet2!I39 = '364591'; Sheet2!I1 = 'Northing'

- **q3** (address) In the sheet 'Sheet2', which cell holds 'Easting' for the row where 'Name' is 'Seahill'? Give its cell address.
  - answer: `Sheet2!H58`; cell `Sheet2!H58`
  - read: Sheet2!E58 = 'Seahill'; Sheet2!H58 = '344061'; Sheet2!H1 = 'Easting'

## rw_ogl01_dof_payments

- **q1** (lookup) In the sheet 'Page1', for the row where 'Invoice number' is 'INV00019126545', what is the value of 'Invoice Amount'?
  - answer: `151200`; cell `Page1!G23`
  - read: Page1!F23 = 'INV00019126545'; Page1!G23 = '151200'; Page1!G1 = 'Invoice Amount'

- **q2** (lookup) In the sheet 'Page1', for the row where 'Invoice number' is 'LPSINV279', what is the value of 'Supplier'?
  - answer: `RED RIDGE SOLUTIONS LTD`; cell `Page1!E54`
  - read: Page1!F54 = 'LPSINV279'; Page1!E54 = 'RED RIDGE SOLUTIONS LTD'; Page1!E1 = 'Supplier'

- **q3** (address) In the sheet 'Page1', which cell holds 'Postcode' for the row where 'Invoice number' is 'SIN033553'? Give its cell address.
  - answer: `Page1!H86`; cell `Page1!H86`
  - read: Page1!F86 = 'SIN033553'; Page1!H86 = 'CB4 0WZ'; Page1!H1 = 'Postcode'

## rw_ogl04_doh_payments

- **q1** (lookup) In the sheet 'For upload', for the row where 'Invoice number' is 5190040, what is the value of 'Invoice Amount'?
  - answer: `2103091.25`; cell `For upload!G13`
  - read: For upload!F13 = '5190040'; For upload!G13 = '2103091.25'; For upload!G1 = 'Invoice Amount'

- **q2** (lookup) In the sheet 'For upload', for the row where 'Invoice number' is 16645298, what is the value of 'Supplier'?
  - answer: `SCOTTISH GOVERNMENT`; cell `For upload!E17`
  - read: For upload!F17 = '16645298'; For upload!E17 = 'SCOTTISH GOVERNMENT'; For upload!E1 = 'Supplier'

- **q3** (address) In the sheet 'For upload', which cell holds 'Postcode' for the row where 'Invoice number' is 'ARGI/00019766'? Give its cell address.
  - answer: `For upload!H29`; cell `For upload!H29`
  - read: For upload!F29 = 'ARGI/00019766'; For upload!H29 = 'W1G 0RN'; For upload!H1 = 'Postcode'

## rw_ogl05_purchase_orders

- **q1** (lookup) In the sheet 'Sheet 1', for the row where 'Purchase Order No' is 'ZZC657809', what is the value of 'Net Order Value Over £5000.00 (line item value shown here)'?
  - answer: `7985.17`; cell `Sheet 1!K104`
  - read: Sheet 1!B104 = 'ZZC657809'; Sheet 1!K104 = '7985.17'; Sheet 1!K1 = 'Net Order Value Over £5000.00 \n(line item value shown here)'

- **q2** (lookup) In the sheet 'Sheet 1', for the row where 'Purchase Order No' is 'ZZP656547', what is the value of 'Supplier Name'?
  - answer: `The Dodd Group`; cell `Sheet 1!E258`
  - read: Sheet 1!B258 = 'ZZP656547'; Sheet 1!E258 = 'The Dodd Group'; Sheet 1!E1 = 'Supplier Name'

- **q3** (address) In the sheet 'Sheet 1', which cell holds 'Pro Class Description' for the row where 'Purchase Order No' is 'ZZP658117'? Give its cell address.
  - answer: `Sheet 1!G418`; cell `Sheet 1!G418`
  - read: Sheet 1!B418 = 'ZZP658117'; Sheet 1!G418 = 'Information Communication Technology  '; Sheet 1!G1 = 'Pro Class Description'

## rw_ogl06_plymouth_spend

- **q1** (lookup) In the sheet 'BI report', for the row where 'Transaction Number' is 47168013, what is the value of 'AP Amount'?
  - answer: `1299775.98`; cell `BI report!H101`
  - read: BI report!G101 = '47168013'; BI report!H101 = '1299775.98'; BI report!H2 = 'AP Amount'

- **q2** (lookup) In the sheet 'BI report', for the row where 'Transaction Number' is 47248380, what is the value of 'Supplier'?
  - answer: `KNOWLEDGE ACADEMY LTD (THE)`; cell `BI report!F165`
  - read: BI report!G165 = '47248380'; BI report!F165 = 'KNOWLEDGE ACADEMY LTD (THE)'; BI report!F2 = 'Supplier'

- **q3** (address) In the sheet 'BI report', which cell holds 'Expense Type' for the row where 'Transaction Number' is 47401369? Give its cell address.
  - answer: `BI report!D262`; cell `BI report!D262`
  - read: BI report!G262 = '47401369'; BI report!D262 = 'Med & Surg Equip General'; BI report!D2 = 'Expense Type'

## rw_ogl07_export_establishments

- **q1** (lookup) In the sheet 'Sheet1', for the row where 'Country' is 'Czechia (CZ)' and 'SectorSection' is 'Composting Plants (ABP-COMP)', what is the value of 'Chapter'?
  - answer: `Animal By-Products `; cell `Sheet1!B174`
  - read: Sheet1!A174 = 'Czechia (CZ)'; Sheet1!C174 = 'Composting Plants (ABP-COMP)'; Sheet1!B174 = 'Animal By-Products '; Sheet1!B1 = 'Chapter'

- **q2** (lookup) In the sheet 'Sheet1', for the row where 'Country' is 'Ireland ROI (IE)' and 'SectorSection' is 'Composting plants (ABP-COMP)', what is the value of 'Chapter'?
  - answer: `Animal by-products`; cell `Sheet1!B433`
  - read: Sheet1!A433 = 'Ireland ROI (IE)'; Sheet1!C433 = 'Composting plants (ABP-COMP)'; Sheet1!B433 = 'Animal by-products'; Sheet1!B1 = 'Chapter'

- **q3** (address) In the sheet 'Sheet1', which cell holds 'Link' for the row where 'Country' is 'Romania (RO)' and 'SectorSection' is 'Eggs and egg products (EEP)'? Give its cell address.
  - answer: `Sheet1!D692`; cell `Sheet1!D692`
  - read: Sheet1!A692 = 'Romania (RO)'; Sheet1!C692 = 'Eggs and egg products (EEP)'; Sheet1!D692 = 'Establishment list - TRACES NT'; Sheet1!D1 = 'Link'

## rw_ogl12_purchase_cards

- **q1** (lookup) In the sheet 'NOV 18', for the row where 'Transaction Number' is 'GPC11180000060', what is the value of 'Net Amount (£)'?
  - answer: `5.4`; cell `NOV 18!J61`
  - read: NOV 18!I61 = 'GPC11180000060'; NOV 18!J61 = '5.4'; NOV 18!J1 = 'Net Amount (£)'

- **q2** (lookup) In the sheet 'NOV 18', for the row where 'Transaction Number' is 'GPC11180000150', what is the value of 'Supplier (Beneficiary)'?
  - answer: `ASDA STORES 4840`; cell `NOV 18!D151`
  - read: NOV 18!I151 = 'GPC11180000150'; NOV 18!D151 = 'ASDA STORES 4840'; NOV 18!D1 = 'Supplier (Beneficiary)'

- **q3** (address) In the sheet 'NOV 18', which cell holds 'Purpose of Expenditure' for the row where 'Transaction Number' is 'GPC11180000240'? Give its cell address.
  - answer: `NOV 18!E241`; cell `NOV 18!E241`
  - read: NOV 18!I241 = 'GPC11180000240'; NOV 18!E241 = 'Furniture and Equipment'; NOV 18!E1 = 'Purpose of Expenditure'

## rw_ogl13_worcs_spend

- **q1** (lookup) In the sheet 'Sheet1', for the row where 'Supplier Name' is 'INSIGHTS LEARNING & DEVELOPMENT LTD', what is the value of 'Expense Type'?
  - answer: `LEARNING & DEVELOPMENT`; cell `Sheet1!D12`
  - read: Sheet1!F12 = 'INSIGHTS LEARNING & DEVELOPMENT LTD'; Sheet1!D12 = 'LEARNING & DEVELOPMENT'; Sheet1!D3 = 'Expense Type'

- **q2** (lookup) In the sheet 'Sheet1', for the row where 'Supplier Name' is 'SOUTH WARWICKSHIRE AND WORCESTERSHIRE MIND LTD', what is the value of 'Expense Area'?
  - answer: `VARIOUS SITES`; cell `Sheet1!E28`
  - read: Sheet1!F28 = 'SOUTH WARWICKSHIRE AND WORCESTERSHIRE MIND LTD'; Sheet1!E28 = 'VARIOUS SITES'; Sheet1!E3 = 'Expense Area'

- **q3** (address) In the sheet 'Sheet1', which cell holds 'Expense Area' for the row where 'Supplier Name' is 'WORCESTER CITY COUNCIL'? Give its cell address.
  - answer: `Sheet1!E38`; cell `Sheet1!E38`
  - read: Sheet1!F38 = 'WORCESTER CITY COUNCIL'; Sheet1!E38 = 'VARIOUS SITES'; Sheet1!E3 = 'Expense Area'

## rw_ogl14_cornwall_spend

- **q1** (lookup) In the sheet 'January 26 for Publication', for the row where 'Transaction number' is '0010298776', what is the value of '£'?
  - answer: `46037.49`; cell `January 26 for Publication!H12`
  - read: January 26 for Publication!G12 = '0010298776'; January 26 for Publication!H12 = '46037.49'; January 26 for Publication!H1 = '£'

- **q2** (lookup) In the sheet 'January 26 for Publication', for the row where 'Transaction number' is '0015193430', what is the value of 'Supplier'?
  - answer: `NHS PROPERTY SERVICES LTD`; cell `January 26 for Publication!F28`
  - read: January 26 for Publication!G28 = '0015193430'; January 26 for Publication!F28 = 'NHS PROPERTY SERVICES LTD'; January 26 for Publication!F1 = 'Supplier'

- **q3** (address) In the sheet 'January 26 for Publication', which cell holds 'Expense type' for the row where 'Transaction number' is '0015193437'? Give its cell address.
  - answer: `January 26 for Publication!D43`; cell `January 26 for Publication!D43`
  - read: January 26 for Publication!G43 = '0015193437'; January 26 for Publication!D43 = 'LEASE NHSPS'; January 26 for Publication!D1 = 'Expense type'

