from fulfilliq.exports import _json_safe


def test_json_safe_converts_non_finite_numbers_to_null():
    assert _json_safe({"rate": float("nan"), "nested": [float("inf"), 0.5]}) == {
        "rate": None,
        "nested": [None, 0.5],
    }
