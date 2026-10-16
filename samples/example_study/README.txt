EXAMPLE - NOT STUDY DATA

Worked example of the Phase 3 study inputs, created with AI assistance as a teaching exemplar.
It is NOT a student's research data and must not be submitted or reported as findings.

profiles_EXAMPLE.csv  28 profiles (24-cell design matrix + 4 edge cases) using SkillPath's skill names
cvs/                  one fictional CV per profile and expected_skills.csv

Try it (from the repository folder):
  .venv\Scripts\python scripts\cv_accuracy.py samples\example_study\cvs
  .venv\Scripts\python run_evaluation.py samples\example_study\profiles_EXAMPLE.csv --label EXAMPLE --out-dir samples\example_study\runs --allow-dirty

How a student builds their own: profiles\profile_builder.xlsx (see its Guide sheet) and
profiles\cv_template\CV_TEMPLATE.docx, then scripts\profiles_from_builder.py.
