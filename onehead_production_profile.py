#!/usr/bin/env python3
"""Authoritative 1-head production profile.

Historical research modules remain frozen. This profile records only the
currently adopted operating choices and is imported by production/regression
wrappers so old experiments stay reproducible.
"""

PROFILE_NAME = "1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100"

HEAD_MODEL = "v308"
HEAD_CUTOFF = 0.78
OPPONENT_MASS_MIN = 0.375

SECOND_MODEL = "v317_OUTER_L2_1"
THIRD_MODEL = "v318_DROPSTART_T0.1"
TICKET_POLICY = "v320_HYBRID"
TICKET_ALPHA = 0.70

EXHIBITION_MODEL = "v332_ATTACK_ENV_SOFT_V345_ATTACKCORE"
EXHIBITION_ENV_W = 0.10
EXHIBITION_Q = 0.65

# LIVE operating profile adopted 2026-09-18 from the 441-cell joint ROI audit.
# Keep the historical production constants above frozen for reproducibility.
LIVE_OPERATION_PROFILE_NAME = "1HEAD_LIVE_20260918_HEAD079_MASS0375_ENV005_Q070"
LIVE_HEAD_CUTOFF = 0.790
LIVE_OPPONENT_MASS_MIN = 0.375
LIVE_EXHIBITION_ENV_W = 0.05
LIVE_EXHIBITION_Q = 0.70

# Stricter subset surfaced as 注目レース. It shares the same HEAD/exhibition
# settings as the basic LIVE profile and differs only by opponent mass.
WATCH_PROFILE_NAME = "1HEAD_WATCH_20260918_HEAD079_MASS0425_ENV005_Q070"
WATCH_HEAD_CUTOFF = 0.790
WATCH_OPPONENT_MASS_MIN = 0.425
WATCH_EXHIBITION_ENV_W = 0.05
WATCH_EXHIBITION_Q = 0.70

# Promoted LIVE WATCH ticket rerank, adopted 2026-09-18 after v353-v355 audit.
# Historical production sentinels above remain frozen; this only changes the
# LIVE ticket choice for WATCH races when the wall3 risk actually fires.
WALL3_LIVE_TICKET_PROFILE_NAME = "1HEAD_WATCH_WALL3_TICKET_V355_SCORE_A406_G2_300_G3_050"
WALL3_LIVE_TICKET_PROMOTED = True

# Backward-compatible alias retained for v356 research regression/history.
WALL3_SHADOW_PROFILE_NAME = WALL3_LIVE_TICKET_PROFILE_NAME
WALL3_SHADOW_ATTACK4_MIN = 0.60
WALL3_SHADOW_SECOND_G2 = 3.00
WALL3_SHADOW_THIRD_G3 = 0.50
WALL3_SHADOW_W_EX = 0.20
WALL3_SHADOW_W_ST = 0.40
WALL3_SHADOW_W_STRAIGHT = 0.25
WALL3_SHADOW_W_ORIG_AVG = 0.15


# Promoted LIVE post-wall3 5->6 ST ticket rerank, adopted 2026-09-18
# after v361-v363 robustness audits.
FIVE6_LIVE_TICKET_PROFILE_NAME = "1HEAD_5TO6_ST_TICKET_V363_SCORE6_060_STGAP040_G2_000_G3_075"
FIVE6_LIVE_TICKET_PROMOTED = True

# Backward-compatible alias retained for research/history fields.
FIVE6_SHADOW_PROFILE_NAME = FIVE6_LIVE_TICKET_PROFILE_NAME
FIVE6_SHADOW_SCORE6_MIN = 0.60
FIVE6_SHADOW_ST_GAP_MIN = 0.40
FIVE6_SHADOW_SECOND_G2 = 0.00
FIVE6_SHADOW_THIRD_G3 = 0.75


# Research-only LIVE stake shadow from v374-v376.
# Official stake remains 100 yen per formal ticket. When either already-formal
# post-exhibition overlay fires, shadow only doubles all three formal tickets.
LIVE_OFFICIAL_STAKE_YEN_PER_TICKET = 100
OVERLAY_STAKE_SHADOW_PROFILE_NAME = "1HEAD_OVERLAY_STAKE_SHADOW_V375_EITHER_2X"
OVERLAY_STAKE_SHADOW_MULTIPLIER = 2
OVERLAY_STAKE_SHADOW_RESEARCH_ONLY = True

# v345 adopted HEAD-side component weights. Historical names are retained for
# compatibility with frozen research modules.
ATTACK_CORE_VERSION = "v345"
ATTACK_CORE_W_ONE_EX = 0.40
ATTACK_CORE_W_ONE_ST = 0.25
ATTACK_CORE_W_ONE_STRAIGHT = 0.15
ATTACK_CORE_W_ONE_ORIG_AVG = 0.20

# v351 formally adopts the SECOND-side opponentCore coefficient selected in v350.
# The frozen v345 276-race HEAD selection remains unchanged.
OPPONENT_CORE_VERSION = "v351_OPPONENTCORE_G2_045_G3_100"
OPPONENT_CORE_SECOND_G2 = 0.45
OPPONENT_CORE_THIRD_G3 = 1.00

# Backward-compatible aliases for historical modules that still import the old
# constant names. New code must use the neutral OPPONENT_CORE_* names above.
OPPONENT_ATTACK_CORE_VERSION = OPPONENT_CORE_VERSION
OPPONENT_ATTACK_CORE_SECOND_G2 = OPPONENT_CORE_SECOND_G2
OPPONENT_ATTACK_CORE_THIRD_G3 = OPPONENT_CORE_THIRD_G3

# Formal v351 production sentinel. Jul/Aug remain NON_PRISTINE support-only;
# September outcomes must remain unread.
PRODUCTION_EXPECTED_PASS_R = 276
PRODUCTION_EXPECTED_HEAD = 241
PRODUCTION_EXPECTED_EXACT3 = 131
PRODUCTION_EXPECTED_PASS_ID_SHA256 = "08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd"
PRODUCTION_EXPECTED_TICKET_ID_SHA256 = "21631473d2a8b82f4fe93d18f8292d777837c26a47c408917fd8b722d1898cd7"

# Frozen v349 sentinel retained so historical production evidence stays explicit.
V349_EXPECTED_PASS_R = 276
V349_EXPECTED_HEAD = 241
V349_EXPECTED_EXACT3 = 130
V349_EXPECTED_PASS_ID_SHA256 = "08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd"
V349_EXPECTED_TICKET_ID_SHA256 = "50378499c439f3c13572f2ee5d4c012a812043fea34cf840e3aa47db4ebbec0c"

# Frozen v345 sentinel retained for historical v346/v347 regression code.
# CURRENT_EXPECTED_* aliases intentionally remain pointed at v345 so those
# historical wrappers stay reproducible without modification.
V345_EXPECTED_PASS_R = 276
V345_EXPECTED_HEAD = 241
V345_EXPECTED_EXACT3 = 121
V345_EXPECTED_PASS_ID_SHA256 = "08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd"
V345_EXPECTED_TICKET_ID_SHA256 = "bb5b7fd44245e616a1bc6455f15f2df1a59083f55196b78ac83d59abbf39daae"
CURRENT_EXPECTED_PASS_R = V345_EXPECTED_PASS_R
CURRENT_EXPECTED_HEAD = V345_EXPECTED_HEAD
CURRENT_EXPECTED_EXACT3 = V345_EXPECTED_EXACT3
CURRENT_EXPECTED_PASS_ID_SHA256 = V345_EXPECTED_PASS_ID_SHA256

# Backward-compatible pre-v345 sentinel used by historical v338 regression.
# Keep EXPECTED_* aliases frozen so old wrappers remain reproducible.
PRE_V345_EXPECTED_PASS_R = 276
PRE_V345_EXPECTED_HEAD = 241
PRE_V345_EXPECTED_EXACT3 = 119
PRE_V345_EXPECTED_PASS_ID_SHA256 = "89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73"
EXPECTED_PASS_R = PRE_V345_EXPECTED_PASS_R
EXPECTED_HEAD = PRE_V345_EXPECTED_HEAD
EXPECTED_EXACT3 = PRE_V345_EXPECTED_EXACT3
EXPECTED_PASS_ID_SHA256 = PRE_V345_EXPECTED_PASS_ID_SHA256

# Original frozen anchor is retained as a regression sentinel, not production.
ANCHOR_HEAD_CUTOFF = 0.8073405637
ANCHOR_EXPECTED_PASS_R = 96
ANCHOR_EXPECTED_HEAD = 83
ANCHOR_EXPECTED_EXACT3 = 45
ANCHOR_PASS_ID_SHA256 = "8c97e8ae4ef7f444ad82ce91f6e8b6483c57181cce3ccdb56593863a533241fc"

JUL_AUG_STATUS = "NON_PRISTINE_SUPPORT_ONLY"
SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD = True
