#!/usr/bin/env python
# coding: utf-8
# Example: python3 merge_rasters_malha.py --mascara_indicadores=rasters/*.tif --arquivo_malha=malha/ferrovias.shp --arquivo_relacao=relacao_arquivos_colunas_malha_rodovias.xlsx --nova_malha=indicadores_rodovias.shp


import rasterio as rio
from rasterio.windows import Window
import geopandas as gpd
from rasterio.mask import mask
import matplotlib.pyplot as plt
import numpy as np
import cv2
import pandas as pd
from pyproj import CRS
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

import shapefile as shp  # Requires the pyshp package


import rasterio as rio
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.features import geometry_mask

import time

# Bibliotecas úteis do sistema
import os
import glob
from datetime import datetime
import argparse

import warnings
# Ignorar warnings
warnings.filterwarnings("ignore")

DEBUG = True
def reproject_raster(in_path, out_path, to_crs):
    """
    """
    # reproject raster to project crs
    with rio.open(in_path) as src:
        src_crs = src.crs
        # Imprimir a CRS atual
        if DEBUG:
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


def plotMalha(malha):
    # Criar uma nova figura
    fig, ax = plt.subplots()

    # Iterar sobre os polígonos da malha e plotar
    for geom in malha.geometry:
        if geom.geom_type == 'Polygon':
            x, y = geom.exterior.xy
            ax.plot(x, y)
        elif geom.geom_type == 'MultiPolygon':
            for polygon in geom:
                x, y = polygon.exterior.xy
                ax.plot(x, y)

    # Exibir o gráfico
    plt.show()

