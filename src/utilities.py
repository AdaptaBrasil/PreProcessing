#!/usr/bin/env python
# coding: utf-8
"""Shared helpers for the PreProcessing scripts.

Heavy libraries (geopandas, rasterio, matplotlib, seaborn, scikit-learn) are
imported inside the functions that need them, so scripts that only build
legends start quickly.
"""

from __future__ import annotations

import os
import re
from decimal import ROUND_DOWN, Decimal, InvalidOperation, localcontext
from typing import List, Optional, Tuple


def version_all_libraries():
    import geopandas as gpd
    import matplotlib
    import openpyxl as xl
    import pandas as pd
    import rasterio as rio
    import seaborn as sns

    print("Geopandas version:", gpd.__version__)
    print("Rasterio version:", rio.__version__)
    print("Pandas version:", pd.__version__)
    print("Openpyxl version:", xl.__version__)
    print("Seaborn version:", sns.__version__)
    print("Matplotlib version:", matplotlib.__version__)


# ---------------------------------------------------------------------------
# Number / interval helpers
# ---------------------------------------------------------------------------

def generate_continuous_intervals(min_value: float, max_value: float, n_terms: int) -> List[Tuple[float, float]]:
    """
    Generate n continuous intervals from min_value to max_value.

    Each interval follows the pattern where the next minimum value is
    the previous maximum value plus 0.01, ensuring continuity.

    Raises:
        ValueError: If n_terms <= 0 or min_value >= max_value
    """
    if n_terms <= 0:
        raise ValueError("Number of terms must be greater than 0")

    if min_value >= max_value:
        raise ValueError("Minimum value must be less than maximum value")

    interval_size = (max_value - min_value) / n_terms

    intervals: List[Tuple[float, float]] = []
    current_min = min_value

    for i in range(n_terms):
        if i == n_terms - 1:  # Last interval
            current_max = max_value
        else:
            current_max = round(current_min + interval_size, 2)

        intervals.append((current_min, current_max))

        # Next minimum is current maximum + 0.01 (continuous pattern)
        current_min = round(current_max + 0.01, 2)

    return intervals


def validate_continuous_intervals(intervals: List[Tuple[float, float]]) -> Tuple[bool, List[str]]:
    """
    Validate that each interval starts exactly 0.01 after the previous one ends
    and that min < max for every interval.

    Returns:
        (is_valid, error_messages)

    Raises:
        ValueError: If intervals list is empty
    """
    if not intervals:
        raise ValueError("Intervals list cannot be empty")

    errors: List[str] = []
    prev_max_val: Optional[float] = None

    for i, (min_val, max_val) in enumerate(sorted(intervals, key=lambda x: x[0])):
        if min_val >= max_val:
            errors.append(
                f"Interval {i + 1}: Minimum value ({min_val}) must be less than maximum value ({max_val})"
            )

        if prev_max_val is not None:
            try:
                if Decimal(str(min_val)) - Decimal(str(prev_max_val)) != Decimal("0.01"):
                    expected_min = Decimal(str(prev_max_val)) + Decimal("0.01")
                    errors.append(
                        f"Interval {i + 1}: Not continuous. Minimum value {min_val} should be {expected_min} to follow previous maximum value"
                    )
            except InvalidOperation:
                errors.append(f"Interval {i + 1}: Invalid numeric values for continuity validation")

        prev_max_val = max_val

    return len(errors) == 0, errors


def trunc(value, decimal_places):
    """Truncate (round toward zero) to `decimal_places`, avoiding float artefacts.

    trunc(1.23456, 2) -> 1.23, trunc(0.29, 2) -> 0.29, trunc(-1.239, 2) -> -1.23
    """
    quantum = Decimal(1).scaleb(-decimal_places)
    with localcontext() as ctx:
        ctx.prec = 80  # room for many decimal places on large numbers
        return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_DOWN)) + 0.0  # +0.0 turns -0.0 into 0.0


def trunc_fix(value, decimal_places):
    """Pad a number's string form to `decimal_places` decimals (1.0 -> '1.00')."""
    my_value = str(value)
    if '.' in my_value:
        partes = my_value.split('.')
        if len(partes[1]) < decimal_places:
            my_value = partes[0] + '.' + partes[1].ljust(decimal_places, '0')
    else:
        my_value = my_value + '.' + '0' * decimal_places
    return my_value


def _decimal_places(value) -> int:
    text = format(Decimal(repr(float(value))), 'f')  # handles '1e-05' too
    return len(text.split('.')[1]) if '.' in text else 0


def generate_value_pairs_fixed_zero(a1, an, numero_termos):
    """Split [a1, an] into `numero_termos` classes, forcing 0 to be a class
    boundary when the range crosses zero. Callers are expected to clean the
    result up afterwards (see fix_legends_from_csv.py)."""
    numero_termos += 1

    # Incluir o zero se o intervalo tiver um número negativo e um positivo
    if a1 < 0 and an > 0:
        razao_negativa = -a1 / (numero_termos // 2)
        razao_positiva = an / ((numero_termos + 1) // 2)
        termos_negativos = [a1 + i * razao_negativa for i in range(numero_termos // 2)]
        termos_positivos = [i * razao_positiva for i in range((numero_termos + 1) // 2)]
        termos = termos_negativos + termos_positivos
    else:
        razao = (an - a1) / (numero_termos - 1)
        termos = [a1 + i * razao for i in range(numero_termos)]

    valores = []
    for i in range(len(termos) - 1):
        valor1 = termos[i]
        # Subtract 1 unit at twice the boundary's precision (0.2 -> 0.19) and
        # truncate there. (The old trunc() multiplied by 100**n, i.e. truncated
        # to 2n places; this keeps that behaviour explicitly.)
        casas = _decimal_places(termos[i + 1])
        valor2 = trunc(termos[i + 1] - 100 ** (-casas), 2 * casas)
        valores.append([valor1, valor2, valor2 - valor1])

    valores[-1][1] = an
    valores[0][0] = a1
    return valores


def generate_value_pairs(a1, an, numero_termos, step=0.01):
    """Split [a1, an] into `numero_termos` contiguous classes with 2-decimal
    boundaries, where each class ends `step` below the start of the next one:
    (0, 1, 5) -> [0, 0.19], [0.2, 0.39], [0.4, 0.59], [0.6, 0.79], [0.8, 1.0].

    Returns a list of [min, max, max - min].
    """
    razao = (an - a1) / numero_termos
    starts = [a1] + [round(a1 + i * razao, 2) for i in range(1, numero_termos)]
    valores = []
    for i, start in enumerate(starts):
        end = an if i == numero_termos - 1 else round(starts[i + 1] - step, 2)
        valores.append([start, end, end - start])
    return valores


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

def convert_to_hexadecimal(color_str):
    """'255,0,0,255' -> '#FF0000' (alpha dropped). Returns None if not RGBA."""
    rgba_values = color_str.split(',')
    if len(rgba_values) != 4:
        return None
    r, g, b, _a = map(int, rgba_values)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def generate_color(i, a):
    # Base color from 'a' modulo 3 (red, green, blue), lightened by 'i'
    color_base = a % 3
    r_base = 255 if color_base == 0 else 0
    g_base = 255 if color_base == 1 else 0
    b_base = 255 if color_base == 2 else 0

    intensity_increment = 59
    r = min(255, r_base + i * intensity_increment)
    g = min(255, g_base + i * intensity_increment)
    b = min(255, b_base + i * intensity_increment)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


# ---------------------------------------------------------------------------
# QML (QGIS style) parsing
# ---------------------------------------------------------------------------

def parse_qml_file(qml_file_path):
    """Read a graduated-renderer QML file.

    Returns {'ranges': {symbol: {...}}, 'symbols': {symbol: {'color': '#RRGGBB'}}},
    or empty dicts when the file has no <renderer-v2>. Classes with a
    non-numeric symbol or empty bounds (e.g. "Dado indisponivel") are skipped.
    """
    import xml.etree.ElementTree as ET

    qml = {'ranges': {}, 'symbols': {}}
    renderer = ET.parse(qml_file_path).getroot().find('renderer-v2')
    if renderer is None:
        return qml

    ranges_element = renderer.find('ranges')
    if ranges_element is not None:
        for range_element in ranges_element.findall('range'):
            try:
                symbol = int(range_element.get('symbol'))
                float(range_element.get('lower')), float(range_element.get('upper'))
            except (TypeError, ValueError):
                continue
            qml['ranges'][symbol] = {
                'label': range_element.get('label'),
                'minvalue': float(range_element.get('lower')),
                'maxvalue': float(range_element.get('upper')),
                'symbol': symbol,
            }

    symbols_element = renderer.find('symbols')
    if symbols_element is not None:
        for symbol_element in symbols_element.findall('symbol'):
            try:
                symbol_id = int(symbol_element.get('name'))
            except (TypeError, ValueError):
                continue
            if symbol_id not in qml['ranges']:
                continue
            properties = {}
            options = symbol_element.find('layer/Option')
            if options is not None:
                for option in options.findall('Option'):
                    if option.get('name') == 'color':
                        properties['color'] = convert_to_hexadecimal(option.get('value'))
                        properties['symbol_id'] = symbol_id
                        break
            qml['symbols'][symbol_id] = properties
    return qml


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def generate_histogram(data: list, title: str, output_file: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import PercentFormatter

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_title(label="Histograma \n" + title + '\n')
    _values, _bins, bars = ax.hist(data, bins=10, weights=np.ones(len(data)) / len(data))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylim([0, 1])
    ax.set_xlim([-1, 1])

    for bar in bars:
        height = bar.get_height()
        x, _y = bar.get_xy()
        if abs(height) > 0.10:
            ax.text(x + bar.get_width() / 2, height + 0.01, f"{height * 100:.1f}",
                    ha="center", va="bottom", size=6)

    fig.savefig(output_file)
    plt.close(fig)


def generate_confusion_matrix(original_class, weighted_class, display_labels: list, indicator: str, output_file: str):
    """Rows (y axis) are the original classes, columns (x axis) the weighted ones."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import confusion_matrix

    cfm = confusion_matrix(original_class, weighted_class, normalize='all', labels=display_labels).round(4) * 100
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    sns.heatmap(cfm, annot=True, fmt='g', ax=ax)  # fmt='g' disables scientific notation

    ax.set_xlabel('Classe Ponderada')
    ax.set_ylabel('Classe Original')
    ax.set_title(f'Matriz de Confusão (%)\n{indicator}')
    ax.xaxis.set_ticklabels(display_labels)
    ax.yaxis.set_ticklabels(display_labels)
    fig.savefig(output_file)
    plt.close(fig)


def plot_mesh_shapefile(mesh):
    import matplotlib.pyplot as plt

    _fig, ax = plt.subplots()
    for geometry in mesh.geometry:
        for polygon in polygon_parts(geometry):
            x, y = polygon.exterior.xy
            ax.plot(x, y)
    plt.show()


# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------

def load_shapefile(path_file_shp, debug=False, change_crs=False, epsg=5880, set_buffer=False):
    import geopandas as gpd
    from pyproj import CRS

    shapefile = gpd.read_file(path_file_shp)

    if change_crs:
        if debug:
            print("Shapefile CRS before change", shapefile.crs)
        shapefile = shapefile.to_crs(CRS.from_epsg(epsg))
        if debug:
            print("New shapefile CRS after change", shapefile.crs)

    if set_buffer:
        shapefile['geometry'] = shapefile.geometry.buffer(10, cap_style=2)

    return shapefile


def polygon_parts(geometry):
    """Return the list of Polygons in a Polygon or MultiPolygon (empty for anything else)."""
    if geometry is None or geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    if geometry.geom_type == 'MultiPolygon':
        return list(geometry.geoms)
    return []


def find_path_containing_string(target_string, string_list):
    for item in string_list:
        if target_string in item:
            return item
    return None


def find_indicator_column(patterns, indicator) -> Optional[str]:
    """Return the first column named in `patterns`, otherwise the last float
    column whose values are all within [0, 1]."""
    import pandas as pd

    for pattern in patterns:
        if pattern in indicator.columns:
            return pattern
    for col in reversed(list(indicator.columns)):
        if pd.api.types.is_float_dtype(indicator[col]) and indicator[col].between(0, 1).all():
            return col
    return None


def next_indicator_column_id(columns) -> int:
    """Next free N for indicator columns named I_<N> (0 when there are none)."""
    ids = [int(c[2:]) for c in columns if re.fullmatch(r'I_\d+', str(c))]
    return max(ids) + 1 if ids else 0


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        print("Creating output folder: ", folder_path)
    os.makedirs(folder_path, exist_ok=True)


def reproject_raster(in_path, out_path, to_crs, debug=False):
    import rasterio as rio
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    with rio.open(in_path) as src:
        if debug:
            print("CRS antigo do indicador:", src.crs)
        transform, width, height = calculate_default_transform(
            src.crs, to_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({'crs': to_crs, 'transform': transform, 'width': width, 'height': height})

        with rio.open(out_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=to_crs,
                    resampling=Resampling.nearest)
    return out_path
