"""Refine the Part 3 exemplar (v2 -> v3): condense to the 4,000-6,000 word limit, add the PRISMA 2020 flow
diagram and a characteristics-of-included-studies table (Annexure B5), complete and verify references, and
apply the IIE format (Arial 12 pt, 1.5 line spacing, justified body, 2 cm margins).

    python scripts/update_exemplar.py <original EXEMPLAR.docx>     # builds v2 from the final runs
    python scripts/refine_exemplar.py                               # builds v3 from v2

Reference metadata was checked against Crossref (DOIs) and the original DHET, WEF and ESCO sources on
2026-10-16. Requires python-docx and matplotlib.
"""

import os
import re

import docx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "exemplar", "REIT8419_Part3_SkillPath_EXEMPLAR_v2.docx")
OUT = os.path.join(ROOT, "docs", "exemplar", "REIT8419_Part3_SkillPath_EXEMPLAR_v3.docx")
PRISMA_PNG = os.path.join(ROOT, "docs", "exemplar", "fig_prisma.png")

DELETE = ["Each sub-question maps to one DSR phase", "The two phases required different selection logics."]

R = {
    "Unemployed graduates in digitally disrupted labour markets face":
        "Unemployed graduates often do not know which skill to develop first, and completing a course does not "
        "automatically give them the confidence to apply it (Priyashantha, Dahanayake and Maduwanthi, 2023; White, "
        "Becker and Du Plessis, 2021). The research proposal framed SkillPath, an AI-powered mobile recommender, as a "
        "Design Science Research (DSR) artefact to be built and evaluated against the criteria of utility, quality and "
        "efficacy (Hevner et al., 2004).",
    "This document reports how that plan was carried out":
        "This document reports what was actually done, including where the plan changed and why. As approved in the "
        "ethics application (Annexure F), Phase 3 used controlled synthetic testing: researcher-built graduate "
        "profiles and fabricated CVs were fed into SkillPath in a fixed sequence and its outputs recorded. No real "
        "person took part, so every Phase 3 result describes system outputs, an artificial evaluation in Venable, "
        "Pries-Heje and Baskerville's (2016) terms. Section 2 defines the populations and sampling, Sections 3 and 4 "
        "describe data collection and analysis, Section 5 presents the findings, Section 6 interprets them and "
        "Section 7 answers the research questions.",
    "Three sub-questions divided this into answerable parts":
        "SQ1 asked which frameworks and findings were most relevant for design, and SQ2 how SkillPath could apply the "
        "derived principles. SQ3 was revised to match the approved evaluation design, because engagement cannot be "
        "measured without real users:",
    "The DSR structure produced two data streams":
        "The study drew on two data streams with different origins, published literature (Phase 1) and system "
        "outputs for synthetic profiles (Phase 3), so each population is defined separately.",
    "The target population for Phase 1 was the body":
        "The target population for Phase 1 was the peer-reviewed and institutional literature on the proposal's five "
        "pillars: adaptive and personalised learning; AI literacy; behavioural design; career development and "
        "direction clarity; and labour market demand and skill adjacency. The accessible population comprised "
        "English-language sources indexed in Google Scholar, IEEE Xplore, Scopus and PubMed, available in full text "
        "and published between 2015 and 2026. Seminal statements of the four underpinning theories were admitted "
        "regardless of date (Vygotsky, 1978; Deci and Ryan, 2000; Fogg, 2003; Hevner et al., 2004).",
    "The unit of analysis in Phase 1 was the individual source":
        "The unit of analysis was the individual source (Table 1).",
    "SkillPath was designed for unemployed and underemployed graduates":
        "SkillPath targets unemployed and underemployed South African graduates, among whom youth unemployment reached "
        "46.1% in early 2025 (Statistics South Africa, 2025) and among whom skill inequalities between faculties shape "
        "recruitment outcomes (Chigbu and Nekhwevha, 2022). The population is defined by a post-school qualification at "
        "NQF level 6 or above, an age of 18 to 34, unemployment or underemployment, and access to a smartphone.",
    "Because the evaluation involved no real people":
        "No members of this population were sampled. Instead, the range of starting positions SkillPath must handle "
        "was represented along three dimensions drawn from the research problem: competency level (limited, "
        "foundational, moderate), because the right next step depends on the starting point (Vygotsky, 1978); "
        "discipline (Commerce, Humanities, Natural Sciences, IT), because faculty-level inequalities imply uneven "
        "service (Chigbu and Nekhwevha, 2022); and employment goal (within field or pivot), because transition "
        "distance shapes how readily a move is made (Autor et al., 2024).",
    "The unit of analysis was the SkillPath artefact":
        "The unit of analysis was the SkillPath artefact (Hevner et al., 2004); the units of observation were its "
        "recorded responses to each profile under each logic version.",
    "Non-probability, purposive sampling was used for the literature":
        "Non-probability, purposive sampling was used because no complete frame of relevant sources exists and the aim "
        "was relevance and depth rather than representativeness. Studies were selected systematically against "
        "predetermined eligibility criteria (Table 2), not recruited. The de-duplicated database exports formed the "
        "sampling frame, and screening followed the PRISMA 2020 sequence (Page et al., 2021): title and abstract "
        "screening, then full-text screening, with every exclusion reason recorded.",
    "This process reduced 1,284 identified records":
        "This reduced 1,284 identified records to 46 included sources (Figure 1). The number follows from the "
        "selection process rather than a target: it is the set of sources that met every criterion while covering "
        "all five pillars.",
    "No sampling of people took place in Phase 3":
        "Phase 3 involved no recruitment of participants, but the test inputs still had to be selected. The ethics "
        "application identified the central risk of synthetic testing: profiles that are too narrow or idealised do "
        "not expose design weaknesses, and random generation clusters around typical cases.",
    "Profiles were therefore designed purposively":
        "Profiles were therefore designed purposively as a full factorial matrix (Table 3): three competency levels, "
        "four disciplines and two goals gave 24 core profiles, so each result could be traced to a dimension. Four "
        "edge cases tested the limits of the design: an empty profile, a very broad profile, skills outside "
        "SkillPath's vocabulary and a profile already holding every skill of its nearest occupations. The matrix was "
        "the sampling frame, and the test set contained 28 profiles.",
    "Every profile was run through both the income-visible":
        "Every profile ran under both the income-visible (A) and income-neutral (B) logic, so each acted as its own "
        "control and any difference could be attributed to income visibility alone.",
    "Data was collected in all three DSR phases":
        "Each DSR phase answered a different sub-question, so data was collected in all three (Table 4).",
    "In this study the literature was data, not background":
        "The literature was data, not background: SQ1 required a traceable route from source to design decision, so "
        "a systematic rather than narrative search was used.",
    "The search was implemented in six steps":
        "A search protocol fixed the search strings, databases, limits and criteria before searching (Annexure B). "
        "Each pillar's string, combining keywords with Boolean operators, was run in each database between 12 May and "
        "20 June 2026 and the results recorded. Exports were merged in Zotero, where duplicates were identified by DOI "
        "and title and removed. Titles and abstracts, then full texts, were screened against Table 2, and the reason "
        "for each full-text exclusion was logged. Each included source was recorded on a data extraction form "
        "(citation, pillar, context, method, key finding, quality rating and design implication). Backward citation "
        "searching added nine sources.",
    "SQ2 asked how SkillPath could be developed":
        "SQ2 required evidence of development decisions, not only the finished application. A traceability matrix "
        "linked each directive to the feature implementing it, and a design decision log recorded each decision's "
        "date, directive, alternatives and rationale.",
    "The proposal planned to evaluate SkillPath through operational data generated by users":
        "The proposal planned to use operational data from users of a live system; the approved ethics application "
        "specified controlled synthetic testing instead, which allowed every starting position to be tested "
        "systematically without exposing job-seekers to an unevaluated prototype. Section 4.2 explains how the "
        "criteria were adapted.",
    "Each cell of the design matrix (Table 3) was turned into":
        "Each matrix cell became a profile in four steps. First, a fabricated CV was written in the South African "
        "graduate format recommended by university career services, with a fictitious name and employers and two, "
        "four or six skills for limited, foundational and moderate profiles respectively. Second, its skills were "
        "expressed in SkillPath's vocabulary: 68 measurable skills in ten categories, linked through ESCO (European "
        "Commission, 2026) to 24 occupations on the DHET (2024) list of occupations in high demand. Third, a target "
        "occupation was assigned, in the same discipline for within-field profiles and a different one for pivots. "
        "Fourth, a specification sheet recorded the profile's purpose and its acceptable recommendations, the target "
        "occupation's skills that the profile lacked, generated by prepare_profiles.py and fixed before testing so "
        "that outputs were judged against expectations SkillPath could not influence (Annexure C).",
    "Testing took place on 16 October 2026":
        "Testing took place on 16 October 2026 on a build frozen and tagged as v1.0-eval (commit 8c154e6). Each "
        "profile ran under versions A and B through five fixed scripts, each exercising specific directives (Table 5).",
    "Outputs were captured automatically by the Python test harness":
        "A Python harness called SkillPath's engine through its adapter and logged every response with a timestamp, "
        "app and logic version, profile, script and step (Annexure D): 762 responses in total. run_evaluation.py "
        "stored the inputs, log, results, a code snapshot and SHA-256 checksums in a replication package, which forms "
        "the raw data shared with the supervisor. Validity rests on mapping each metric to the directive it tests "
        "(Table 6); reliability was checked directly, since re-running the package reproduced identical outputs (Q2).",
    "The ethics application (Annexure Q) was accepted":
        "Annexure Q was accepted by the supervisor without conditions on 1 July 2026, and a waiver for secondary "
        "studies was submitted on 30 June 2026 [and approved on date] (Annexure F). With no participants, consent and "
        "recruitment procedures did not apply, but three safeguards did: CVs contained no information about real "
        "people; data was stored as the Data Management Plan specifies, in an encrypted, two-factor-protected backup "
        "and a private GitHub repository; and the bias safeguards in the ethics application, transparent data "
        "sources and income labelled as an estimate, were tested rather than assumed (Sections 4.2 and 4.3).",
    "The proposal planned to evaluate SkillPath partly through operational data":
        "The proposal also planned operational data from app use. Without users, it was produced by scripted "
        "simulated users: each profile was combined with seven literature-grounded personas, namely a steady "
        "completer and a struggler (Vygotsky, 1978; Bandura, 1997), a drifter who returns when prompted (Fogg, 2003), "
        "an explorer who swaps and a deferrer who chooses 'Not now' (Deci and Ryan, 2000), a part-time learner (Du "
        "Plooy, Casteleijn and Franzsen, 2024) and a dropout (Jordan, 2015), in both versions, giving 392 users. A "
        "script drove SkillPath's own interface over a simulated 21 days, so SkillPath recorded every event itself "
        "(7,960 events). Behaviour was identical in both versions, because scripting a reaction to income would "
        "fabricate the effect being tested.",
    "Each data stream was analysed with a method suited to its form":
        "Thematic analysis was used for the literature and criterion-based evaluation for system outputs; results "
        "were then traced back to the directives they tested.",
    "The extraction forms were analysed using Braun and Clarke":
        "Braun and Clarke's (2006) thematic analysis was chosen because it handles sources with different methods "
        "while keeping themes traceable to coded extracts. PRISMA 2020 governed how the search was reported; "
        "thematic analysis was the method of synthesis. The analysis was hybrid: the pillars gave a deductive frame "
        "and codes were generated inductively, the abductive movement described in the proposal.",
    "In familiarisation, every extraction form was read twice":
        "Extraction forms were read twice with analytic memos; design-relevant findings were coded in an Excel "
        "codebook (68 codes, Annexure B); codes were clustered into candidate themes and checked against their "
        "extracts and the corpus (five merged or discarded); and each surviving theme was rewritten as a testable "
        "directive ('SkillPath must…') and entered into the traceability matrix.",
    "The proposal defined its evaluation thresholds in terms of user behaviour":
        "The proposal's thresholds assumed real users choosing whether to continue, which synthetic testing cannot "
        "produce. The DSR criteria were therefore re-operationalised as properties of SkillPath's outputs: utility as "
        "whether every profile received an appropriate direction, quality as correct, consistent, transparent and "
        "robust behaviour, and efficacy as correctly staged progression. Table 6 defines the nine metrics, whose "
        "thresholds were set on 2 October 2026 and approved by the supervisor before testing.",
    "The core metrics were calculated on the income-neutral version":
        "Core metrics used the income-neutral version (B); consistency and explanation completeness used both. "
        "Rule-based metrics such as Q1 and Q5 had 100% thresholds, because one failure is a design fault. The results "
        "are descriptive proportions over a designed set of cases rather than a sample, so no inferential tests were "
        "applied; their significance is practical, showing whether each rule works.",
    "The proposal intended the A/B comparison":
        "The proposal intended the A/B comparison to test whether income visibility motivates users more than it "
        "sustains them. Self-Determination Theory predicts that extrinsic rewards do not sustain learning (Deci and "
        "Ryan, 2000), which is why income was designed as information rather than the engine of the system (DD9). "
        "Testing motivation requires real graduates: synthetic profiles have none, and simulated users behaved "
        "identically in both versions. The comparison therefore asked whether income visibility changes what "
        "SkillPath recommends, comparing for each core profile the primary recommendation, the overlap of "
        "alternatives, whether A labelled income as an estimate and whether income leaked into B.",
    "Every case where a recommendation fell outside its acceptable set":
        "Every mismatch and edge-case response was read alongside its specification sheet and coded inductively as "
        "'goal not visible' (the target was not among the nearest occupations) or 'neighbouring-occupation pull' (the "
        "target was near, but another occupation's skill gave a larger gain). Results were also broken down by "
        "competency, discipline and goal.",
    "All quantitative analysis was carried out with a Python script":
        "Analysis used analyse_outputs.py (pandas and matplotlib; Annexure E), run by run_evaluation.py, which "
        "computed each metric's numerator and denominator, applied the thresholds and produced the tables and "
        "figures. Scripting made every step recorded and re-runnable on the raw data.",
    "Each Phase 3 metric was mapped back to the design directives":
        "Each metric was mapped to its directives (Table 6). A directive was supported when all its metrics met "
        "their thresholds, partly supported when results were mixed and not supported otherwise; directives "
        "concerning human experience were marked as not testable. Following Hevner et al. (2004), unsupported "
        "directives were treated as findings.",
    "Lincoln and Guba's (1985) criteria were applied as follows":
        "Lincoln and Guba's (1985) criteria were applied. Credibility came from triangulating databases and pillars "
        "and from testing every profile combination, including edge cases. Transferability came from documenting the "
        "matrix and specification sheets in full. Dependability came from a frozen build, scripted tests and a direct "
        "consistency measure (Q2). Confirmability was threatened because the researcher built the artefact, profiles "
        "and acceptable sets; deriving the sets from target occupations before testing, and supervisor review of six "
        "specification sheets, reduced this risk.",
    "Findings are presented in the order of the three DSR phases":
        "Findings follow the three DSR phases. Sections 5.3 to 5.8 describe SkillPath's outputs for synthetic "
        "profiles and simulated users, not real behaviour.",
    "The search identified 1,284 records across the four databases":
        "The search identified 1,284 records. After 312 duplicates were removed, 972 titles and abstracts were "
        "screened and 861 excluded; of 111 full texts assessed, 74 were excluded, most often because they addressed a "
        "pillar only in passing (reasons in Annexure B). Backward citation searching added nine, giving 46 sources "
        "(Figure 1), with 11 on adaptive learning and 8 on AI literacy at the extremes; seven were South African and 31 "
        "reported empirical findings. Annexure B5 summarises the context, method and key findings of the principal "
        "studies.",
    "Thematic analysis produced 10 themes":
        "Thematic analysis produced ten themes, each translated into a design directive (Table 7).",
    "SkillPath was developed between July 2026 and October 2026":
        "SkillPath was built between July and October 2026 as the four proposed layers. The profiling layer draws on "
        "68 measurable skills in ten categories, each with a definition, a task that demonstrates it and World "
        "Economic Forum (2025) demand evidence, linked through ESCO to 24 DHET (2024) high-demand occupations; a "
        "locally hosted language model (all-MiniLM-L6-v2) proposes skills from an uploaded CV for the user to confirm. "
        "The adjacency layer ranks each missing skill by how much it raises average similarity to the up to three "
        "nearest occupations sharing a skill. The micro-learning layer generates six five-to-ten-minute steps that "
        "rise by at most one difficulty level per step and link to free resources, and the progression layer awards "
        "a milestone every three steps (Table 8; Figures 2 to 5).",
    "28 synthetic profiles were tested":
        "Twenty-eight profiles (24 core and 4 edge cases) ran under both versions and five scripts, producing 762 "
        "responses from build v1.0-eval against a reference table of 24 occupations and 68 skills (Table 9).",
    "Every core profile received a recommendation and a six-step pathway":
        "Every core profile received a recommendation and a six-step pathway (U1), and 17 of 24 recommendations fell "
        "in the acceptable set (U2, 70.8%), just above the 70% threshold. Revisions occurred only after a second "
        "consecutive failure and always lowered difficulty (Q1), repeats matched the baseline (Q2), every "
        "recommendation was explained (Q3), edge cases raised no errors (Q4) and first nudges fell on the second "
        "inactive day (Q5). Both efficacy metrics were met. Denominators of 25 include the broad edge case, which also "
        "received a pathway.",
    "All seven mismatches occurred in pivot profiles":
        "All seven mismatches were pivot profiles: in five the target was not among the nearest occupations, and in "
        "two (SP10 and SP12) a neighbouring occupation's skill outranked it. Two (SP06 and SP10) recommended a "
        "laboratory skill to graduates pivoting into data science, because shared skills such as data analysis placed "
        "science occupations nearest. The empty, unrecognised and saturated profiles each received a clear message and "
        "no recommendation, and the broad profile received HTML and CSS with alternatives.",
    "Table 13a and Figure 8 present the operational measures":
        "Table 13a and Figure 8 present the operational measures for the 392 simulated users. All completed the "
        "assessment, and every recipient of a recommendation adopted a pathway, 14.3% after swapping and 14.3% after "
        "first deferring. Every revision was followed by a return within 48 hours, 57.1% of adopters reached two "
        "milestones and 12.8% of users were active after 14 days; both versions produced identical values.",
    "These values follow from the persona mix chosen by the researcher":
        "These values follow from the researcher's persona mix, so they show that SkillPath supports, records and "
        "exports each behaviour, not how graduates engage. The simulation also exposed a fault: SkillPath first nudged "
        "inactive users daily, including users who had finished and were told they were three modules from a "
        "milestone that did not exist, and only 2.9% of 3,450 nudges were opened. Nudges were then restricted to open "
        "pathways and stopped after three unopened nudges (decision log, entries 53 and 55), cutting them to 1,100 with "
        "9.1% opened. A dropout now receives three nudges, but a part-time learner still receives nine (Section 6.6).",
    "The Phase 3 findings describe what SkillPath does":
        "The findings describe what SkillPath does, not how graduates respond; where a human response would be needed, "
        "the evidence is silent (Section 6.7).",
    "SkillPath gave every core profile a direction (U1)":
        "SkillPath gave every profile a direction (U1), addressing the graduate who does not know where to start "
        "(Priyashantha, Dahanayake and Maduwanthi, 2023). Its appropriateness depended on the goal: every within-field "
        "recommendation was acceptable, consistent with Autor et al.'s (2024) evidence that short competency leaps are "
        "the transitions most readily made, but only 41.7% of pivot recommendations were. In five of the seven "
        "failures the target was not adjacent at all, so a proximity-based recommender could not see it; in two it "
        "was adjacent but outranked.",
    "This exposes a tension the proposal did not anticipate":
        "The smallest leap and the desired destination can therefore diverge: adjacency answers 'what is closest to "
        "you?', whereas a pivoting graduate asks 'what gets me there?'. Tavakoli et al.'s (2022) eDoer matched learners "
        "to a chosen role instead, and neither approach alone serves both groups. The implication is a hybrid: "
        "adjacency by default, with an optional goal that constrains the candidate skills.",
    "Performance across disciplines was more even":
        "Performance across disciplines was more even than expected (66.7% for Commerce, Humanities and Natural "
        "Sciences; 83.3% for IT). Building the reference table from six DHET occupations per discipline gave every "
        "discipline nearby destinations, which suggests that balancing reference data mitigates the sector skew the "
        "ethics application warned of, although it cannot remove the labour-market inequalities documented by Chigbu "
        "and Nekhwevha (2022).",
    "The uneven result lay elsewhere":
        "The unevenness lay elsewhere. Generic skills such as data analysis pulled pivoting profiles towards "
        "occupations that share them, so two graduates pivoting into data science were recommended a laboratory "
        "skill. Limited profiles matched most often (87.5%) and broader profiles less often (62.5%), because more "
        "skills spread similarity across competing occupations. This qualifies the Zone of Proximal Development "
        "assumption that more competence makes the next step clearer (Vygotsky, 1978) and strengthens the case for "
        "goal input.",
    "All rule-based quality metrics were met. Revision timing":
        "All rule-based quality metrics were met: revision timing (Q1) confirms the calibration logic drawn from "
        "Vygotsky (1978) and Halkiopoulos and Gkintoni (2024); nudge timing (Q5) confirms the Fogg (2003) rule, though "
        "not human response; and consistency (Q2) means that the same graduate always receives the same advice.",
    "Qualitative inspection of the edge cases confirmed":
        "Reading the edge cases confirmed the robustness result: unrecognised input was named explicitly and the "
        "saturated profile was told that it already covered its nearest occupations. Users can only judge AI "
        "recommendations critically when the reasoning is visible (Long and Magerko, 2020; Chee, Ahn and Lee, 2025), "
        "and every explanation named the nearest occupations, skills held and sources. A robustness metric shows only "
        "that no error occurred, which is why each case was also read.",
    "Every steady-progress run produced at least two milestones":
        "Every steady run produced two milestones (E1) and every pathway rose gradually (E2), creating the visible "
        "staging that the proposal argued builds confidence alongside competence (Bandura, 1997; White, Becker and Du "
        "Plessis, 2021) and that is often missing outside formal institutions (Du Plooy, Casteleijn and Franzsen, "
        "2024). The mechanism works; whether it builds confidence cannot be shown without real graduates.",
    "Income visibility changed nothing about what SkillPath recommended":
        "Income changed nothing that SkillPath recommended, appeared only in version A and was always labelled as an "
        "estimate. It therefore functioned as information rather than as a force reshaping recommendations, as the "
        "proposal's reading of Self-Determination Theory required (Deci and Ryan, 2000). Whether it motivates real "
        "graduates remains untested.",
    "The nudge rule passed its rule-level test":
        "The nudge rule passed its rule-level test (Q5), but the simulated users showed how it behaves over a whole "
        "journey: it first nudged every inactive user daily, including users who had finished, and fewer than one "
        "nudge in thirty was opened. A prompt produces behaviour only when it coincides with motivation and ability "
        "(Fogg, 2003), and learning platforms tend to fail at this trigger layer (Halkiopoulos and Gkintoni, 2024). "
        "Restricting and capping nudges cut their volume by two thirds and tripled the share opened.",
    "One mismatch remained, and it qualifies DD7":
        "One mismatch remained: a part-time learner studying every third day, typical of informal learners (Du Plooy, "
        "Casteleijn and Franzsen, 2024), was still nudged nine times, because a fixed two-day rule reads a deliberate "
        "rhythm as disengagement. Prompts the learner did not choose also sit uneasily with autonomy (Deci and Ryan, "
        "2000). Trigger timing should therefore adapt to each learner's observed rhythm, and learners should be able "
        "to set or pause reminders; whether that helps real graduates is a question for naturalistic evaluation.",
    "Three parts of the research problem lie beyond controlled testing":
        "Three parts of the problem lie beyond controlled testing: self-efficacy, a primary employability barrier "
        "(White, Becker and Du Plessis, 2021) that synthetic profiles cannot hold; engagement, the persistence that "
        "Jordan's (2015) completion data concerns; and perceived relevance and trust, which Chee, Ahn and Lee (2025) "
        "link to AI literacy. These mark the boundary between artificial and naturalistic evaluation (Venable, "
        "Pries-Heje and Baskerville, 2016).",
    "Four further limits apply":
        "Four further limits apply. The researcher built the artefact, profiles and acceptable sets; generating the "
        "sets mechanically and fixing them before testing reduced but did not remove this risk. One profile per cell "
        "means that a single unusual CV can swing a result. The reference table shaped the results, as the generic "
        "shared skills showed. Finally, U2 cleared its threshold narrowly (70.8% against 70%). Adaptive systems often "
        "optimise proxies rather than skill gains (Hariyanto, Kristianingsih and Maharani, 2025), and output "
        "correctness is such a proxy: the findings show that SkillPath's logic largely works as designed, not that it "
        "improves employability.",
    "SQ1 was answered by the ten design directives":
        "SQ1 was answered by the ten directives in Table 7. Adjacency evidence and the Zone of Proximal Development "
        "translated most directly into ranking and calibration rules, while Self-Determination Theory acted mainly as "
        "a constraint on how income and revisions were presented.",
    "SQ2 was answered by the artefact":
        "SQ2 was answered by the artefact and Table 8: all ten directives were implemented, DD7 as a fixed rather than "
        "motivation-aware trigger and DD10 in part, because milestones record step completion rather than verified "
        "evidence.",
    "SQ3 (revised) was answered by Tables 10 to 13":
        "SQ3 was answered by Tables 10 to 13a. The direction-first design gave an appropriate next skill to every "
        "within-field graduate but to 41.7% of pivoting graduates (70.8% overall against 70%), and the "
        "progression-visible design staged learning correctly in every run. The shortfall is explained: adjacency "
        "cannot see a non-adjacent destination, and shared generic skills pull pivots sideways.",
    "RQ1 asked what the design requirements are":
        "RQ1 is answered by the directives in Table 7, now carrying evaluation evidence (Table 15). The evaluation adds "
        "two requirements that the literature did not supply: an optional goal for pivoting graduates, and trigger "
        "timing that adapts to the learner. It confirms a third that was designed in: declining transparently to "
        "recommend when a profile is not recognised. For self-efficacy, it shows only that the confidence-building "
        "mechanism functions.",
    "The research problem identified three gaps":
        "The direction gap was closed for graduates building on their field and only partly for those changing "
        "fields. The confidence gap was met by a progression mechanism that works as designed, though its effect on "
        "confidence is untested. The exclusion gap was addressed by a free, mobile-first tool for individuals, and "
        "balanced reference data kept performance even across disciplines.",
    "The implications run in three directions":
        "For theory, the results qualify adjacency reasoning: it explains which transitions are easiest, not which a "
        "person wants, and broader skill sets can make direction harder to find. For practice, the design matrix, "
        "scripted tests and simulated users form a reusable test battery that exposed the pivot problem and a nudge "
        "fault before any job-seeker met them. For research design, the study shows where artificial evaluation is "
        "informative and where it is silent, which specifies the naturalistic evaluation needed next.",
    "This document reported a three-phase DSR study":
        "A systematic review of 46 sources produced ten design directives, which were implemented in SkillPath and "
        "evaluated through controlled synthetic testing of 28 researcher-built profiles and 392 simulated users "
        "against thresholds fixed in advance. SkillPath met all nine thresholds and kept income separate from its "
        "recommendations, but adjacency served graduates staying in their field far better than those changing "
        "fields, and a fixed nudge rule did not fit every learner. How real graduates respond remains for "
        "naturalistic evaluation and for the final report's discussion of future work.",
}

# (author-year sort key, [(text, italic), ...]) - Harvard (IIE): italics for book/report/journal titles
NEW_REFS = [
    ("DHET", [("DHET (Department of Higher Education and Training), 2024. ", False),
              ("2024 national list of occupations in high demand", True),
              (". Government Gazette No. 50510, Notice 2414 of 2024, 16 April. Pretoria: Government Printing Works. "
               "Available at: https://www.dhet.gov.za/System%20Monitoring%20%20Labour%20Market%20Intelligence/"
               "Gazette_The%202024%20National%20List%20of%20Occupations%20in%20High%20Demand.pdf [Accessed 5 October "
               "2026].", False)], "Du Plooy"),
    ("European Commission", [("European Commission, 2026. ", False),
                             ("ESCO: European skills, competences, qualifications and occupations", True),
                             (". [online] Brussels: European Commission. Available at: https://esco.ec.europa.eu "
                              "[Accessed 5 October 2026].", False)], "Fogg"),
    ("Hariyanto", [("Hariyanto, Kristianingsih, F.X.D. and Maharani, R., 2025. Artificial intelligence in adaptive "
                    "education: A systematic review of techniques for personalised learning. ", False),
                   ("Discover Education", True),
                   (", 4, p.458. Available at: https://doi.org/10.1007/s44217-025-00908-6 [Accessed 25 March 2026].",
                    False)], "Hevner"),
    ("World Economic Forum", [("World Economic Forum, 2025. ", False), ("The future of jobs report 2025", True),
                              (". Geneva: World Economic Forum. Available at: https://reports.weforum.org/docs/"
                               "WEF_Future_of_Jobs_Report_2025.pdf [Accessed 5 October 2026].", False)], None),
]
FIX_REFS = {
    "[Page, M.J.": [("Page, M.J., McKenzie, J.E., Bossuyt, P.M., Boutron, I., Hoffmann, T.C., Mulrow, C.D. et al., "
                     "2021. The PRISMA 2020 statement: An updated guideline for reporting systematic reviews. ", False),
                    ("BMJ", True), (", 372, n71. Available at: https://doi.org/10.1136/bmj.n71 [Accessed 16 October "
                                    "2026].", False)],
    "[Venable, J.": [("Venable, J., Pries-Heje, J. and Baskerville, R., 2016. FEDS: A framework for evaluation in "
                      "design science research. ", False), ("European Journal of Information Systems", True),
                     (", 25(1), pp.77-89. Available at: https://doi.org/10.1057/ejis.2014.36 [Accessed 16 October "
                      "2026].", False)],
}

STUDIES = [  # Annexure B5: principal included studies (details as reported in the research proposal)
    ("Study", "Context", "Method", "Key finding", "Directive"),
    ("Autor et al. (2024)", "US Census, 1940-2018", "Longitudinal labour-market analysis",
     "Workers whose competencies sit close to new roles transition fastest", "DD2"),
    ("Chee, Ahn and Lee (2025)", "Learner groups", "Competency framework study",
     "Understanding AI differs from evaluating AI recommendations", "DD8"),
    ("Chigbu and Nekhwevha (2022)", "335 students, University of Fort Hare", "Survey",
     "Skill inequalities between faculties shape recruitment outcomes", "Equity"),
    ("Du Plooy, Casteleijn and Franzsen (2024)", "Higher education, 69 studies", "Scoping review",
     "Adaptive learning improved performance in 59% of studies; weaker outside formal structures", "DD3"),
    ("Halkiopoulos and Gkintoni (2024)", "E-learning", "Review",
     "Ignoring cognitive load produced disengagement; platforms fail at the trigger layer", "DD4, DD7"),
    ("Hariyanto, Kristianingsih and Maharani (2025)", "Adaptive education", "Systematic review",
     "Adaptive systems often optimise participation proxies rather than skill gains", "DD10"),
    ("Jordan (2015)", "221 MOOCs", "Secondary analysis of completion data", "Median completion rate of 12.6%", "DD1"),
    ("Long and Magerko (2020)", "Human-computer interaction", "Framework synthesis",
     "Seventeen AI literacy competencies", "DD8"),
    ("Priyashantha, Dahanayake and Maduwanthi (2023)", "118 articles", "Systematic literature review",
     "Career decision-making difficulty is a primary determinant of indecision", "DD1"),
    ("Tavakoli et al. (2022)", "Open, labour-market-driven education", "Artefact with randomised experiment",
     "Recommender (eDoer) matching learners to role requirements", "DD2"),
    ("White, Becker and Du Plessis (2021)", "Industrial Psychology graduates, South Africa", "Quasi-experiment",
     "Low self-efficacy is an employability barrier; a development centre improved it", "DD5"),
]


def set_text(par, text):
    if par.runs:
        par.runs[0].text = text
        for r in par.runs[1:]:
            r.text = ""
    else:
        par.add_run(text)


def prisma_figure(path):
    fig, ax = plt.subplots(figsize=(9, 7.2))
    ax.axis("off")

    def box(x, y, w, h, text, fc="#FFFFFF"):
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=True, fc=fc, ec="#1F3A5F", lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, wrap=True, family="Arial")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color="#1F3A5F", lw=1.1))

    for y, lab in [(0.84, "Identification"), (0.47, "Screening"), (0.08, "Included")]:
        ax.text(0.015, y, lab, rotation=90, va="center", fontsize=9, fontweight="bold", family="Arial")
    box(0.06, 0.78, 0.40, 0.14, "Records identified from databases\n(Scopus, IEEE Xplore, Google Scholar, PubMed)\n(n = 1,284)")
    box(0.56, 0.78, 0.40, 0.14, "Records removed before screening:\nduplicates (n = 312)")
    box(0.06, 0.56, 0.40, 0.11, "Records screened (titles and abstracts)\n(n = 972)")
    box(0.56, 0.56, 0.40, 0.11, "Records excluded\n(n = 861)")
    box(0.06, 0.34, 0.40, 0.11, "Full-text reports assessed for eligibility\n(n = 111)")
    box(0.56, 0.31, 0.40, 0.17, "Reports excluded (n = 74):\npillar addressed only in passing\nand other reasons (Annexure B)")
    box(0.56, 0.14, 0.40, 0.11, "Other methods: backward citation\nsearching (n = 9)", fc="#F2F5F9")
    box(0.06, 0.02, 0.40, 0.12, "Studies included in review\n(n = 46: 37 from databases + 9)")
    arrow(0.26, 0.78, 0.26, 0.67); arrow(0.46, 0.85, 0.56, 0.85)
    arrow(0.26, 0.56, 0.26, 0.45); arrow(0.46, 0.615, 0.56, 0.615)
    arrow(0.26, 0.34, 0.26, 0.14); arrow(0.46, 0.395, 0.56, 0.395)
    arrow(0.56, 0.18, 0.46, 0.09)
    ax.set_title("PRISMA 2020 flow diagram (Page et al., 2021)", fontsize=10, family="Arial")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def add_ref(before_par, parts, like):
    p = before_par.insert_paragraph_before("", style=like.style)
    p.paragraph_format.alignment = like.paragraph_format.alignment
    for text, italic in parts:
        r = p.add_run(text)
        r.italic = italic
    return p


def rewrite_ref(par, parts):
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    for text, italic in parts:
        par.add_run(text).italic = italic


def apply_format(d):
    for s in d.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2)

    def arial(run):
        run.font.name = "Arial"
        run.font.size = Pt(12)
        rpr = run._r.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = rpr.makeelement(qn("w:rFonts"), {})
            rpr.append(fonts)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(a), "Arial")

    for st in d.styles:
        try:
            st.font.name = "Arial"
            st.font.size = Pt(12)
        except Exception:
            pass
    paras = list(d.paragraphs)
    start = [i for i, p in enumerate(paras) if p.text.startswith("1. Introduction to Part 3")][-1]
    for i, p in enumerate(paras):
        for r in p.runs:
            arial(r)
        p.paragraph_format.line_spacing = 1.5
        heading = p.style is not None and p.style.name.lower().startswith(("heading", "title"))
        has_pic = bool(p._p.xpath(".//w:drawing"))
        if i >= start and not heading and not has_pic and p.text.strip():
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        arial(r)
                    p.paragraph_format.line_spacing = 1.0


def body_word_count(d):
    els = list(d.element.body.iterchildren())
    txt = [e.xpath("string(.)").strip() for e in els]
    s = [i for i, t in enumerate(txt) if t.startswith("1. Introduction to Part 3")][-1]
    e = [i for i, t in enumerate(txt) if t == "Reference List"][-1]
    return sum(len(t.split()) for t in txt[s:e])


def main():
    d = docx.Document(SRC)
    paras = list(d.paragraphs)
    start = [i for i, p in enumerate(paras) if p.text.startswith("1. Introduction to Part 3")][-1]
    body = paras[start:]
    done = set()
    for p in body:
        for k, v in R.items():
            if k not in done and p.text.startswith(k):
                set_text(p, v)
                done.add(k)
        if any(p.text.startswith(k) for k in DELETE):
            p._p.getparent().remove(p._p)
    missing = sorted(set(R) - done)

    for t in d.tables:  # Springer Nature placeholder in Table 7
        for row in t.rows:
            for c in row.cells:
                if "Springer Nature (2025)" in c.text:
                    set_text(c.paragraphs[0], "Hariyanto, Kristianingsih and Maharani (2025)")

    # PRISMA figure
    prisma_figure(PRISMA_PNG)
    fig_par = next(p for p in d.paragraphs if p.text.strip() == "[INSERT FIGURE 1]")
    set_text(fig_par, "")
    fig_par.runs[0].add_picture(PRISMA_PNG, width=Cm(15))
    fig_par.alignment = 1

    # References
    paras = list(d.paragraphs)
    ref_i = [i for i, p in enumerate(paras) if p.text.strip() == "Reference List"][-1]
    annex_i = next(i for i in range(ref_i + 1, len(paras)) if paras[i].text.startswith("Annexure A: AI"))
    ref_paras = [p for p in paras[ref_i + 1:annex_i] if p.text.strip()]
    like = next(p for p in ref_paras if p.text.startswith("Bandura"))
    for p in ref_paras:
        for k, parts in FIX_REFS.items():
            if p.text.startswith(k):
                rewrite_ref(p, parts)
        if p.text.startswith("[AUTHORS, 2025"):
            p._p.getparent().remove(p._p)
    ref_paras = [p for p in ref_paras if p._p.getparent() is not None]
    annex_a = paras[annex_i]
    for key, parts, before in NEW_REFS:
        target = next((p for p in ref_paras if before and p.text.startswith(before)), None)
        if target is None:  # append at the end of the list
            target = annex_a
        add_ref(target, parts, like)

    # Annexure B5: characteristics of principal included studies
    allp = list(d.paragraphs)
    b4 = next(i for i, p in enumerate(allp) if p.text.startswith("B4. Codebook template"))
    annex_c = next(p for p in allp[b4:] if p.text.startswith("Annexure C:"))
    b_head = next(p for p in d.paragraphs if p.text.startswith("B4. Codebook template"))
    h = annex_c.insert_paragraph_before("B5. Characteristics of principal included studies", style=b_head.style)
    note = annex_c.insert_paragraph_before(
        "The principal studies behind the design directives (Table 7); the full table for all 46 sources is "
        "exported from the data extraction forms.", style=like.style)
    t = d.add_table(rows=len(STUDIES), cols=len(STUDIES[0]))
    t.style = d.tables[0].style
    for i, row in enumerate(STUDIES):
        for j, v in enumerate(row):
            t.rows[i].cells[j].text = v
            if i == 0:
                for r in t.rows[i].cells[j].paragraphs[0].runs:
                    r.bold = True
    annex_c._p.addprevious(t._tbl)
    annex_c.insert_paragraph_before("Table B5: Characteristics of principal included studies", style=like.style)

    apply_format(d)
    n = body_word_count(d)
    for p in d.paragraphs:
        if p.text.startswith("Word count (body"):
            set_text(p, f"Word count (body, excluding cover page, reference list and annexures): {n:,} words")
    d.save(OUT)
    print(f"wrote {OUT}\nbody words (paragraphs + tables): {n}")
    if missing:
        print("NOT FOUND:", missing)


if __name__ == "__main__":
    main()
