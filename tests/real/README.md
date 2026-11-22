# Real-world workbooks for the round-trip tests

`test_real_corpus.py` round-trips these (encode, decode to `.xlsx`, encode again) and checks cells, formulas and
typed values survive. Every committed file comes from a publisher whose licence allows redistribution; see
`manifest.json` for the source URL, licence and SHA-256 of each.

| Source | Licence | Files |
|---|---|---|
| BEA, IRS, Census | US federal government work, public domain | `bea_*`, `irs_*`, `census_*` |
| World Bank Open Data | CC BY 4.0 (attribution: The World Bank, GDP indicator NY.GDP.MKTP.CD) | `worldbank_gdp.xlsx` |
| Northern Ireland departments, NHS trusts, Stockport MBC and similar | Open Government Licence v3.0, as declared in the data.gov.uk catalogue | `ogl*` |

Files that were `.xls` at the source were converted to `.xlsx` with LibreOffice (`converted_from_xls` in the manifest).

**Not committed:** the Damodaran (NYU Stern) workbooks have no explicit licence. The five native `.xlsx` ones are in
`manifest.json` under `fetch`. Set `CELLPROSE_FETCH_REAL=1` to download them at test time (checked against the
SHA-256, cached in `.pytest_cache`); without it those tests are skipped. Also left out: files over about 250 KB, and
`ogl11`/`ogl15`, whose catalogue entries name no licence.

Files in this folder are third-party data. Treat them as untrusted input.
