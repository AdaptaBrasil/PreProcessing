import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Point, box

import utilities as u
from fix_legends_from_csv import verify_list
from truncate_values import process_cell_value, truncate_float


# --- truncation ------------------------------------------------------------

@pytest.mark.parametrize("value, places, expected", [
    (1.23456, 2, 1.23),
    (0.29, 2, 0.29),        # floor(0.29 * 100) would give 0.28
    (-1.239, 2, -1.23),     # toward zero, not floor
    (5, 2, 5.0),
    (0.0, 2, 0.0),
    (1e-05, 5, 1e-05),
])
def test_trunc(value, places, expected):
    assert u.trunc(value, places) == expected
    assert truncate_float(value, places) == expected


def test_process_cell_value():
    assert process_cell_value(3.0, 2) == 3
    assert process_cell_value(0.239, 2) == 0.23
    assert process_cell_value("DI", 2) == "DI"
    assert process_cell_value("0.567", 2) == 0.56
    with pytest.raises(ValueError):
        process_cell_value("abc", 2)


def test_trunc_fix():
    assert u.trunc_fix(1.0, 2) == "1.00"
    assert u.trunc_fix(3, 2) == "3.00"
    assert u.trunc_fix(1.25, 2) == "1.25"


# --- legend intervals --------------------------------------------------------

def _is_contiguous(pairs, step=0.01):
    return all(round(nxt[0] - cur[1], 2) == step for cur, nxt in zip(pairs, pairs[1:]))


@pytest.mark.parametrize("low, high", [(0.0, 1.0), (-0.5, 0.8), (0.12, 0.97), (-3.2, -0.4), (0, 100), (2.5, 7.25)])
def test_generate_value_pairs_is_contiguous(low, high):
    pairs = u.generate_value_pairs(low, high, 5)
    assert len(pairs) == 5
    assert pairs[0][0] == low and pairs[-1][1] == high
    assert _is_contiguous(pairs)
    assert all(lo < hi for lo, hi, _ in pairs)


def test_generate_value_pairs_example():
    assert [p[:2] for p in u.generate_value_pairs(0, 1, 5)] == [
        [0, 0.19], [0.2, 0.39], [0.4, 0.59], [0.6, 0.79], [0.8, 1]]


@pytest.mark.parametrize("low, high", [(0.0, 1.0), (-0.5, 0.8), (0.12, 0.97), (0, 100)])
def test_continuous_intervals_validate(low, high):
    intervals = u.generate_continuous_intervals(low, high, 5)
    assert len(intervals) == 5
    assert u.validate_continuous_intervals(intervals) == (True, [])


def test_validate_continuous_intervals_reports_gaps():
    ok, errors = u.validate_continuous_intervals([(0.0, 0.19), (0.25, 0.5)])
    assert not ok and "Not continuous" in errors[0]


def test_generate_continuous_intervals_rejects_bad_input():
    with pytest.raises(ValueError):
        u.generate_continuous_intervals(1, 1, 5)
    with pytest.raises(ValueError):
        u.generate_continuous_intervals(0, 1, 0)


def test_verify_list_respects_sign():
    assert verify_list([[-1.0, -0.51], [-0.5, 0.0]], 0.01)
    # -0.5 vs expected 0.5 used to pass because only absolute values were compared
    assert not verify_list([[-1.0, 0.49], [-0.5, 0.0]], 0.01)


# --- colors / QML -------------------------------------------------------------

def test_convert_to_hexadecimal():
    assert u.convert_to_hexadecimal("255,131,0,255") == "#FF8300"
    assert u.convert_to_hexadecimal("1,2,3") is None


def test_hex_to_rgba_round_trip():
    from generate_qml_from_legends import format_number, hex_to_rgba
    assert hex_to_rgba("#FF8300", 255) == "255,131,0,255"
    assert u.convert_to_hexadecimal(hex_to_rgba("#02C650", 255)) == "#02C650"
    assert format_number(0.1 + 0.2) == "0.3"
    assert format_number(0.0) == "0.0"


def test_qml_round_trip(tmp_path):
    """A QML written by generate_qml_from_legends is read back by parse_qml_file."""
    import generate_qml_from_legends as g

    legend = pd.DataFrame({
        'LEGEND_ID': [1, 1, 1],
        'SYMBOL': ['0', '1', 'Dado indisponível'],
        'MINVALUE': [0.0, 0.5, None],
        'MAXVALUE': [0.49, 1.0, None],
        'COLOR': ['#F40000', '#02C650', '#DCDCDC'],
    })
    assert g.validate_legend_values(legend)
    path = tmp_path / "1.qml"
    g.write_qml(str(path), legend)

    text = path.read_text(encoding='utf-8')
    assert 'label="0,0 - 0,49"' in text and "Dado indisponível" in text

    # Numeric classes are read back; the 'Dado indisponivel' class is skipped
    qml = u.parse_qml_file(str(path))
    assert sorted(qml['ranges']) == [0, 1] and sorted(qml['symbols']) == [0, 1]
    assert qml['ranges'][0]['minvalue'] == 0.0 and qml['ranges'][1]['maxvalue'] == 1.0
    assert qml['symbols'][1]['color'] == '#02C650'


def test_validate_legend_values_detects_gap():
    import generate_qml_from_legends as g
    legend = pd.DataFrame({'LEGEND_ID': [1, 1], 'SYMBOL': ['0', '1'],
                           'MINVALUE': [0.0, 0.6], 'MAXVALUE': [0.49, 1.0], 'COLOR': ['#000000'] * 2})
    assert not g.validate_legend_values(legend)


# --- geo helpers ------------------------------------------------------------

def test_polygon_parts():
    multi = MultiPolygon([box(0, 0, 1, 1), box(2, 2, 3, 3)])
    assert len(u.polygon_parts(multi)) == 2
    assert len(u.polygon_parts(box(0, 0, 1, 1))) == 1
    assert u.polygon_parts(Point(0, 0)) == []


def test_next_indicator_column_id():
    assert u.next_indicator_column_id(['objectid', 'geometry']) == 0
    assert u.next_indicator_column_id(['I_0', 'I_1', 'I_10', 'geometry']) == 11
    assert u.next_indicator_column_id(['I_x', 'II_3']) == 0


def test_find_indicator_column():
    df = pd.DataFrame({'name': ['a', 'b'], 'CL-ORIG': [0.1, 0.9], 'other': [5.0, 6.0]})
    assert u.find_indicator_column(['N_ORIG'], df) == 'CL-ORIG'   # hyphen used to break .query()
    assert u.find_indicator_column(['other'], df) == 'other'
    assert u.find_indicator_column([], pd.DataFrame({'x': [2.0]})) is None
