#!/usr/bin/env python
# coding: utf-8

import math
import os
import warnings
from decimal import Decimal, InvalidOperation
from typing import List, Tuple, Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import openpyxl as xl
import pandas as pd
import rasterio as rio
import rtree as rt
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from pyproj import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import MultiPolygon, Polygon
from sklearn.metrics import confusion_matrix


warnings.filterwarnings("ignore")

def version_all_libraries():
    # Bibliotecas de processamento de dados geoespaciais
    print("Geopandas version:", gpd.__version__)
    print("Rasterio version:", rio.__version__)
    print("Rtree version:", rt.__version__)

    # Bibliotecas de manipulação de dados
    print("Pandas version:", pd.__version__)
    print("Openpyxl version:", xl.__version__)

    # Bibliotecas de visualização
    print("Seaborn version:", sns.__version__)
    print("Matplotlib version:", plt.matplotlib.__version__)

# version_all_libraries()

def generate_continuous_intervals(min_value: float, max_value: float, n_terms: int) -> List[Tuple[float, float]]:
    """
    Generate n continuous intervals from min_value to max_value.
    
    Each interval follows the pattern where the next minimum value is 
    the previous maximum value plus 0.01, ensuring continuity.
    
    Args:
        min_value: Starting minimum value for the first interval
        max_value: Ending maximum value for the last interval  
        n_terms: Number of intervals to generate
        
    Returns:
        List of tuples containing (min, max) for each interval
        
    Raises:
        ValueError: If n_terms <= 0 or min_value >= max_value
    """
    if n_terms <= 0:
        raise ValueError("Number of terms must be greater than 0")
    
    if min_value >= max_value:
        raise ValueError("Minimum value must be less than maximum value")
    
    # Calculate the total range and interval size
    total_range = max_value - min_value
    interval_size = total_range / n_terms
    
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
    Validate if a list of intervals is continuous.
    
    Checks that each interval follows the pattern where the next minimum 
    value is the previous maximum value plus 0.01, ensuring continuity
    as expected by the existing validation logic.
    
    Args:
        intervals: List of tuples containing (min, max) for each interval
        
    Returns:
        Tuple containing (is_valid, error_messages)
        - is_valid: Boolean indicating if all intervals are continuous
        - error_messages: List of validation error messages
        
    Raises:
        ValueError: If intervals list is empty or contains invalid data
    """
    if not intervals:
        raise ValueError("Intervals list cannot be empty")
    
    errors: List[str] = []
    
    # Sort intervals by minimum value to ensure proper order
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    
    prev_max_val: Optional[float] = None
    
    for i, (min_val, max_val) in enumerate(sorted_intervals):
        # Validate min < max for each interval
        if min_val >= max_val:
            errors.append(
                f"Interval {i + 1}: Minimum value ({min_val}) must be less than maximum value ({max_val})"
            )
        
        # Check continuity with previous interval
        if prev_max_val is not None:
            try:
                # Using Decimal for precision (same as existing validation)
                expected_min = prev_max_val + 0.01
                if Decimal(str(min_val)) - Decimal(str(prev_max_val)) != Decimal("0.01"):
                    errors.append(
                        f"Interval {i + 1}: Not continuous. Minimum value {min_val} should be {expected_min} to follow previous maximum value"
                    )
            except InvalidOperation:
                errors.append(f"Interval {i + 1}: Invalid numeric values for continuity validation")
        
        prev_max_val = max_val
    
    is_valid = len(errors) == 0
    return is_valid, errors

# Função trunc para truncar valores com base no número de casas decimais
def trunc(value, decimal_places):
    if value == 0:
        value = 0.0
    multiplier = 100 ** decimal_places
    truncated_value = math.trunc(value * multiplier) / multiplier
    return truncated_value


def generate_value_pairs_fixed_zero(a1, an, numero_termos):
    termos = []
    numero_termos += 1

    # Incluir o zero se o intervalo tiver um número negativo e um positivo
    if a1 < 0 and an > 0:
        # Calcular a razão para os intervalos separadamente
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
        valor2 = termos[i + 1]
        numero_casas_decimais_valor2 = len(str(valor2).split('.')[1]) if '.' in str(valor2) else 0
        valor2 = valor2 - 100 ** (-numero_casas_decimais_valor2)
        valor2 = trunc(valor2, numero_casas_decimais_valor2)

        diferenca = valor2 - valor1

        valores.append([valor1, valor2, diferenca])

    valores[-1][1] = an
    valores[0][0] = a1
    return valores

def generate_value_pairs(a1, an, numero_termos):
    numero_termos += 1
    razao = (an - a1) / (numero_termos - 1)
    termos = [a1 + (i * razao) for i in range(numero_termos)]

    valores = []

    for i in range(len(termos) - 1):
        valor1 = termos[i]
        valor2 = termos[i + 1]
        numero_casas_decimais_valor2 = len(str(valor2).split('.')[1])
        # Subtrair 1 unidade na ultima casa decimal do valor2 
        valor2 = valor2 - 10 ** (-numero_casas_decimais_valor2)
        # Arredondar o valor2 com truncamento para 2 casas decimais. Trunc
        valor2 = trunc(valor2, numero_casas_decimais_valor2)

        diferenca = valor2 - valor1

        valores.append([valor1, valor2, diferenca])

    # Corrigir o último valor
    valores[-1][1] = an
    # Corrigir o primeiro valor
    valores[0][0] = a1
    return valores

def convert_to_hexadecimal(color_str):
    rgba_values = color_str.split(',')
    
    if len(rgba_values) != 4:
        return None
    
    r, g, b, a = map(int, rgba_values)
    hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
    
    return hex_color

def generate_color(i, a):
    # Determinar a cor base usando 'a' módulo 3
    color_base = a % 3
    r_base, g_base, b_base = 0, 0, 0
    
    if color_base == 0:  # Vermelho
        r_base = 255
    elif color_base == 1:  # Verde
        g_base = 255
    else:  # Azul
        b_base = 255
    
    # Ajustar a intensidade da cor base com base em 'i'
    intensity_increment = 59  # Valor escolhido para obter o comportamento desejado
    r = min(255, r_base + i * intensity_increment)
    g = min(255, g_base + i * intensity_increment)
    b = min(255, b_base + i * intensity_increment)
    
    # Retorna a cor no formato desejado
    return "#{:02X}{:02X}{:02X}".format(r, g, b)

def load_shapefile(path_file_shp, debug=False, change_crs=False, epsg=5880, set_buffer=False):
    # Load shapefile
    shapefile = gpd.read_file(path_file_shp)

    # Change CRS to EPSG 5880 or other specified
    if change_crs:
        if debug:
            print("Shapefile CRS before change", shapefile.crs)
        
        # Change CRS
        shapefile = shapefile.to_crs(CRS.from_epsg(epsg))

        if debug:
            print("New shapefile CRS after change", shapefile.crs)

    # Change geometry to buffer
    if set_buffer:
        shapefile['geometry'] = shapefile.geometry.buffer(10, cap_style=2)
        
    return shapefile

def generate_histogram(data: list, title: str, output_file: str):

    def plotting_hist(data: list, title: str):
        f, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(label="Histograma \n" + title+'\n')

        values, bins, bars = ax.hist(data,
                bins=10, weights=np.ones(len(data)) / len(data))
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        ax.set_ylim([0, 1])
        ax.set_xlim([-1, 1])

        for bar in bars:
            height = bar.get_height()
            x, y = bar.get_xy()
            ax.text(x + bar.get_width() / 2, height + 5,
                    f"{height*100:.1f}" if abs(height) > 0.10 else "", ha="center", va="bottom", size=6, fontdict=None)

        plt.savefig(output_file)

    plotting_hist(data, title)
    plt.clf()

def generate_confusion_matrix(original_class, weighted_class, display_labels: list, indicator: str, output_file: str):
    cfm = confusion_matrix(original_class, weighted_class, normalize='all', labels=display_labels).round(4) * 100
    # annot=True to annotate cells, ftm='g' to disable scientific notation
    f, ax = plt.subplots(1, 1, figsize=(8, 6))
    sns.heatmap(cfm, annot=True, fmt='g', ax=ax)

    ax.set_xlabel('Classe Original')
    ax.set_ylabel('Classe Ponderada')
    ax.set_title(f'Matriz de Confusão (%)\n{indicator}')
    ax.xaxis.set_ticklabels(display_labels)
    ax.yaxis.set_ticklabels(display_labels)
    plt.savefig(output_file)
    ax.remove()
    plt.clf()

def find_path_containing_string(target_string, string_list):
    for item in string_list:
        if target_string in item:
            return item
    return None

def find_indicator_column(patterns, indicator: pd.DataFrame) -> str:
    
    for pattern in patterns:
        if pattern in indicator.columns:
            return pattern
    for i, dtype in enumerate(reversed(indicator.dtypes)):
        if dtype == float:
            col_test = indicator.columns[len(indicator.columns) - i - 1]
            if len(indicator.query(f'{col_test} >= 0 and {col_test} <= 1.0')) == len(indicator):
                return col_test
    return None

def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        print("Creating output folder: ", folder_path)
        os.makedirs(folder_path)

def convert_multi_to_single_polygon(geometry):
    if isinstance(geometry, MultiPolygon):
        # Se for um MultiPolygon, combine todos os polígonos em um único polígono
        return Polygon([p for polygon in geometry for p in polygon.exterior.coords])
    # Caso contrário, retorne a geometria original
    return geometry


def plot_mesh_shapefile(mesh):
    # Create a new figure
    fig, ax = plt.subplots()

    # Iterate over the polygons in the mesh and plot them
    for geometry in mesh.geometry:
        if geometry.geom_type == 'Polygon':
            x, y = geometry.exterior.xy
            ax.plot(x, y)
        elif geometry.geom_type == 'MultiPolygon':
            for polygon in geometry:
                x, y = polygon.exterior.xy
                ax.plot(x, y)

    # Show the plot
    plt.show()



def reproject_raster(in_path, out_path, to_crs, debug=False):
    # reproject raster to project crs
    with rio.open(in_path) as src:
        src_crs = src.crs
        # Imprimir a CRS atual
        if debug:
            print("CRS antigo do indicador:", src_crs)
        transform, width, height = calculate_default_transform(
            src_crs, to_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()

        kwargs.update({
            'crs': to_crs,
            'transform': transform,
            'width': width,
            'height': height})

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
    return(out_path)
