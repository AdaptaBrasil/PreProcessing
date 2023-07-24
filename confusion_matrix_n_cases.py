#!/usr/bin/env python
# coding: utf-8

# Example: python3 confusion_matrix_n_cases.py --mesh_file=malha/ferrovias.shp  --indicator_files_mask=indicadores/*.shp --indicators_spreadsheet=planilhas/solução_risco_desl_para_matriz.xlsx --debug --output_folder=output/confusion_matrices


import geopandas as gpd
from pyproj import CRS
import pandas as pd
import glob
import argparse
import time

# My functions utilities
from utilities import *
import config

def main(args):
    # Input files with shapefile data for indicators and mesh
    mesh_file_path = args.mesh_file
    indicator_files_mask = args.indicator_files_mask
    indicators_spreadsheet = args.indicators_spreadsheet
    debug = args.debug
    output_folder_path = args.output_folder

    if debug:
        print("Passed arguments:")
        print("Mesh file:", mesh_file_path)
        print("Indicator files mask:", indicator_files_mask)
        print("Indicators spreadsheet:", indicators_spreadsheet)
        print("Debug mode:", debug)
        print("Output folder:", output_folder_path)
        # Default CRS
        print("Default CRS:", config.DEFAULT_CRS)

    # Create output folder if it doesn't exist
    create_folder_if_not_exists(output_folder_path)

    # Load shapefile
    mesh = load_shapefile(mesh_file_path, debug=debug, change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=True)
    print("Number of items in the mesh: ", len(mesh))

    # Setup the column names
    if 'objectid' not in mesh.columns:
        mesh.columns = ['objectid', *mesh.columns[1:]]

    # Get all indicators shapefiles paths
    all_indicator_shapefile_paths = glob.glob(indicator_files_mask, recursive=True)

    indicators_spreadsheet_df = pd.read_excel(indicators_spreadsheet)
    if debug:
        print("Indicators spreadsheet head:  ", indicators_spreadsheet_df.head())

    # Remove the row at index 0 from the dataframe
    indicators_spreadsheet_df = indicators_spreadsheet_df.drop(indicators_spreadsheet_df.index[0])

    # Reorder the index
    indicators_spreadsheet_df.index = range(len(indicators_spreadsheet_df))

    # Rename the first column to 'objectid'
    indicators_spreadsheet_df = indicators_spreadsheet_df.rename(columns={indicators_spreadsheet_df.columns[0]: 'objectid'})

    # Extract column 0 to create a new dataframe
    objectid_column_df = indicators_spreadsheet_df.iloc[:, [0]].copy()

    # Remove the objectid column from the indicators spreadsheet
    indicators_spreadsheet_df = indicators_spreadsheet_df.drop(columns=[indicators_spreadsheet_df.columns[0]])

    # Iterate over each column with for loop
    for i_column, column_name in enumerate(indicators_spreadsheet_df.columns):
        # Print the column name
        print(f"\nStarting processing for indicator {i_column}: {column_name}")
        
        point = column_name.rfind('.')
        indicator_name = column_name if point == -1 else column_name[:point]
        
        # Check if the indicator_name is contained in the strings of the list of indicators (all_indicator_shapefile_paths)
        indicator_shp_path = find_path_containing_string(indicator_name, all_indicator_shapefile_paths)
        
        if indicator_shp_path is None:
            print(f"ERROR: Indicator {indicator_name} not found!")
            continue

        # Create a new dataframe with the objectid column and the indicator column
        indicator_df = pd.concat([objectid_column_df, indicators_spreadsheet_df.iloc[:, [i_column]]], axis=1)
        
        # Rename the columns of indicator_df to 'objectid' and 'values'
        indicator_df.columns = ['objectid', 'values']

        indicator = gpd.read_file(indicator_shp_path)

        if debug:
            print("Current CRS of the indicator:", indicator.crs)

        # Change to the CRS EPSG 5880 (default)
        indicator = indicator.to_crs(CRS.from_epsg(config.DEFAULT_CRS))

        if debug:
            print("New CRS of the indicator:", indicator.crs)

        # First merge indicator with the mesh, obtaining the geometries.
        mesh_merge = mesh.merge(indicator_df, on='objectid', how='inner')
        
        # Then merge indicator+mesh with the original indicator value.
        intersection = gpd.sjoin(indicator, mesh_merge, how='inner', predicate='intersects')

        # Routine to generate the confusion matrix.
        CONFUSION_BINS =   [0, 0.01, 0.25, 0.50, 0.75, 1]
        CONFUSION_LABELS = ['0.00 to 0.01', '0.01 to 0.25', '0.25 to 0.50', '0.50 to 0.75', '0.75 to 1']

        # Define patterns to find the indicator column
        patterns = ['CL_ORIG', 'CL_N-0ORIG', 'N_ORIG']
        data_field = find_indicator_column(patterns, intersection)
        if data_field is None:
            data_field = 'ERROR: Indicator column not found!'

        intersection['indicator_label'] = pd.cut(x=intersection[data_field], bins=CONFUSION_BINS,
                                                 labels=CONFUSION_LABELS)
        intersection['estimation_label'] = pd.cut(x=intersection['values'], bins=CONFUSION_BINS,
                                                  labels=CONFUSION_LABELS)

        intersection = intersection.dropna(subset=['indicator_label', 'estimation_label'])
        intersection['indicator_label'] = intersection['indicator_label'].values.astype('string')
        intersection['estimation_label'] = intersection['estimation_label'].values.astype('string')

        output_confusion_matrix_i = f'{output_folder_path}/confusion_matrix_indicator_{i_column}_{column_name}.png'
        generate_confusion_matrix(intersection['indicator_label'],
                                  intersection['estimation_label'],
                                  CONFUSION_LABELS,
                                  column_name, output_confusion_matrix_i)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh_file", required=True, help="Path to the mesh file")
    parser.add_argument("--indicator_files_mask", required=True, help="Path to the directory where the indicator file masks are located. The glob will be used to find the indicator files.")
    parser.add_argument("--indicators_spreadsheet", required=True, help="Path to the spreadsheet with the relationships of indicators by columns.")
    parser.add_argument("--debug", action='store_true', help="Activate debug mode.")
    parser.add_argument("--output_folder", default='output', required=True, help="Path to the directory that will be used to save the generated files.")
    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")

