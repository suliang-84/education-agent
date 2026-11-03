from datetime import datetime, timezone

import pytest

from app.services.smart_training.intents import parse_llm_json, validate_intents

AT = datetime(2026, 11, 3, tzinfo=timezone.utc)


def test_parse_plain_and_wrapped():
    assert parse_llm_json('{"intents":[],"summary":"x"}')["summary"] == "x"
    assert parse_llm_json('好的：\n```json\n{"intents":[{"kp_id":1,"confidence":0.9}],"summary":""}\n```')["intents"][0]["kp_id"] == 1


def test_parse_garbage():
    with pytest.raises(Exception):
        parse_llm_json("没有任何 JSON")


def test_validate_filters_and_clamps():
    raw = [{"kp_id": 1, "confidence": 0.9}, {"kp_id": 1, "confidence": 0.5}, {"kp_id": 99, "confidence": 1},
           {"kp_id": "2", "confidence": 3}, {"kp_id": 3}, "bad", {"kp_id": 4, "confidence": 0}]
    out = validate_intents(raw, {1, 2, 3, 4}, AT)
    assert {o["kp_id"]: o["confidence"] for o in out} == {1: 0.9, 2: 1.0}


def test_validate_empty():
    assert validate_intents([], {1}, AT) == [] and validate_intents(None, {1}, AT) == []
