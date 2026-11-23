# Income reference: Statistics South Africa (for the researcher to review)

`income_reference_statssa.csv` contains **median monthly earnings of employees, 2024** from:

> Statistics South Africa. 2024. *Labour Market Dynamics in South Africa, 2024*. Report 02-11-02 (2024).
> Pretoria: Statistics South Africa. ISBN 978-1-83491-516-6.
> https://www.statssa.gov.za/publications/Report-02-11-02/Report-02-11-022024.pdf
> Section 4.3, "Median monthly earnings of employees" (printed page 64; PDF page 65), text paragraph and Table 4.14.

## How these figures were obtained
Extracted from the text layer of the PDF on 2026-10-05. Only values that
appear as text in the report are included. Both-sexes values for Clerk and the lower groups appear only in
the chart (Figure 4.30), not as text, so they are left blank. **Check every figure against the PDF before
use.**

## How to use (researcher)
1. Map each occupation in `data/skill_map.csv` to its major occupation group (OFO/ISCO major group:
   Manager, Professional, Technician, Clerk, ...). That mapping is your decision; record it in DECISIONS.md.
2. Copy the `suggested_income_estimate` text of that group into the occupation's `income_estimate` cell, and
   add the citation above to its `source` cell (or a separate note).
3. SkillPath (version A) then shows: `Estimated R25 000 per month (2024 median for Professionals)
   (literature-derived estimate, not financial advice)`.

## Limitations to report
- Figures are medians for **all employees** in each broad occupation group, not for specific occupations
  and not for entry-level graduates. For context, the overall median for employees aged 25–34 was R5 600
  (Table 4.12), against R6 000 for all ages.
- Occupations in the same group get the same figure, so income in version A cannot separate them.
- QLFS earnings data have known limitations (e.g. non-response and imputation), see Kerr (2026),
  *South African Journal of Economics*, https://doi.org/10.1111/saje.70031
- The engine never uses income for ranking (DD9); this file is reference material only and is not read by
  any code.
