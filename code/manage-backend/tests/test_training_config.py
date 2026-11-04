import pytest

from app.core.exceptions import AppException
from app.services import training_config_service as svc
from app.services.smart_training.core import DEFAULT_PARAMS


def test_smart_defaults_roundtrip():
    out = svc.validate_smart_params({})
    assert out["slots"] == DEFAULT_PARAMS["slots"]
    assert out["review_intervals_days"] == [1, 3, 7, 14]


def test_smart_partial_override_keeps_rest():
    out = svc.validate_smart_params({"temperature": 0.5, "weights": {"intent": 2}})
    assert out["temperature"] == 0.5
    assert out["weights"]["intent"] == 2 and out["weights"]["kp_weak"] == 1.0


@pytest.mark.parametrize("bad", [
    {"temperature": 9},
    {"slots": {"weak": 0, "strong": 0, "review": 0}},
    {"review_intervals_days": []},
    {"prior": [1]},
    {"intent_min_slots": 1.5},
])
def test_smart_invalid(bad):
    with pytest.raises(AppException):
        svc.validate_smart_params(bad)


def test_ratio_rules():
    assert svc._ratio(None, svc.DIFFICULTIES, "难度比例") is None
    assert svc._ratio({"basic": 1, "advanced": 0}, svc.DIFFICULTIES, "难度比例") == {"basic": 1, "advanced": 0}
    with pytest.raises(AppException):
        svc._ratio({"basic": 0, "advanced": 0}, svc.DIFFICULTIES, "难度比例")
    with pytest.raises(AppException):
        svc._ratio({"nope": 1}, svc.DIFFICULTIES, "难度比例")
