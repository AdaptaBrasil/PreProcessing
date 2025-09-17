#!/usr/bin/env python
# coding: utf-8

# Example: python3 generate_histograms_matrices.py --mesh_file=local_data/indicadores_ferrovias_em_operacao_vmax/indicadores_ferrovias_em_operacao_vmax.shp --indicator_files_mask=local_data/indicadores/*.shp --indicators_spreadsheet=local_data/planilhas/indicadores_ferrovias_em_operacao_vmax.xlsx --m --h --debug --output_folder=output/result_histograms_matrices


# System Libraries
import argparse
import os
import time
import traceback
from glob import glob

# Geospatial Libraries
import geopandas as gpd
from pyproj import CRS

# Data Visualization Libraries
import matplotlib.pyplot as plt
import seaborn as sns

# Numerical Libraries
import numpy as np
import pandas as pd

# Machine Learning Libraries
from sklearn.metrics import confusion_matrix

# Warning Handling
import warnings


# Ignore warnings
warnings.filterwarnings("ignore")

# My utility functions
import config
from utilities import (
    create_folder_if_not_exists,
    find_path_containing_string,
    find_indicator_column,
    generate_confusion_matrix,
    generate_histogram,
    load_shapefile,
)

def main(args):
    mesh_file_path = args.mesh_file
    indicator_files_mask = args.indicator_files_mask
    indicators_spreadsheet = args.indicators_spreadsheet
    is_histograms = args.h
    is_matrices = args.m
    right_cut = args.right_cut
    debug = args.debug
    output_folder_path = args.output_folder

    if debug:
        print("\nPassed arguments:")
        print("Mesh file:", mesh_file_path)
        print("Indicator files mask:", indicator_files_mask)
        print("Indicators spreadsheet:", indicators_spreadsheet)
        print("Generate histograms:", is_histograms)
        print("Generate matrices:", is_matrices)
        print("Is right cut:", right_cut)
        print("Debug mode:", debug)
        print("Output folder:", output_folder_path)
        print("Default CRS:", config.DEFAULT_CRS, "\n")

    output_path_images_histograms = f'{output_folder_path}/histograms/'
    output_path_images_confusion_matrices = f'{output_folder_path}/confusion_matrices'

    # Create the output folders
    if is_matrices:
        create_folder_if_not_exists(output_path_images_confusion_matrices)
    if is_histograms:
        create_folder_if_not_exists(output_path_images_histograms)

    indicator_files = glob(indicator_files_mask, recursive=True)
    mesh_indicators = load_shapefile(mesh_file_path, debug=debug, change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=False)

    indicators_relation = pd.read_excel(indicators_spreadsheet)
    if debug:
        print("Indicators spreadsheet head:", indicators_relation.head())

    num_indicators = len(indicator_files)
    for i, indicator_file_name in enumerate(indicator_files):
        indicator_file_name = indicator_files[i]

        indicator_name = os.path.basename(indicator_file_name).split('.')[0]

        print(f"\nStarting processing for indicator {i}/{num_indicators}: {indicator_file_name}")

        

        indicator_shapefile_path = find_path_containing_string(indicator_name, indicator_files)

        if indicator_shapefile_path is None:
            print(f"ERROR: Indicator {indicator_name} not found!")
            continue
        
        if is_matrices:
            if os.path.isfile(fr"{output_path_images_confusion_matrices}/{indicator_name}.png"):
                continue

        if is_histograms:
            if os.path.isfile(fr"{output_path_images_histograms}/{indicator_name}.png"):
                continue

        try:
            indicator = gpd.read_file(indicator_file_name)
            if debug:
                print("Current CRS of the indicator:", indicator.crs)

            # Change to the CRS EPSG 5880 (default)
            indicator = indicator.to_crs(CRS.from_epsg(config.DEFAULT_CRS))

            if debug:
                print("New CRS of the indicator:", indicator.crs)

            mesh_column = (indicators_relation.query(f"file_name == '{indicator_name}'")['column']).values[0]

            # Define patterns to find the indicator column
            patterns = ['CL_ORIG', 'CL_N-0ORIG', 'N_ORIG']
            indicator_column = find_indicator_column(patterns, indicator)
            if indicator_column is None:
                indicator_column = 'ERROR: Indicator column not found!'

            intersection = gpd.sjoin(mesh_indicators, indicator, how='inner', op='intersects')

            CONFUSION_BINS = [0, 0.01, 0.25, 0.50, 0.75, 1]
            CONFUSION_LABELS = ['0.00 to 0.01', '0.01 to 0.25', '0.25 to 0.50', '0.50 to 0.75', '0.75 to 1']

            intersection['label_indicator'] = pd.cut(x=intersection[indicator_column], bins=CONFUSION_BINS,
                                                     labels=CONFUSION_LABELS, right=right_cut)
            intersection['label_mesh'] = pd.cut(x=intersection[mesh_column], bins=CONFUSION_BINS,
                                                labels=CONFUSION_LABELS, right=right_cut)
            intersection = intersection.dropna(subset=['label_indicator', 'label_mesh'])
            intersection['label_indicator'] = intersection['label_indicator'].values.astype('string')
            intersection['label_mesh'] = intersection['label_mesh'].values.astype('string')

            output_confusion_matrix_i = f'{output_path_images_confusion_matrices}/{indicator_name}.png'
            generate_confusion_matrix(intersection['label_indicator'],
                                      intersection['label_mesh'],
                                      CONFUSION_LABELS,
                                      indicator_name,
                                      output_confusion_matrix_i)

            intersection['diff'] = intersection[indicator_column] - intersection[mesh_column]

            output_histogram_i = fr'{output_path_images_histograms}/{indicator_name}.png'
            generate_histogram(intersection['diff'].to_list(), indicator_name, output_histogram_i)

        except Exception as ex:
            print(f'ERROR: {ex}\n')
            # Print the error traceback
            print(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh_file", required=True,
                        help="Path to the mesh file.")
    parser.add_argument("--indicator_files_mask", required=True,
                        help="Path to the indicator files mask. The glob function will be used to find the indicator files.")
    parser.add_argument("--indicators_spreadsheet", required=True,
                        help="Path to the spreadsheet with the relationships of indicators by columns.")

    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--h", action='store_true',
                        help="Generate histograms?")
    parser.add_argument("--m", action='store_true',
                        help="Generate matrices?")
    parser.add_argument("--right_cut", action='store_true',
                        help="Is right cut?")

    parser.add_argument("--output_folder", default='output', required=True,
                        help="Path to the directory that will be used to save the generated files.")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")