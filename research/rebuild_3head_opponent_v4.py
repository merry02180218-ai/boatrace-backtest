# Reproducible opponent v4 implementation contract
# Exact executed script SHA256: 296b8be435b81a1225904d5c99e5efa3befc32f048e35e9912e0f8760f3f9854
# Source: Run34754875342 / Artifact10317157868.
# Base executable logic is research/rebuild_3head_opponent_v1.py; direct ordered-pair LogisticRegression C=.25.
# February-only GroupKFold(5), grouped by race. March is evaluated only after winner frozen.
# Feature candidates tested: baseline67; no_lane_structure; no_st; no_national_strength; no_local; no_motor; no_boat; no_gap3; no_s_minus_t; no_pair_mean; performance_only; st_performance; performance_motor; core_nat23_st_motor23.
# Winner selection: mean February top3 capture desc, then AUC desc, with fold-SD <= 1.5x baseline fold-SD.
# Frozen winner: no_local (remove 当地勝率 and 当地2連対率 feature families), 55 features.
# Model: median imputation -> StandardScaler -> LogisticRegression(C=.25,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0).
# Tickets: exactly top 3 ordered pairs per race; tie break score desc, second asc, third asc.
# Deterministic output hash recorded in result JSON. Full executable source was run locally and its SHA above is the audit identity; this contract records all changed choices from v1.
