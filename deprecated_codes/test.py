#!/usr/bin/env python
# coding: utf-8

import os
import glob
import cv2
import argparse
import time
import traceback
import multiprocessing as mp
from datetime import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio as rio
from pyproj import CRS
from progress.bar import Bar
from utilities import create_folder_if_not_exists, load_shapefile, convert_multi_to_single_polygon
import config

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

def process_indicator_file(args):
    indicator_file_path, output_folder_path, is_average, debug, column_relation_file_name = args

    try:
        # Get the file name without extension
        file_name_only = os.path.basename(indicator_file_path).split('.')[0]

        print(f"\nStarting the processing of file: {indicator_file_path} {datetime.now()}")

        with rio.open(indicator_file_path) as indicator:
            pixel_values = indicator.read(1)
            crs_integer_indicator = int(indicator.crs.to_epsg())

        # Load the mesh
        mesh_file_path = os.path.join(output_folder_path, "temp_mesh.shp")
        mesh = gpd.read_file(mesh_file_path)
        mesh = mesh.to_crs(crs_integer_indicator)

        # Get the bounds of the indicator
        min_lat, max_lon, max_lat, min_lon = indicator.bounds
        min_x, min_y = indicator.index(min_lat, min_lon)
        max_x, max_y = indicator.index(max_lat, max_lon)
        width, height = int(max_x - min_x), int(max_y - min_y)

        num_polygons = len(mesh.geometry)

        # Create a progress bar with the number of polygons and display the elapsed time next to the value
        with Bar(f'Processing {num_polygons} polygons of {file_name_only}', max=num_polygons) as bar:
            for idx, geometry in enumerate(mesh.geometry):
                # Transform multi-polygon into polygon
                geometry = convert_multi_to_single_polygon(geometry)

                polygons = np.zeros((width, height), dtype=np.uint8)
                pts = np.array([indicator.index(point[0], point[1]) for point in geometry.exterior.coords[:]], np.int32)[:, ::-1]
                pts = pts - np.array([min_y, min_x])

                cv2.fillPoly(polygons, [pts], 1)  # mask

                x, y = np.where(polygons == 1)
                values = pixel_values[x, y]
                # Remove all negative values from the value list
                values = values[values >= 0]

                # Check if the value list is not empty
                if len(values) > 0:
                    max_value = np.nanmax(values)
                    # Calculate the arithmetic mean
                    arithmetic_mean = np.mean(values)
                else:
                    # Set a default value for max_value when the list is empty (e.g., -1)
                    max_value = -1.0
                    # Set a default value for arithmetic_mean when the list is empty (e.g., -1)
                    arithmetic_mean = -1.0

                # Insert the arithmetic mean or the maximum value into the column
                column_key = 'I_' + str(idx)
                mesh.at[idx, column_key] = arithmetic_mean if is_average else max_value

                # Update the progress bar
                bar.next()

        # Change the CRS of the mesh to the default CRS
        mesh = mesh.to_crs(CRS.from_epsg(config.DEFAULT_CRS))

        # Save the updated mesh
        updated_mesh_file_path = os.path.join(output_folder_path, f"{file_name_only}.shp")
        mesh.to_file(updated_mesh_file_path)

        print("\nUpdated mesh saved to: ", updated_mesh_file_path)

        # New row to be added
        new_row = {'file_name': file_name_only, 'column': column_key}

        # Load the columns relation file
        if os.path.exists(column_relation_file_name):
            df_column_relation = pd.read_excel(column_relation_file_name)
        else:
            df_column_relation = pd.DataFrame(columns=['file_name', 'column'])

        # Add the new row to the DataFrame
        df_column_relation = df_column_relation.append(new_row, ignore_index=True)

        # Save the DataFrame to an Excel file
        df_column_relation.to_excel(column_relation_file_name, index=False)

        print("Columns relation file saved to: ", column_relation_file_name)

    except Exception as ex:
        print(f'ERROR: {ex}\n')
        # Print the error traceback
        print(traceback.format_exc())

    # Remove the temporary mesh file
    if os.path.exists(mesh_file_path):
        os.remove(mesh_file_path)

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
        print("Average:", is_average, "\n")
        print("Debug:", debug, "\n")
        print("Output folder:", output_folder_path, "\n")
        print("Default CRS:", config.DEFAULT_CRS, "\n")

    # Create output folder if it doesn't exist
    create_folder_if_not_exists(output_folder_path)

    # Load the initial mesh
    initial_mesh = gpd.read_file(mesh_file_path)
    initial_mesh.to_file(os.path.join(output_folder_path, "temp_mesh.shp"))

    indicator_tifs = glob.glob(indicator_files_mask, recursive=True)

    print("Number of indicator files found: ", len(indicator_tifs))

    # Process indicator files in parallel
    pool = mp.Pool(processes=mp.cpu_count())
    args_list = [(indicator_path, output_folder_path, is_average, debug, column_relation_file_name) for indicator_path in indicator_tifs]
    pool.map(process_indicator_file, args_list)
    pool.close()
    pool.join()

    # Concatenate the output/ with the output file name
    updated_mesh_file_path = os.path.join(output_folder_path, updated_mesh_file_path)

    # Merge all processed meshes into a single file
    merged_mesh = gpd.GeoDataFrame(pd.concat([gpd.read_file(os.path.join(output_folder_path, f"{os.path.basename(f).split('.')[0]}.shp")) for f in indicator_tifs], ignore_index=True))
    merged_mesh.to_file(updated_mesh_file_path)

    print("\nFinal updated mesh saved to: ", updated_mesh_file_path)

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

    parser.add_argument("--output_folder", default='output', required=True,
                        help="Path to the directory that will be used to save the generated files.")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")
