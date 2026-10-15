#!/usr/bin/env python3
"""C4.2 transport adapter: separate R1 reasoning from final JSON, without repair.

Accept only: native JSON object, pure JSON object, one fenced JSON object,
or ONE initial <think>...</think> followed by either JSON form.
Never mine JSON from natural language or modify values.
"""
import json
import re

FENCE = re.compile(r"\A```(?:json)?[ \t]*\n(?P<body>.*?)\n```\Z", re.I | re.S)
THINK = re.compile(r"\A<think>(?P<reason>.*?)</think>[ \t\n\r]*(?P<final>.+)\Z", re.S)


def separate(value):
    """Return (parsed object or None, reasoning or None, transport metadata).
    Input MUST be the actual provider response field, not an invented concatenation.
    """
    if isinstance(value, dict):
        return value, None, {"ok":True,"format":"provider_object",
                             "had_think":False,"had_fence":False}
    if not isinstance(value, str):
        return None, None, {"ok":False,"format":"wrong_response_type",
                            "had_think":False,"had_fence":False}
    s = value.strip()
    reasoning = None
    had_think = False
    if "<think>" in s or "</think>" in s:
        m = THINK.fullmatch(s)
        if (not m or s.count("<think>") != 1 or s.count("</think>") != 1
                or "<think>" in m.group("reason") or "</think>" in m.group("reason")):
            return None, None, {"ok":False,"format":"invalid_reasoning_delimiter",
                                "had_think":True,"had_fence":False}
        reasoning = m.group("reason")
        s = m.group("final").strip()
        had_think = True
        if "<think>" in s or "</think>" in s:
            return None, reasoning, {"ok":False,"format":"reasoning_inside_final",
                                     "had_think":True,"had_fence":False}
    fence = FENCE.fullmatch(s)
    had_fence = bool(fence)
    if fence:
        s = fence.group("body")
    try:
        parsed = json.loads(s)
    except (TypeError,ValueError):
        return None, reasoning, {"ok":False,"format":"non_json_final",
                                 "had_think":had_think,"had_fence":had_fence}
    if not isinstance(parsed, dict):
        return None, reasoning, {"ok":False,"format":"not_json_object",
                                 "had_think":had_think,"had_fence":had_fence}
    return parsed, reasoning, {"ok":True,
                               "format":("think_plus_" if had_think else "")
                                        + ("single_fenced_json" if had_fence else "json"),
                               "had_think":had_think,"had_fence":had_fence}
