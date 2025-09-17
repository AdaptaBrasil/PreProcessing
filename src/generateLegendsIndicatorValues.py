# !/usr/bin/env python
# coding: utf-8

# Example: python3 generate_legends_from_xlsx.py --xlsx_files=local_data/legendas/entrada1/*.xlsx --debug --output_folder=output/export_legends --output_file=ultimate_legends_indicators.csv --settings_labels=data/settings_labels.csv

import glob
import argparse
import time
import pandas as pd
import math
from utilities import convert_to_hexadecimal, create_folder_if_not_exists, generate_value_pairs
import numpy as np

def main(args):
    input_file = args.input_file
    debug = args.debug
    output_file = args.output_file
    path_settings_labels = args.settings_labels

    if debug:
        print("Passed arguments:")
        print("input_file:", input_file)
        print("Settings labels file:", path_settings_labels)
        print("Debug mode:", debug)
        print("Output file:", output_file)
        print("Complete output file path:", f"{output_file}")

    setting_labels = pd.read_csv(path_settings_labels, sep=';')

    column_relation_data = {
        'id': pd.Series(dtype='int'),
        'label': pd.Series(dtype='str'),
        'color': pd.Series(dtype='str'),
        'minvalue': pd.Series(dtype='float'),
        'maxvalue': pd.Series(dtype='float'),
        'legend_id': pd.Series(dtype='int'),
        'indicator_id': pd.Series(dtype='int'),
        'tag': pd.Series(dtype='str'),
        'order': pd.Series(dtype='int')
    }

    df_final = pd.DataFrame(column_relation_data)
    control_index_legend = 1000
    legend_id = 100
    size_t = 5  # Intervalo de valores

    data = []

    # Read the input XLSX file using pandas
    df_values = pd.read_csv(input_file, sep=';')

    # Sort by column name
    df_values = df_values.sort_index(axis=1)


    df_local = pd.DataFrame(column_relation_data)
    data = []

    for index, value in df_values.iterrows():
        if math.isnan(value.min_value):
            continue
        step = (value.max_value - value.min_value)/5
        k = 1
        for j, sl in setting_labels.iterrows():
            new_row = {
                'id': k + (index - 1) * 6,
                'label': sl.label,
                'color': sl.color,
                'minvalue': (value.min_value + (k - 1) * step) if sl.tag != 'None' else np.nan,
                'maxvalue': (value.min_value + k * step) if sl.tag != 'None' else np.nan,
                'legend_id': value.indicator_id,
                'indicator_id': value.indicator_id,
                'tag': sl.tag,
                'order': sl.order
            }
            df_final = df_final.append(new_row, ignore_index=True)
            k+=1

    # Save the final dataframe
    # Change data types
    df_final['id'] = df_final['id'].astype(int)
    df_final['legend_id'] = df_final['legend_id'].astype(int)
    df_final['indicator_id'] = df_final['indicator_id'].astype(int)
    df_final['order'] = df_final['order'].astype(int)

    # Save the final dataframe. Save in encoding='utf-8'
    df_final.to_csv(f'{output_file}', index=False, encoding='utf-8-sig')
    print(f"File {output_file} saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--input_file", required=True,
                        help="Entry file to be processed, with columns: indicator_id, min_value, max_value")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--settings_labels", default='settings_labels.csv', required=False,
                        help="Name of the settings_labels.csv file. Labels for the legends: label, color, order, tag.")
    parser.add_argument("--output_file", default='legends_indicators.csv', required=False,
                        help="Name of the output file.")
    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"\nTotal time: {total_time_in_minutes} minutes")
