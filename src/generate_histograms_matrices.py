#!/usr/bin/env python
# coding: utf-8

# Example: python3 generate_histograms_matrices.py --mesh_file=local_data/indicadores_ferrovias_em_operacao_vmax/indicadores_ferrovias_em_operacao_vmax.shp --indicator_files_mask=local_data/indicadores/*.shp --indicators_spreadsheet=local_data/planilhas/indicadores_ferrovias_em_operacao_vmax.xlsx --m --h --debug --output_folder=output/result_histograms_matrices

import argparse
import os
import time
import traceback
from glob import glob

import geopandas as gpd
import pandas as pd
from pyproj import CRS

import config
from utilities import (
    create_folder_if_not_exists,
    find_indicator_column,
    generate_confusion_matrix,
    generate_histogram,
    load_shapefile,
)

CONFUSION_BINS = [0, 0.01, 0.25, 0.50, 0.75, 1]
CONFUSION_LABELS = ['0.00 to 0.01', '0.01 to 0.25', '0.25 to 0.50', '0.50 to 0.75', '0.75 to 1']


def classify(values, right_cut):
    # include_lowest keeps 0.0 when right=True; the last bin is widened so 1.0 is kept when right=False
    bins = CONFUSION_BINS if right_cut else CONFUSION_BINS[:-1] + [1 + 1e-9]
    return pd.cut(x=values, bins=bins, labels=CONFUSION_LABELS, right=right_cut, include_lowest=True)


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

    if not (is_histograms or is_matrices):
        raise SystemExit("Nothing to do: pass --h (histograms) and/or --m (confusion matrices).")

    output_path_histograms = os.path.join(output_folder_path, 'histograms')
    output_path_matrices = os.path.join(output_folder_path, 'confusion_matrices')
    if is_matrices:
        create_folder_if_not_exists(output_path_matrices)
    if is_histograms:
        create_folder_if_not_exists(output_path_histograms)

    indicator_files = sorted(glob(indicator_files_mask, recursive=True))
    mesh_indicators = load_shapefile(mesh_file_path, debug=debug, change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=False)

    indicators_relation = pd.read_excel(indicators_spreadsheet)
    if debug:
        print("Indicators spreadsheet head:", indicators_relation.head())

    num_indicators = len(indicator_files)
    for i, indicator_file_name in enumerate(indicator_files):
        indicator_name = os.path.basename(indicator_file_name).split('.')[0]
        print(f"\nStarting processing for indicator {i + 1}/{num_indicators}: {indicator_file_name}")

        matrix_file = os.path.join(output_path_matrices, f'{indicator_name}.png')
        histogram_file = os.path.join(output_path_histograms, f'{indicator_name}.png')
        do_matrix = is_matrices and not os.path.isfile(matrix_file)
        do_histogram = is_histograms and not os.path.isfile(histogram_file)
        if not (do_matrix or do_histogram):
            continue

        try:
            matches = indicators_relation.loc[indicators_relation['file_name'] == indicator_name, 'column']
            if matches.empty:
                print(f"ERROR: Indicator {indicator_name} not found in {indicators_spreadsheet}")
                continue
            mesh_column = matches.values[0]

            indicator = gpd.read_file(indicator_file_name)
            if debug:
                print("Current CRS of the indicator:", indicator.crs)
            indicator = indicator.to_crs(CRS.from_epsg(config.DEFAULT_CRS))

            indicator_column = find_indicator_column(['CL_ORIG', 'CL_N-0ORIG', 'N_ORIG'], indicator)
            if indicator_column is None:
                print(f"ERROR: Indicator column not found in {indicator_file_name}")
                continue

            intersection = gpd.sjoin(mesh_indicators, indicator, how='inner', predicate='intersects')

            if do_matrix:
                labeled = intersection.assign(
                    label_indicator=classify(intersection[indicator_column], right_cut),
                    label_mesh=classify(intersection[mesh_column], right_cut),
                ).dropna(subset=['label_indicator', 'label_mesh'])
                generate_confusion_matrix(labeled['label_indicator'].astype('string'),
                                          labeled['label_mesh'].astype('string'),
                                          CONFUSION_LABELS,
                                          indicator_name,
                                          matrix_file)

            if do_histogram:
                diff = (intersection[indicator_column] - intersection[mesh_column]).dropna()
                generate_histogram(diff.to_list(), indicator_name, histogram_file)

        except Exception as ex:
            print(f'ERROR: {ex}\n')
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
                        help="Generate histograms")
    parser.add_argument("--m", action='store_true',
                        help="Generate confusion matrices")
    parser.add_argument("--right_cut", action='store_true',
                        help="Use right-closed bins (a, b] instead of left-closed [a, b)")
    parser.add_argument("--output_folder", default='output',
                        help="Path to the directory that will be used to save the generated files (default: output).")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    total_time_in_minutes = (time.time() - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")
