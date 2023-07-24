#!/usr/bin/env python
# coding: utf-8
# Example: python3 merge_rasters_mesh.py --indicator_files_mask=rasters/*.tif --mesh_file=malha/ferrovias.shp --column_relation_file=relacao_arquivos_colunas_malha_rodovias.xlsx --new_mesh_file=indicadores_rodovias.shp --average --debug --output_folder=output/result_rasters_mesh

# Geospatial data processing libraries
import rasterio as rio
from pyproj import CRS

# Numerical processing library
import numpy as np
import cv2

# Data manipulation libraries
import pandas as pd

# System utility libraries
import os
import glob
from datetime import datetime
import argparse
import time
import traceback

# Useful libraries
from progress.bar import Bar

# My utility functions
from utilities import create_folder_if_not_exists, load_shapefile, convert_multi_to_single_polygon
import config

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

def main(args):
    # Get all the passed arguments
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
        # Default CRS
        print("Default CRS:", config.DEFAULT_CRS, "\n")

    # Create output folder if it doesn't exist
    create_folder_if_not_exists(output_folder_path)

    # Concatenate the output/ with the output file name
    updated_mesh_file_path = os.path.join(output_folder_path, updated_mesh_file_path)
    column_relation_file_name = os.path.join(output_folder_path, column_relation_file_name)

    mesh = load_shapefile(mesh_file_path, debug=debug, change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=False)
    print("Number of items in the mesh: ", len(mesh), "\n")

    # Get next column ID
    next_col_id = 1
    if 'I_1' in mesh.columns:
        last_col = mesh.columns[len(mesh.columns) - 2]
        next_col_id = int(last_col[2:]) + 1

    if debug:
        print("Next column ID: ", next_col_id)

    # Verify if the columns relation file exists.
    if next_col_id > 1:
        print("Columns relation file exists. Opening...")
        # Load the columns relation file
        df_column_relation = pd.read_excel(column_relation_file_name)
    else:
        print("Columns relation file doesn't exist. Creating...")
        # Create the columns relation file
        column_relation_data = {
            'file_name': [],
            'column': []
        }
        df_column_relation = pd.DataFrame(column_relation_data)

    if debug:
        print("Columns relation file head:  ", df_column_relation.head())

    indicator_tifs = glob.glob(indicator_files_mask, recursive=True)

    print("Number of indicator files found: ", len(indicator_tifs))

    # Print the names of the .tif files found
    for i, indicator_file_path in enumerate(indicator_tifs):
        try:
            # Get the file name without extension
            file_name_only = os.path.basename(indicator_file_path).split('.')[0]

            print(
                f"\nStarting the processing of file {next_col_id + i}: {indicator_file_path} {datetime.now()}")

            indicator = rio.open(indicator_file_path)
            pixel_values = indicator.read(1)

            crs_integer_indicator = int(indicator.crs.to_epsg())

            # Print the current CRS
            if debug:
                print("Current CRS of the indicator:", crs_integer_indicator)

            mesh = mesh.to_crs(crs_integer_indicator)

            # Print the current CRS of the mesh
            if debug:
                print("Current CRS of the mesh:", mesh.crs)

            if debug:
                print(f"Shape of indicator {i}: {pixel_values.shape}")

            # Create a new column key "I_i" and set a float value
            # For example, set the value -1 to all records
            column_key = 'I_' + str(i)
            mesh[column_key] = -1.0

            # Display the GeoDataFrame with the new column
            if debug:
                print(f"Column {column_key} in the mesh: ", mesh[column_key])

            # Bring values from degrees to Cartesian plane
            min_lat, max_lon, max_lat, min_lon = indicator.bounds
            min_x, min_y = indicator.index(min_lat, min_lon)
            max_x, max_y = indicator.index(max_lat, max_lon)
            width, height = int(max_x - min_x), int(max_y - min_y)

            num_polygons = len(mesh.geometry)

            # Create a progress bar with the number of polygons and display the elapsed time next to the value
            with Bar(f'Processing {num_polygons} polygons of indicator {i}', max=num_polygons) as bar:
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
                    mesh.at[idx, column_key] = arithmetic_mean if is_average else max_value

                    # Update the progress bar
                    bar.next()

            # New row to be added
            new_row = {'file_name': file_name_only, 'column': column_key}

            # Add the new row to the DataFrame
            df_column_relation = df_column_relation.append(new_row, ignore_index=True)

            # Save the DataFrame to an Excel file
            df_column_relation.to_excel(column_relation_file_name, index=False)

            # Change the CRS of the mesh to the default CRS
            mesh = mesh.to_crs(CRS.from_epsg(config.DEFAULT_CRS))

            # Save the updated mesh
            mesh.to_file(updated_mesh_file_path)

            print("\nUpdated mesh saved to: ", updated_mesh_file_path)
            print("Columns relation file saved to: ", column_relation_file_name)

            # Close the indicator
            indicator.close()

        except Exception as ex:
            print(f'ERROR: {ex}\n')
            # Print the error traceback
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

    parser.add_argument("--output_folder", default='output', required=True,
                        help="Path to the directory that will be used to save the generated files.")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")
