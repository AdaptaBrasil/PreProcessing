#!/usr/bin/env python
# coding: utf-8
# Example: python3 merge_rasters_mesh.py --indicator_files_mask=local_data/rasters/*.tif --mesh_file=local_data/malha/ferrovias.shp --column_relation_file=relacao_arquivos_colunas_malha_rodovias.xlsx --new_mesh_file=indicadores_rodovias.shp --average --debug --output_folder=output/result_rasters_mesh

import proj_env  # noqa: F401 -- must run before rasterio/pyproj/geopandas load
import argparse
import glob
import os
import time
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import rasterio as rio
from pyproj import CRS
from rasterio.mask import mask as raster_mask
from progress.bar import Bar

import config
from utilities import create_folder_if_not_exists, load_shapefile, next_indicator_column_id, polygon_parts


def polygon_value(raster, geometry, is_average):
    """Mean (or max) of the non-negative, non-nodata pixels whose centre falls
    inside `geometry`. Returns -1.0 when there are none."""
    parts = polygon_parts(geometry)
    if not parts:
        return -1.0
    try:
        data, _ = raster_mask(raster, parts, crop=True, filled=False, indexes=1)
    except ValueError:  # polygon does not overlap the raster
        return -1.0
    values = data.compressed()
    values = values[np.isfinite(values) & (values >= 0)]
    if values.size == 0:
        return -1.0
    return float(values.mean() if is_average else values.max())


def main(args):
    indicator_files_mask = args.indicator_files_mask
    mesh_file_path = args.mesh_file
    column_relation_file_name = args.column_relation_file
    updated_mesh_file_path = args.new_mesh_file
    is_average = args.average
    debug = args.debug
    output_folder_path = args.output_folder

    if debug:
        print("\nPassed arguments:")
        print("Indicator files mask:", indicator_files_mask)
        print("Mesh file:", mesh_file_path)
        print("Columns relation file:", column_relation_file_name)
        print("Updated mesh file:", updated_mesh_file_path)
        print("Average:", is_average)
        print("Debug:", debug)
        print("Output folder:", output_folder_path)
        print("Default CRS:", config.DEFAULT_CRS, "\n")

    create_folder_if_not_exists(output_folder_path)

    updated_mesh_file_path = os.path.join(output_folder_path, updated_mesh_file_path)
    column_relation_file_name = os.path.join(output_folder_path, column_relation_file_name)

    mesh = load_shapefile(mesh_file_path, debug=debug, change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=False)
    print("Number of items in the mesh: ", len(mesh), "\n")

    next_col_id = next_indicator_column_id(mesh.columns)
    if debug:
        print("Next column ID: ", next_col_id)

    if next_col_id > 0 and os.path.exists(column_relation_file_name):
        print("Columns relation file exists. Opening...")
        df_column_relation = pd.read_excel(column_relation_file_name)
    else:
        print("Columns relation file doesn't exist. Creating...")
        df_column_relation = pd.DataFrame({'file_name': [], 'column': []})

    if debug:
        print("Columns relation file head:  ", df_column_relation.head())

    indicator_tifs = sorted(glob.glob(indicator_files_mask, recursive=True))
    print("Number of indicator files found: ", len(indicator_tifs))

    for indicator_file_path in indicator_tifs:
        try:
            file_name_only = os.path.basename(indicator_file_path).split('.')[0]
            if (df_column_relation['file_name'] == file_name_only).any():
                print(f"Skipping {indicator_file_path}: already processed")
                continue

            column_key = f'I_{next_col_id}'
            print(f"\nStarting the processing of file {column_key}: {indicator_file_path} {datetime.now()}")

            with rio.open(indicator_file_path) as indicator:
                if debug:
                    print("Current CRS of the indicator:", indicator.crs)
                    print("Shape of indicator:", indicator.shape)

                geometries = mesh.geometry.to_crs(indicator.crs)
                values = []
                with Bar(f'Processing {len(geometries)} polygons of {column_key}', max=len(geometries)) as bar:
                    for geometry in geometries:
                        values.append(polygon_value(indicator, geometry, is_average))
                        bar.next()

            mesh[column_key] = values

            df_column_relation = pd.concat(
                [df_column_relation, pd.DataFrame([{'file_name': file_name_only, 'column': column_key}])],
                ignore_index=True)
            df_column_relation.to_excel(column_relation_file_name, index=False)

            mesh = mesh.to_crs(CRS.from_epsg(config.DEFAULT_CRS))
            mesh.to_file(updated_mesh_file_path)
            next_col_id += 1

            print("\nUpdated mesh saved to: ", updated_mesh_file_path)
            print("Columns relation file saved to: ", column_relation_file_name)

        except Exception as ex:
            print(f'ERROR: {ex}\n')
            print(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--indicator_files_mask", required=True,
                        help="Path to the indicator files mask. The glob function will be used to find the indicator files. Example: directory/*.tif")
    parser.add_argument("--mesh_file", required=True,
                        help="Path to the mesh file. Example: mesh.shp")
    parser.add_argument("--column_relation_file", required=True,
                        help="Path to the columns relation file. Example: relation.xlsx")
    parser.add_argument("--new_mesh_file", required=True,
                        help="Path to the new updated mesh file. Example: new_updated_mesh.shp")
    parser.add_argument("--average", action='store_true',
                        help="Calculate the average of the pixel values within each mesh polygon. If False, take the maximum value.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--output_folder", default='output',
                        help="Path to the directory that will be used to save the generated files (default: output).")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    total_time_in_minutes = (time.time() - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")
