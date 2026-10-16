"""SkillPath design constants.

These values are design settings of the artefact and are measured by the DSR
evaluation. They MUST match the constants in run_synthetic_tests.py and
analyse_outputs.py (tests/test_config.py checks this).
"""

# DD2 Adjacency prioritisation: number of nearest occupations (by Jaccard
# similarity) whose skills form the candidate set.
K = 3

# DD4 Short units: number of modules in a pathway (= run_synthetic_tests.STEADY_MODULES).
MODULES = 6

# DD4 Short units: every module takes 5 to 10 minutes. Estimated minutes are
# derived from difficulty: difficulty 1 -> 5 min ... difficulty 5 -> 9 min.
MODULE_MIN_MINUTES = 5
MODULE_MAX_MINUTES = 10

# DD5 Visible milestones: a milestone (MS1, MS2, ...) is awarded every 3rd pass.
MODULES_PER_MILESTONE = 3

# DD3 Calibrate difficulty: after every 2nd pass, difficulty rises by 1.
PASSES_PER_DIFFICULTY_STEP = 2

# DD3 Calibrate difficulty: the roadmap is revised (difficulty lowered by 1)
# on the 2nd consecutive failure, never the 1st.
FAILS_BEFORE_REVISION = 2

# DD7 Trigger timing: nudge when the user has been inactive this many days.
INACTIVE_DAYS_NUDGE = 2

# DD7 Trigger timing: stop nudging after this many consecutive unopened nudges, until the user returns
# (opening a nudge or any activity resets the count). Avoids repeated unwelcome prompts (Fogg, 2003).
MAX_UNOPENED_NUDGES = 3

# DD3 Calibrate difficulty: difficulty scale (= analyse_outputs.MIN_DIFFICULTY).
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5

# DD3 Calibrate difficulty: starting difficulty by self-rated competency level.
# Any other value is treated as DEFAULT_COMPETENCY.
START_LEVELS = {"limited": 1, "foundational": 2, "moderate": 3}
DEFAULT_COMPETENCY = "foundational"

# DD8 Transparency: disclaimer appended to every explanation.
DISCLAIMER = ("AI-generated suggestion based on published labour-market literature. "
              "Not professional career or financial advice.")

# DD9 Income as information: label applied to income shown in version A.
INCOME_TEMPLATE = "Estimated {income} (literature-derived estimate, not financial advice)"

# Logic versions: A = income-visible, B = income-neutral.
INCOME_VISIBLE_VERSION = "A"

# Skill profiling layer: CV skill extraction (skillpath/cv.py).
# Locally hosted sentence-embedding model (Apache-2.0), run offline via fastembed/ONNX.
CV_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Minimum cosine similarity between a CV phrase and a skill for the skill to be proposed.
# Proposals are always confirmed by the user; tune with care and record changes in DECISIONS.md.
CV_MATCH_THRESHOLD = 0.55
# At most this many proposed skills are shown, highest similarity first.
CV_MAX_SKILLS = 25
