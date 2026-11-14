#!/usr/bin/env python
# coding: utf-8

# Example: python3 generate_legends_from_qml_v2_merge.py --qml_files=local_data/qml/**/*.qml --debug --output_folder=output/export_legends --output_file=legends_indicators_v2_merge.csv
#
# QML files whose names share the same prefix before '-' (e.g. 1234-2030.qml and
# 1234-2050.qml) are merged into one legend spanning their overall min and max.

import argparse
import glob
import os
import time

import pandas as pd

from utilities import create_folder_if_not_exists, generate_color, generate_value_pairs, parse_qml_file, trunc

COLUMNS = ['id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id', 'indicator', 'tag', 'order']


def main(args):
    qml_files = args.qml_files
    debug = args.debug
    output_folder_path = args.output_folder
    output_file = args.output_file

    if debug:
        print("Passed arguments:")
        print("QML files mask:", qml_files)
        print("Debug mode:", debug)
        print("Output folder:", output_folder_path)
        print("Output file:", output_file)
        print("Complete output file path:", os.path.join(output_folder_path, output_file))

    create_folder_if_not_exists(output_folder_path)
    qml_files = sorted(glob.glob(qml_files, recursive=True))
    print(f'Found {len(qml_files)} QML files')

    # Overall [min, max] per indicator key (file name prefix before '-')
    ranges_by_key = {}
    for i, full_path_qml in enumerate(qml_files):
        print(f"\nStarting processing for indicator {i}: {full_path_qml}")

        key = os.path.splitext(os.path.basename(full_path_qml))[0].split('-')[0]
        qml_content = parse_qml_file(full_path_qml)
        for symbol_id in qml_content['symbols']:
            qml_range = qml_content['ranges'][symbol_id]
            low, high = float(qml_range['minvalue']), float(qml_range['maxvalue'])
            if key in ranges_by_key:
                ranges_by_key[key] = [min(ranges_by_key[key][0], low), max(ranges_by_key[key][1], high)]
            else:
                ranges_by_key[key] = [low, high]

    frames = []
    legend_id = 1
    row_id = 1
    for key, (minvalue, maxvalue) in ranges_by_key.items():
        data = []
        for i, (low, high, _diff) in enumerate(generate_value_pairs(minvalue, maxvalue, 5)):
            low, high = trunc(low, 5), trunc(high, 5)
            data.append((row_id, f"{low} - {high}", generate_color(i, legend_id), low, high, legend_id, key))
            row_id += 1
        legend_id += 1

        df_local = pd.DataFrame(data, columns=COLUMNS[:7]).sort_values(by=['minvalue'])
        df_local['order'] = range(1, len(df_local) + 1)
        df_local['tag'] = df_local['order']
        frames.append(df_local)

    df_final = pd.concat(frames, ignore_index=True)[COLUMNS] if frames else pd.DataFrame(columns=COLUMNS)

    output_path = os.path.join(output_folder_path, output_file)
    df_final.to_csv(output_path, index=False)
    print(f"File {output_file} saved in {output_folder_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--qml_files", required=True,
                        help="Path to the directory where the QML files are located. Use glob patterns to find the QML files.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--output_folder", default='output',
                        help="Path to the directory where the generated files will be saved (default: output).")
    parser.add_argument("--output_file", default='legends_indicators.csv', required=False,
                        help="Name of the output file.")
    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    total_time_in_minutes = (time.time() - initial_time) / 60
    print(f"\nTotal time: {total_time_in_minutes} minutes")
