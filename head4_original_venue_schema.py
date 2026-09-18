#!/usr/bin/env python3
"""Venue-aware original-exhibition contract for HEAD4 live operation.

Pinned to the 1HEAD v351 live probe survey.
The avg key means the venue's published aggregate source is usable for orig_avg:
all published original channels must be numeric for all six boats.
"""
from __future__ import annotations

ORIG_REQUIRED={
    1:('avg','turn','straight'),2:('avg','turn','straight'),3:(),
    4:('avg','turn','straight'),5:('avg','turn','straight'),
    6:('avg','turn','straight'),7:('avg','turn','straight'),
    8:('avg','turn','straight'),9:(),
    10:('avg','turn','straight'),11:('avg','turn','straight'),
    12:('avg','turn'),13:('avg','turn'),
    14:('avg','turn','straight'),15:('avg','turn','straight'),
    16:('avg','turn','straight'),17:('avg','turn','straight'),
    18:('avg','turn'),19:('avg','turn','straight'),
    20:('avg','turn','straight'),21:('avg','turn','straight'),
    22:('avg','turn','straight'),23:('avg','turn','straight'),
    24:('avg','turn','straight'),
}

def required_orig(jcd:int)->tuple[str,...]:
    return ORIG_REQUIRED.get(int(jcd),('avg','turn','straight'))

def publishes_original(jcd:int)->bool:
    return bool(required_orig(jcd))
