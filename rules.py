"""Built-in conversion rules stored in the program."""

from __future__ import annotations

import re

from engine import GlobalRule, LineRule, Rule, apply_rules

# Whole-line rules for rungs that need structural changes (match anchors from old format).
_LINE_RULES: list[LineRule] = [
    LineRule(
        find="H_WIRE;\tMASK_COMP_WORD_30 2 DEVHLD1[0],L DP_FFFF[0],G",
        replace=(
            "H_WIRE;\tMASK_COMP_WORD 2 DEVHLD1[0],L DP_FFFF[0],G MASK3,L,%R05853 1 ** "
            "MASK1,L,%R05861 MASK1,L,%R05861;\tC+1;\tH_WIRE;\tH_WIRE;\tH_WIRE;\tH_WIRE;\t"
            "H_WIRE;\tH_WIRE;\tCOIL T00033,G,%T00033;\tR+;\tC+1;\tC+1;\tV_WIRE;\tC-;\t"
            "H_WIRE;\tEND_RUNG;"
        ),
    ),
    LineRule(
        find="NCCON T00033,G,%T00033;\tTMR_HUNDS_30 MODFLTS_TMR1",
        replace=(
            "NCCON T00033,G,%T00033;\tTMR_HUNDS MODFLTS_TMR1,G,%R05867 270 **;\tH_WIRE;\t"
            "H_WIRE;\tMOVE_INT 2 DEVHLD1,L,%R05851 GBC_D00,L,%M00257;\tEND_RUNG;"
        ),
    ),
    LineRule(
        find="CONTCON;\tARRAY_MOVE_BYTE 30 DP_ZERO_BYTE,G,%R05863",
        replace=(
            "CONTCON;\tARRAY_MOVE_DINT 30 DP_ZERO_BYTE,G,%R05863 1 WRKRG03,G,%R05859 1 "
            "MOD_FLT_START_BYTE,G,%M00289;\tH_WIRE;\tH_WIRE;\tH_WIRE;\tH_WIRE;\tH_WIRE;\t"
            "H_WIRE;\tH_WIRE;\tJUMPN MODFLTS2;\tEND_RUNG;"
        ),
    ),
    LineRule(
        find="NOCON #IO_FLT,G,%SC0011;\tGE_INT_30 RAW_DROP_NO,G,%R05888 1 RAW_DROP_NO,G,%R05888;",
        replace=(
            "NOCON #IO_FLT,G,%SC0011;\tGE_INT RAW_DROP_NO,G,%R05888 1 **;\tC+1;\tH_WIRE;\t"
            "LE_INT RAW_DROP_NO,G,%R05888 12 **;\tC+1;\tH_WIRE;\tH_WIRE;\tH_WIRE;\tCONTCOIL;\t"
            "R+;\tC+1;\tC+1;\tV_WIRE;\tC-;\tH_WIRE;\tC+1;\tC+1;\tV_WIRE;\tC-;\tH_WIRE;\tEND_RUNG;"
        ),
    ),
    LineRule(
        find="CONTCON;\tEQ_INT_30 GROUP_NO,G,%R05896 3 FLT_CATG,G,%R05893;",
        replace=(
            "CONTCON;\tEQ_INT GROUP_NO,G,%R05896 3 **;\tC+1;\tH_WIRE;\tEQ_INT FLT_CATG,G,%R05893 142 **;\t"
            "C+1;\tH_WIRE;\tH_WIRE;\tH_WIRE;\tCONTCOIL;\tR+;\tC+1;\tC+1;\tV_WIRE;\tC-;\tH_WIRE;\t"
            "C+1;\tC+1;\tV_WIRE;\tC-;\tH_WIRE;\tEND_RUNG;"
        ),
    ),
]

# Known global token replacements applied after line rules.
_GLOBAL_RULES: list[GlobalRule] = [
    GlobalRule(old="OR_WORD_30", new="OR_WORD 1"),
    GlobalRule(old="NOT_WORD_30", new="NOT_WORD 1"),
    GlobalRule(old="XOR_WORD_30", new="XOR_WORD 1"),
    GlobalRule(old="AND_WORD_30", new="AND_WORD 1"),
    GlobalRule(old="MASK_COMP_WORD_30", new="MASK_COMP_WORD"),
]

# Catch remaining *_WORD_30 instructions not listed above.
_WORD_30_PATTERN = re.compile(r"\b([A-Z][A-Z0-9_]*_WORD)_30\b")


def get_rules() -> list[Rule]:
    """Return all built-in rules in apply order."""
    return [*_LINE_RULES, *_GLOBAL_RULES]


def _apply_word_30_fallbacks(text: str) -> str:
    """Convert any remaining *_WORD_30 tokens using the standard operand pattern."""

    def replace(match: re.Match[str]) -> str:
        instruction = match.group(1)
        if instruction == "MASK_COMP_WORD":
            return "MASK_COMP_WORD"
        return f"{instruction} 1"

    return _WORD_30_PATTERN.sub(replace, text)


def convert(text: str) -> str:
    """Apply built-in rules, then generic fallbacks for unmatched _30 instructions."""
    result = apply_rules(text, get_rules())
    return _apply_word_30_fallbacks(result)
