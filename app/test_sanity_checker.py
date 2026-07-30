from sanity_checker import check_result_sanity


def test_clean_result_passes():
    rows = [{"name": "Alice", "order_count": 2}, {"name": "Bob", "order_count": 1}]
    result = check_result_sanity(rows)
    assert result.passed
    assert result.issues == []


def test_null_heavy_column_fails():
    rows = [
        {"name": "Alice", "order_count": None},
        {"name": "Bob", "order_count": None},
        {"name": "Priya", "order_count": None},
        {"name": "Real", "order_count": 3},
    ]
    result = check_result_sanity(rows)
    assert not result.passed
    assert any("NULL" in issue for issue in result.issues)


def test_row_count_upper_bound_catches_fanout():
    rows = [{"name": f"cust{i}", "total": 10} for i in range(9)]
    result = check_result_sanity(rows, expected_row_count_upper_bound=3)
    assert not result.passed
    assert any("fan-out" in issue for issue in result.issues)


def test_empty_result_flagged_but_not_failed():
    result = check_result_sanity([])
    assert result.passed
    assert len(result.issues) == 1


def test_negative_amount_fails():
    rows = [{"name": "Alice", "total_amount": -50.0}]
    result = check_result_sanity(rows)
    assert not result.passed