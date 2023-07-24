#!/usr/bin/env python
# coding: utf-8

# Bibliotecas de processamento de dados geoespaciais
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import MultiPolygon, Polygon
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Bibliotecas de manipulação de dados
import pandas as pd

# Bibliotecas de visualização
import seaborn as sns
import matplotlib.pyplot as plt

# Bibliotecas úteis do sistema
import os
from datetime import datetime

# Bibliotecas de aprendizado de máquina e funções de avaliação
from sklearn.metrics import confusion_matrix

# Ignorar warnings
import warnings
warnings.filterwarnings("ignore")

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

def generate_confusion_matrix(original_class, weighted_class, display_labels: list, indicator: str, output_file: str):
    cfm = confusion_matrix(original_class, weighted_class, normalize='all', labels=display_labels).round(4) * 100
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
        os.makedirs(folder_path)

def convert_multi_to_single_polygon(geometry):
    if isinstance(geometry, MultiPolygon):
        # Se for um MultiPolygon, combine todos os polígonos em um único polígono
        return Polygon([p for polygon in geometry for p in polygon.exterior.coords])
    # Caso contrário, retorne a geometria original
    return geometry

import matplotlib.pyplot as plt

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
