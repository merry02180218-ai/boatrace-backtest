# Reproducible opponent v3 specification
# Source/frozen head population and direct ordered-pair implementation are inherited verbatim from research/rebuild_3head_opponent_v1.py.
# February-only GroupKFold(5) comparison:
# - direct ordered-pair LogisticRegression
# - decomposed candidate P(second)*P(third)
# C grid: [0.1,0.25,0.5,1,2,4]
# Selection priority: mean top3 true-pair capture, then pair AUC.
# Candidate decomposed features: lane one-hot; own nine card metrics; candidate-minus-boat3 gaps.
# Both candidate models: median imputer -> StandardScaler -> LogisticRegression(class_weight='balanced', solver='liblinear', max_iter=2000, random_state=0).
# Pair score = P(second=a)*P(third=b), a!=b.
# Deterministic tie break: score desc, second asc, third asc; exactly 3 tickets/race.
# Frozen February CV result selected DIRECT C=0.25 before March settlement.
# This file records the exact experiment contract; v1 contains the executable direct implementation used by the frozen winner.
