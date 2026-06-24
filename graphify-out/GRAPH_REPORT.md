# Graph Report - ccmed  (2026-06-24)

## Corpus Check
- 138 files · ~205,059 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1364 nodes · 2586 edges · 111 communities (104 shown, 7 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a6043ee0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 108|Community 108]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 132|Community 132]]

## God Nodes (most connected - your core abstractions)
1. `FormattedProblem` - 70 edges
2. `QuestionContext` - 66 edges
3. `DNA` - 56 edges
4. `VocabGated` - 32 edges
5. `get_cache()` - 32 edges
6. `log_interpolate()` - 30 edges
7. `ErrorPattern` - 30 edges
8. `set_cache()` - 26 edges
9. `20. Lessons Learned & Implementation Pitfalls` - 25 edges
10. `generate_pair_by_window()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `PlacementEngine` --uses--> `SkillNode`  [INFERRED]
  backend/app/services/placement.py → backend/app/models.py
- `RedisDict` --uses--> `CompetencyConfiguration`  [INFERRED]
  backend/app/routes/matatag_router.py → backend/app/models.py
- `replenish_question_cache()` --calls--> `SessionLocal()`  [EXTRACTED]
  backend/app/routes/admin_router.py → backend/app/database.py
- `replenish_question_cache()` --calls--> `SessionLocal()`  [EXTRACTED]
  backend/app/routes/matatag_router.py → backend/app/database.py
- `replenish_question_cache()` --calls--> `SessionLocal()`  [EXTRACTED]
  backend/app/routes/practice_router.py → backend/app/database.py

## Import Cycles
- None detected.

## Communities (111 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (10): BackgroundTasks, _combined_interests(), get_practice_question(), get_practice_question_batch(), Background task to pre-generate questions into the cache.     Uses parallel exec, Onboarding Placement / Elo Match practice question dispatch router.     Integrat, Returns a batch of 3 questions.      ELA/Verbal — batch-of-3 LLM strategy:, Merge parent-set interest_tags and student-set student_interest_tags into a (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (20): _get_available_formats(), get_matatag_difficulty_axes(), get_matatag_lab_config(), get_matatag_lab_interests(), get_matatag_nodes(), get_matatag_progress(), get_node_capabilities(), matatag_lab_generate() (+12 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (25): 20.0 Curriculum Descriptor ≠ Student Vocabulary, 20.10 Common Generator Pitfalls, 20.11 Debugging Visual Rendering Issues, 20.12 Introduction Slide ≠ Definitions Slide (CRITICAL), 20.13 Grade-Level Vocabulary Constraints, 20.14 Cross-Branch Terms and the Vocabulary System, 20.15 Every Competency Needs a Worked Example, 20.16 Interest Wrapping Must Be Consistent Within a Mini-Lesson (+17 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (11): Practice Generation — DNA Base Definitions  All dataclasses, enums, and shared u, A reusable story template with named slots.      Slots are filled from the stude, Fill template with interest slots and numeric values.                  Handles s, Spine, build_scaffold_sequence(), Practice Generation — Scaffolded Experience Wrapper  Ascending-difficulty sequen, Build an ordered list of difficulty profiles for a scaffold sequence.      Each, Practice Generation — Standard Experience Wrapper  Simple pass-through wrapper t (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.28
Nodes (8): generate_hints(), generate_params(), _make_arithmetic_sequence(), _make_repeating_sequence(), DNA: Patterns (Number & Algebra)  Covers MATATAG grades 1–3 pattern competencies, Return 2–4 step-by-step hints for the given pattern problem., Build a sequence by repeating the cycle starting at start offset., Generate a pattern sequence based on grade and difficulty profile.      Returns:

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (35): Any, ErrorPattern, A pedagogically meaningful wrong answer.      formula:          SymPy expression, A mathematical term fragment gated behind vocab knowledge.      preferred:    Te, VocabGated, generate_hints(), generate_params(), DNA: Pictographs (Data & Probability)  Covers MATATAG grades 1–2 pictograph comp (+27 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (34): enumerate_profiles(), extract_numerical_limits(), get_dimension_ranges(), _make_predicates(), measure_acceptance_rate(), normalize_difficulty(), Practice Generation — Difficulty Engine ========================================, Convert a difficulty_profile dict to a scalar in [0.0, 1.0].      Each axis pres (+26 more)

### Community 7 - "Community 7"
Cohesion: 0.24
Nodes (9): _boundary_distance(), generate_hints(), generate_params(), DNA: Rounding (Number & Algebra)  G3 only — rounding 4-digit numbers to nearest, Return 2–4 step-by-step hints for a rounding problem., Round n to the nearest precision (10, 100, 1000) using round-half-up., Return how far n is from the nearest rounding boundary., Generate a rounding problem (G3 only).      Returns:         {             "numb (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (20): call_ai(), _format_age_grade_constraints(), GenAIBridge, generate_ela_batch_subagent(), generate_ela_skeleton_subagent(), generate_math_question_ai(), _get_bridge_pool(), has_visual_reference() (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (37): _gen_g3_dp_q3_bar_graphs(), _gen_g3_dp_q3_probability(), _gen_g3_mg_q1_area(), _gen_g3_mg_q1_lines(), _gen_g3_mg_q2_capacity(), _gen_g3_mg_q2_mass(), _gen_g3_mg_q4_symmetry(), _gen_g3_na_q1_comparing() (+29 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (18): _count_decimal_places(), generate_number_by_window(), Choose a number randomly from the candidates list within the difficulty range wi, Score signed integers, adding a small penalty for negative numbers., Score a fraction n/d based on:     - Denominator size (40%)     - Numerator/Deno, Ordinal difficulty scales linearly with magnitude (1st is easiest, 100th is hard, Score a whole number or decimal based on divisibility, digits, and magnitude., Unified scoring router based on number type. (+10 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (53): _gen_g2_dp_q3_pictograph(), _gen_g2_mg_q1_circles(), _gen_g2_mg_q1_slides(), _gen_g2_mg_q2_measurement(), _gen_g2_mg_q4_perimeter(), _gen_g2_mg_q4_solid_figures(), _gen_g2_mg_q4_time(), _gen_g2_na_q1_addition() (+45 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (31): dependencies, dagre, @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities, localtunnel, lucide-react, react (+23 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (25): AdminGraphEdge, AdminGraphNode, AdminGraphResponse, AnswerSubmitRequest, AnswerSubmitResponse, Config, GraphNode, GraphTrack (+17 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (27): API_BASE, BalanceScaleInteractive(), BarChartInteractive(), CalendarInteractive(), CategorizeInteractive(), ClockSetInteractive(), ConstraintSatisfactionInteractive(), EmojiPictorialInteractive() (+19 more)

### Community 15 - "Community 15"
Cohesion: 0.17
Nodes (15): generate_node_id(), get_competencies_for_grade(), get_competency_by_id(), _get_matatag_data_path(), load_matatag_curriculum(), _load_matatag_json(), parse_node_id(), matatag_loader.py ----------------- Loads MATATAG (Philippine K-10 Math Curricul (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (23): 1. Architecture Decisions, 1. Core Architecture Layers, 1. Critical Pitfalls (AVOID THESE), 2. DNA API & Generation Flow, 2. Gating and Routing Architecture, 2. Supported Visual Types (The 12 Core Archetypes), 3. Engine API Interface, A. Stateless IDs (`skeleton_id`) (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (29): _gen_g1_dp_q3_data(), _gen_g1_mg_q1_shapes(), _gen_g1_mg_q2_length(), _gen_g1_mg_q4_time(), _gen_g1_mg_q4_turns(), _gen_g1_na_q2_addition(), _gen_g1_na_q2_counting(), _gen_g1_na_q2_place_value() (+21 more)

### Community 18 - "Community 18"
Cohesion: 0.23
Nodes (9): MasteryState, StudentProfile, PlacementEngine, Calculates the active search bounds from the student's attempt history., Concludes placement onboarding, calculates baseline ELO and populates mastery st, Implements a Binary Search Onboarding Placement Engine.     Pinpoints student's, Initializes placement state for a new student.         Seeds grade-appropriate m, Bypasses the placement test and seeds mastery based on the student's claimed gra (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (12): DimensionSpec, interpolate(), Compute the dimension value at difficulty scalar t.          If override_min/ove, Interpolate between min_val and max_val using the given scale type.      scale_t, Specification for a single difficulty dimension.      Defines how a dimension sc, generate_hints(), generate_params(), DNA: Addition (Number & Algebra)  Refactored from:   - matatag_skeletons.py  (ar (+4 more)

### Community 20 - "Community 20"
Cohesion: 0.25
Nodes (7): generate_hints(), generate_params(), DNA: Subtraction (Number & Algebra)  Refactored from:   - matatag_skeletons.py, Generate (a, b) with a >= b that satisfy the difficulty_profile constraints., Return 2–4 step-by-step hint strings for the given subtraction problem., For subtraction, regrouping (borrowing) occurs when a digit in b > corresponding, _satisfies_regrouping()

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (9): 15. Data Dependencies, 16. File Structure, 19. Open Questions (To Resolve During Implementation), 1. Philosophy, 2. Core Architecture, 9. Runtime Generation Pipeline, CCMed — Adaptive K-12 Mastery Engine, Introductory Content Strategy (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.15
Nodes (26): get_db(), FastAPI dependency that yields a database session.     Guarantees session closur, SessionLocal(), Background task to pre-generate questions into the cache.     Uses parallel exec, replenish_question_cache(), compute_difficulty_scalar(), get_axes_for_concept(), Return the UI-ready axis list for a concept, or [] if not found. (+18 more)

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (16): 1. Architecture Overview, 2. Automated CI/CD (GitHub Actions Workflow), 3. Required Secrets & Configuration Keys, 4. Operational Playbook & Maintenance, 5. Common Pitfalls & Solutions, 6. AI Agent Workflow (Graphify & MCP), Agent Environment, Backend Flow (`.github/workflows/deploy-backend.yml`) (+8 more)

### Community 24 - "Community 24"
Cohesion: 0.32
Nodes (7): _fraction_str(), generate_hints(), generate_params(), DNA: Fractions (Number & Algebra)  Refactored from:   - matatag_skeletons.py  (f, Rejection-sample a fraction (or pair of fractions) matching difficulty_profile., Return 2–4 step-by-step hint strings for the given fractions problem., _simplify()

### Community 25 - "Community 25"
Cohesion: 0.29
Nodes (6): generate_hints(), generate_params(), DNA: Counting (Number & Algebra)  Refactored from:   - matatag_skeletons.py  (co, Generate counting parameters satisfying difficulty_profile., Return 2–4 step-by-step hint strings for the given counting problem., _select_skip()

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (23): BalanceScaleParams, BarChartParams, BaseVisualParams, CalendarParams, ClockParams, EmojiPictorialParams, FillInTableParams, FractionModelParams (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (4): RedisDict, RedisDict, get_cache(), set_cache()

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (11): get_matatag_competencies(), Return MATATAG competencies for dropdown selection in Problem Lab.          Resp, _combined_interests(), _match_competency_to_visual_type(), Background task to pre-generate questions into the cache.     Uses parallel exec, Socratic Tutor split-screen dialog endpoint.     Guides the student out of their, Match a MATATAG competency to a visual skeleton type using regex patterns.     R, Merge parent-set interest_tags and student-set student_interest_tags into a (+3 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (16): generate_pair_by_window(), Choose an operand pair randomly from candidate_pairs within the difficulty range, _close_pair(), _compare_symbol(), generate_hints(), generate_params(), DNA: Comparing and Ordering Numbers (Number & Algebra)  Covers MATATAG grades 1–, Return 2–4 step-by-step hints for a comparison/ordering problem. (+8 more)

### Community 30 - "Community 30"
Cohesion: 0.07
Nodes (36): QuestionContext, Format-agnostic intermediate produced by the context generator.      Everything, _build_equation_sentence(), format_cloze(), Textual Formatter — Cloze (Fill-in-the-Blank)  Unified formatter for fill-in-the, Build pure equation with blank based on concept and blank_target., Format a QuestionContext as a cloze (fill-in-the-blank) problem.      Respects t, _build_pure_question() (+28 more)

### Community 31 - "Community 31"
Cohesion: 0.29
Nodes (7): 11. Frontend Specification, Entry Flow, Navigation, New View State: `node_intro`, Slide Component, Slide Type Rendering, Visual Rendering Priority

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (7): 4. Perseus Template → Parameterized Template, Multiple Strategies Per Concept, Original Perseus (fixed):, Parameterization Rules, Parameterized Version (dynamic):, The Transformation Process, Variable Slot Types

### Community 33 - "Community 33"
Cohesion: 0.29
Nodes (7): 8. Definition Bank, Classification Rules, Definition Bank Location, Rebuilding After Changes, Two-Field Vocabulary Structure, Vocabulary Classification Principle, When `student_vocab = []`

### Community 34 - "Community 34"
Cohesion: 0.29
Nodes (6): Architectural Refactoring Implementation Plan, Phase 1: Immediate Priority - Data Contracts & Normalization (High Impact), Phase 2: Structural Improvements via Graph Insights (Medium Risk), Phase 3: Frontend Efficiency & State Management (Medium Risk), Phase 4: Performance & Scaling - Backend Efficiency (High Risk), Phase 5: CI/CD & Verification

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (22): linear_interpolate(), Linear interpolation between min_val and max_val at position t., generate_hints(), generate_params(), DNA: Bar Graphs (Data & Probability)  Covers MATATAG grade 3 bar graph competenc, Returns visual_params for the BarChart formatter (G3 only).     {"categories": l, generate_hints(), generate_params() (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (20): generate_intro_content(), get_available_intro_nodes(), get_interest_themes(), _get_introduction(), Intro Content Generator  Produces structured intro slides for MATATAG nodes usin, Return all interest themes. Grade parameter is ignored (kept for API compatibili, Bind the G1_NA_Q1 generator functions after they are defined., Return list of nodes that have intro content available. (+12 more)

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (13): get_dnas_for_formatter(), get_supported_variants(), get_variants_for_dna(), is_compatible(), is_variant_supported(), Practice Generation — DNA-Formatter Compatibility Table ========================, Return True if the formatter is compatible with the given DNA concept.      Args, Return all DNA concept names that support a given formatter.      Performs a rev (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.33
Nodes (6): 17. Reference: G1_NA_Q1 Intro Structure, Competencies (10 total), Mini-Lesson 1: "Counting & Numerals", Mini-Lesson 2: "Comparing & Ordering", Mini-Lesson 3: "Breaking Apart Numbers", Mini-Lesson 4: "Addition"

### Community 39 - "Community 39"
Cohesion: 0.19
Nodes (15): _build_params(), _build_question_text(), _correct_answer(), format_emoji_pictorial(), _generate_distractors(), _get_emoji_name(), _pluralize(), fmt_emoji_pictorial.py — Emoji Pictorial Model formatter  NEW formatter — Aligns (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.33
Nodes (6): 5. Vocabulary & Cognitive Constraints, Enforcement Points, Grade Knowledge Ceiling, NOT_YET_KNOWN Enforcement, Rule 1: Incorporate — draw from prior vocabulary, Rule 2: Exclude — never use future vocabulary

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (5): 1. Difficulty Dimensions, 2. Contextual Variants, 3. Formatters (Problem Types), 4. Final Review, Learning Competency Practice Problem Generator Checklist

### Community 42 - "Community 42"
Cohesion: 0.33
Nodes (6): generate_hints(), generate_params(), num_to_words(), DNA: Money / Philippine Peso (Number & Algebra)  Covers MATATAG grades 1–3 money, Generate a money problem for the given grade., Return 2–4 step-by-step hints for the given money problem.

### Community 43 - "Community 43"
Cohesion: 0.40
Nodes (5): 14. Subagent Roles, Content Validator Subagent, Definition Author Subagent, Introduction Author Subagent, Perseus Strategy Selector Subagent

### Community 44 - "Community 44"
Cohesion: 0.40
Nodes (5): 18. Implementation Phases, Phase 1: Infrastructure, Phase 2: G1_NA_Q1 Content, Phase 3: Scale to G1, Phase 4: Scale to G1-3

### Community 45 - "Community 45"
Cohesion: 0.40
Nodes (5): 6. Interest Wrapping, Answer Invariance, Grade Band Filtering, Interest Bank Structure, When Interest Wrapping Applies

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (17): Generate a single practice problem and return it as a dict.      This is the sin, run(), find_node_id(), get_all_node_ids(), get_node_competency_bounds(), get_node_formatters(), get_node_info(), _parse_competency_bounds() (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.50
Nodes (4): 10. Backend API Specification, GET /api/matatag/intro/{node_key}, GET /api/matatag/intro/{node_key}/status, POST /api/matatag/intro/{node_key}/viewed

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (28): DNA, Specification of a mathematical concept for practice generation.      dna_type:, Return param_bounds for grade, falling back to nearest defined grade., Return the index of a level within an axis (0 = easiest)., Return a 0.0–1.0 scalar for a given axis level., _build_symbolic_question(), _detect_axes_served(), _eval_error_formula() (+20 more)

### Community 49 - "Community 49"
Cohesion: 0.50
Nodes (4): 13. Validation, Type A Validation (Worked Examples), Type B Validation (Authored Content), Validation Pipeline

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (13): _build_addition_params(), _build_subtraction_params(), _build_traps(), _build_visual_params(), _correct_value(), format_number_line(), fmt_number_line.py — NumberLine visual formatter  Produces a FormattedProblem wi, Build number-line visual_params for a given grade / difficulty.      Returns dic (+5 more)

### Community 51 - "Community 51"
Cohesion: 0.22
Nodes (13): _build_traps(), _build_visual_params(), format_peso_money(), _grade_denominations(), _greedy(), fmt_peso_money.py — PesoMoney visual formatter  Produces a FormattedProblem with, Generate PesoMoney visual_params.      visual_params keys:         coins, Return trap dict mirroring visual_skeletons._traps_peso_money. (+5 more)

### Community 52 - "Community 52"
Cohesion: 0.11
Nodes (38): FormattedProblem, Final output of the practice generation pipeline.      Produced by a formatter o, Apply the mastery-drill experience wrapper.      Sets problem.experience to "mas, wrap_mastery_drill(), Apply the scaffolded experience wrapper.      Sets problem.experience to "scaffo, wrap_scaffolded(), Apply the standard (no-op) experience wrapper.      Sets problem.experience to ", wrap_standard() (+30 more)

### Community 53 - "Community 53"
Cohesion: 0.50
Nodes (4): 7. Mini-Lesson Grouping, Grouping Algorithm, Mini-Lesson Structure, Slide Count Estimates

### Community 54 - "Community 54"
Cohesion: 0.21
Nodes (13): get_node(), Return the raw knowledge-graph node dict for node_id, or None.      Args:, _load_dna(), Practice Generation — Vocabulary & Concept Constraint Validation  Verifies that, Verify that distractors don't presuppose unknown concepts.      For each distrac, Generate sample problems for a node and run vocabulary/concept checks.      Args, Import the DNA module and return its DNA instance, or None on failure., Return True if `term` appears as a standalone token in `text`.      Case-insensi (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.13
Nodes (17): log_interpolate(), Logarithmic interpolation between min_val and max_val at position t.      Produc, generate_hints(), generate_params(), DNA: Length Measurement (Measurement & Geometry)  Covers MATATAG grades 1–2 leng, Returns numeric params used by the ruler_measure formatter or word-problem spine, generate_hints(), generate_params() (+9 more)

### Community 56 - "Community 56"
Cohesion: 0.24
Nodes (11): CompetencyConfiguration, PydanticBaseModel, LabV2ConfigSaveRequest, LabV2GenerateRequest, LabV2SubmitRequest, matatag_lab_v2_submit(), Request body for /api/matatag/lab/v2/generate, Request body for /api/matatag/lab/v2/submit (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.08
Nodes (24): QuestionFlagRequest, StudentRegisterRequest, TelemetrySessionStartRequest, UpdateInterestsRequest, load_matatag_curriculum_endpoint(), Load MATATAG (Philippine K-10 Math) curriculum into the skill_nodes table., get_intro_status(), get_node_config() (+16 more)

### Community 59 - "Community 59"
Cohesion: 0.31
Nodes (3): Background task to pre-generate questions into the cache.     Uses parallel exec, RedisDict, replenish_question_cache()

### Community 61 - "Community 61"
Cohesion: 0.24
Nodes (11): _build_traps(), _decompose(), format_place_value_blocks(), _grade_max(), _grade_min(), fmt_place_value_blocks.py — PlaceValueBlocks visual formatter  NEW formatter — n, Build a PlaceValueBlocks FormattedProblem from a QuestionContext.      interacti, Break number into place-value blocks appropriate for the grade.     Returns dict (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (4): LearningDomain, Enforces Grade-Level Vocabulary Constraints (Community 2), Extracts common misconceptions (Community 5), Base class for Domain Services.     Encapsulates DNA generation logic, curriculu

### Community 63 - "Community 63"
Cohesion: 0.38
Nodes (6): _build_traps(), _build_visual_params(), format_array_grid(), fmt_array_grid.py — ArrayGrid (GridArea) visual formatter  Produces a FormattedP, Build an ArrayGrid FormattedProblem from a QuestionContext.      interaction_mod, Build ArrayGrid visual_params.      Grade 2: arrays up to 10×10 (multiplication

### Community 64 - "Community 64"
Cohesion: 0.40
Nodes (5): Practice Generation — Hint-Gated Experience Wrapper  Hints unlock one at a time., Apply the hint-gated experience wrapper.      Sets problem.experience to "hint_g, Increment hints_revealed by 1 and return the updated problem.      If the proble, reveal_next_hint(), wrap_hint_gated()

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (5): is_mastered(), Practice Generation — Mastery Drill Experience Wrapper  Rapid-fire practice unti, Return an updated session state after one answer.      Correct answer  → consecu, Return True if the student has reached mastery.      Args:         session_state, update_drill_state()

### Community 66 - "Community 66"
Cohesion: 0.67
Nodes (3): 12. Database Model, New Table: `node_intro_views`, Node Key Format

### Community 67 - "Community 67"
Cohesion: 0.67
Nodes (3): 3. Content Types, Type A: Perseus-Derived (Dynamic, Automatable), Type B: Authored Augmentations (Static, Validated)

### Community 68 - "Community 68"
Cohesion: 0.50
Nodes (3): ParentLoginRequest, parent_login(), Parent Login. Auto-registers alphanumeric password on first run for developer co

### Community 69 - "Community 69"
Cohesion: 0.29
Nodes (10): _build_traps(), _build_visual_params(), format_clock(), fmt_clock.py — ClockSet visual formatter  Produces a FormattedProblem with clock, Generate clock visual_params deterministically from (grade, diff_level, rng)., Build a ClockSet FormattedProblem from a QuestionContext.      interaction_mode, Return trap dict mirroring visual_skeletons._traps_clock_set logic.      Keys: h, Extract up to 3 distinct trap time-strings (excluding the correct answer). (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.27
Nodes (10): _answer_from_bond(), _build_bond(), _build_traps(), format_number_bond(), _max_whole(), fmt_number_bond.py — NumberBond visual formatter  NEW formatter — gap analysis a, Return up to 3 distractor values.      Traps:         wrong_op   — student adds, Build a NumberBond FormattedProblem from a QuestionContext.      interaction_mod (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.25
Nodes (10): _build_sequence(), _build_traps(), _choose_missing_indices(), format_pattern_sequence(), fmt_pattern_sequence.py — PatternSequence visual formatter  Refactored from visu, Select which indices to blank out.     Never blank the first two terms (anchors), Return list of distractor values for the primary missing term.      Traps:, Build a PatternSequence FormattedProblem from a QuestionContext.      interactio (+2 more)

### Community 72 - "Community 72"
Cohesion: 0.67
Nodes (3): PlacementSkipRequest, Bypasses placement for a subject and seeds based on student grade., skip_placement()

### Community 73 - "Community 73"
Cohesion: 0.36
Nodes (9): Attempt, NodeIntroView, ParentAccount, QuestionFlag, SkillEdge, SkillNode, SpacedRepetition, TelemetrySession (+1 more)

### Community 74 - "Community 74"
Cohesion: 0.27
Nodes (9): generate_hints(), generate_params(), _make_expanded_form(), num_to_tagalog_style_english_words(), DNA: Number Reading / Writing (Number & Algebra)  Covers MATATAG grades 1–3 nume, Generate a number reading/writing problem.      Returns:         {             ", Return 2–4 step-by-step hints for a number reading/writing problem., Convert a positive integer (1–10000) to Filipino math word style English.      E (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.27
Nodes (9): generate_hints(), generate_params(), _ordinal_suffix(), _ordinal_word(), DNA: Ordinal Numbers (Number & Algebra)  Static-bank DNA. Item pool is authored, Static-bank generator: pick a template and fill in a random ordinal value., Return 2–4 step-by-step hints for an ordinal number problem., Return '1st', '2nd', '3rd', '4th', … for any positive integer. (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.67
Nodes (3): StudentLoginRequest, PIN-based Student login endpoint., student_login()

### Community 77 - "Community 77"
Cohesion: 0.67
Nodes (3): TelemetrySessionUpdateRequest, Updates statistics in the telemetry logs database., update_telemetry_session()

### Community 78 - "Community 78"
Cohesion: 0.29
Nodes (9): _build_pure_equation(), _distractor_label(), _distractor_value(), format_error_detect(), _pick_actor(), Textual Formatter — Error Detection ("Check the Work")  Presents a worked proble, Deterministically pick an actor name from the rotation using the seed., Build a pure equation string for the actor's work display. (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (9): _build_traps(), _build_visual_params(), format_bar_chart(), _grade_scale(), _pick_categories(), fmt_bar_chart.py — BarChart visual formatter  Produces a FormattedProblem with b, Build BarChart visual_params.      visual_params keys:         categories     —, Build a BarChart FormattedProblem from a QuestionContext.      interaction_mode (+1 more)

### Community 80 - "Community 80"
Cohesion: 0.31
Nodes (9): _build_traps(), _build_visual_params(), _days_in_month(), format_calendar(), fmt_calendar.py — Calendar visual formatter  Produces a FormattedProblem with ca, Build a Calendar FormattedProblem from a QuestionContext.      interaction_mode, Return English day-of-week name for a date using stdlib datetime., Build Calendar visual_params.      Grade 1–2: date-selection tasks only (click t (+1 more)

### Community 81 - "Community 81"
Cohesion: 0.29
Nodes (9): _build_traps(), format_fraction_model(), _pick_fraction(), _pick_model_type(), fmt_fraction_model.py — FractionModel visual formatter  NEW formatter — no exist, Build a FractionModel FormattedProblem from a QuestionContext.      interaction_, Return (numerator, denominator) appropriate for the grade.      G1: unit fractio, Return up to 3 pedagogically meaningful wrong answers (fraction strings).      T (+1 more)

### Community 82 - "Community 82"
Cohesion: 0.29
Nodes (9): _build_shapes(), _correct_answer_and_traps(), format_shape_board(), fmt_shape_board.py — ShapeBoard visual formatter  Refactored from visual_skeleto, Build a ShapeBoard FormattedProblem from a QuestionContext.      interaction_mod, Sample `count` shapes appropriate for the grade.      G1-2: triangles, squares,, Return (correct_answer, traps_list, question_detail).      question_detail: extr, _select_question_type() (+1 more)

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (9): _build_params(), _build_traps(), _correct_answer(), format_ten_frame(), fmt_ten_frame.py — TenFrame visual formatter  NEW formatter — gap analysis addit, Return up to 3 distractor values.      Traps:         count_all      — total cel, Build a TenFrame FormattedProblem from a QuestionContext.      Grade band: G1-G2, Generate ten-frame parameters.      G1: single frame (1-10), simple count_filled (+1 more)

### Community 92 - "Community 92"
Cohesion: 0.28
Nodes (8): _build_expression_str(), _evaluate_left_to_right(), generate_hints(), generate_params(), DNA: Order of Operations (Number & Algebra)  G3 only — addition and subtraction, Generate an order-of-operations problem (G3 only, + and − left to right).      R, Return 2–4 step-by-step hints for an order-of-operations problem., Evaluate an expression left to right given operands and operator list.

### Community 98 - "Community 98"
Cohesion: 0.31
Nodes (8): _build_ruler_params(), _build_traps(), format_ruler_measure(), fmt_ruler_measure.py — RulerMeasure visual formatter  NEW formatter — partial an, Build a RulerMeasure FormattedProblem from a QuestionContext.      interaction_m, Generate ruler + object placement for the given grade.      G1:   non-standard u, Return up to 3 distractor values.      Traps:         misread_start   — student, _stem()

### Community 102 - "Community 102"
Cohesion: 0.32
Nodes (7): extract_constraints(), extract_numeric_limit(), has_constraint(), Constraint Extractor Module  Parses dimensional constraints from MATATAG compete, Extract all dimensional constraints from a competency text.          Args:, Quick extraction of just the numeric limit.          Returns:         Numeric li, Check if a competency has a specific constraint type.          Args:         com

### Community 105 - "Community 105"
Cohesion: 0.32
Nodes (7): _detect_input_type(), format_numeric_input(), _numeric_bounds(), Textual Formatter — Numeric Input (Free-Entry)  Refactored from visual_skeletons, Classify the correct answer into integer, decimal, or fraction., Derive min_value / max_value from correct answer and available distractors., Format a QuestionContext as a free-entry numeric input problem.      format_data

### Community 107 - "Community 107"
Cohesion: 0.32
Nodes (7): Practice Generation — Compatibility & Registry Coverage Validation  Verifies tha, Verify bidirectional coverage between the knowledge graph and NODE_TO_DNA,     a, Run all compatibility and coverage checks and print a summary.      Returns:, Validate every entry in the COMPATIBILITY table.      Checks:       1. Each DNA, validate_all(), validate_compatibility_table(), validate_registry_coverage()

### Community 108 - "Community 108"
Cohesion: 0.36
Nodes (7): _build_traps(), format_fraction_shade(), _pick_params(), fmt_fraction_shade.py — FractionShade visual formatter  NEW formatter — gap anal, Build a FractionShade FormattedProblem from a QuestionContext.      interaction_, Return up to 3 distractor fraction strings.      Traps:         swap_nd        —, _stem()

### Community 132 - "Community 132"
Cohesion: 0.40
Nodes (3): Content Generation Rules, Core Persona: The Master K-12 Educator, Engineering & Verification Constraints

## Knowledge Gaps
- **151 isolated node(s):** `Config`, `name`, `private`, `version`, `type` (+146 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FormattedProblem` connect `Community 52` to `Community 3`, `Community 11`, `Community 13`, `Community 30`, `Community 39`, `Community 50`, `Community 51`, `Community 61`, `Community 63`, `Community 64`, `Community 65`, `Community 69`, `Community 70`, `Community 71`, `Community 78`, `Community 79`, `Community 80`, `Community 81`, `Community 82`, `Community 83`, `Community 85`, `Community 98`, `Community 105`, `Community 108`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `get_cache()` connect `Community 27` to `Community 0`, `Community 1`, `Community 5`, `Community 22`, `Community 59`, `Community 28`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `DNA` connect `Community 48` to `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 10`, `Community 19`, `Community 20`, `Community 24`, `Community 25`, `Community 29`, `Community 35`, `Community 42`, `Community 52`, `Community 54`, `Community 55`, `Community 74`, `Community 75`, `Community 92`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **What connects `Constraint Extractor Module  Parses dimensional constraints from MATATAG compete`, `Extract all dimensional constraints from a competency text.          Args:`, `Quick extraction of just the numeric limit.          Returns:         Numeric li` to the rest of the system?**
  _598 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08994708994708994 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._