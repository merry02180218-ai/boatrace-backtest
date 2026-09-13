#!/usr/bin/env python3
"""Authoritative 1-head production profile.

Historical research modules remain frozen.  This profile records only the
currently adopted operating choices and is imported by production/regression
wrappers so old experiments stay reproducible.
"""

PROFILE_NAME = "1HEAD_PRODUCTION_20260914_HEAD078"

HEAD_MODEL = "v308"
HEAD_CUTOFF = 0.78
OPPONENT_MASS_MIN = 0.375

SECOND_MODEL = "v317_OUTER_L2_1"
THIRD_MODEL = "v318_DROPSTART_T0.1"
TICKET_POLICY = "v320_HYBRID"
TICKET_ALPHA = 0.70

EXHIBITION_MODEL = "v332_ATTACK_ENV_SOFT"
EXHIBITION_ENV_W = 0.10
EXHIBITION_Q = 0.65

# Frozen Feb-Aug regression identity from successful v337 audit.
EXPECTED_PASS_R = 276
EXPECTED_HEAD = 241
EXPECTED_EXACT3 = 119
EXPECTED_PASS_ID_SHA256 = "89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73"

# Original frozen anchor is retained as a regression sentinel, not production.
ANCHOR_HEAD_CUTOFF = 0.8073405637
ANCHOR_EXPECTED_PASS_R = 96
ANCHOR_EXPECTED_HEAD = 83
ANCHOR_EXPECTED_EXACT3 = 45
ANCHOR_PASS_ID_SHA256 = "8c97e8ae4ef7f444ad82ce91f6e8b6483c57181cce3ccdb56593863a533241fc"

SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD = True
