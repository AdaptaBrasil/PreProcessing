#!/usr/bin/env python
# coding: utf-8

# Example: python3 generate_legends_from_qml.py --qml_files=local_data/qml/**/*.qml --debug --output_folder=output/export_legends --output_file=legends_indicators.csv

import argparse
import glob
import os
import time

import pandas as pd

from utilities import create_folder_if_not_exists, parse_qml_file

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

    frames = []
    dumb_index = 100

    for i, full_path_qml in enumerate(qml_files):
        print(f"\nStarting processing for indicator {i}: {full_path_qml}")

        indicator_name = os.path.splitext(os.path.basename(full_path_qml))[0]
        qml_content = parse_qml_file(full_path_qml)
        if not qml_content['ranges']:
            print(f"WARNING: no graduated ranges found in {full_path_qml}; skipping")
            continue

        data = []
        for symbol_id, symbol_properties in qml_content['symbols'].items():
            qml_range = qml_content['ranges'][symbol_id]
            data.append((dumb_index, qml_range['label'], symbol_properties.get('color', ''),
                         qml_range['minvalue'], qml_range['maxvalue'], i + 10, indicator_name))
            dumb_index += 1

        df_local = pd.DataFrame(data, columns=COLUMNS[:7]).sort_values(by=['minvalue'])
        df_local['order'] = range(1, len(df_local) + 1)
        df_local['tag'] = df_local['order']
        frames.append(df_local)

    df_final = pd.concat(frames, ignore_index=True)[COLUMNS] if frames else pd.DataFrame(columns=COLUMNS)

    # Save the final dataframe
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
