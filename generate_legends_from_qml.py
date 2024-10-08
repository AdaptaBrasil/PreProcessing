#!/usr/bin/env python
# coding: utf-8

# Example: python3 generate_legends_from_qml.py --qml_files=local_data/qml/**/*.qml --debug --output_folder=output/export_legends --output_file=legends_indicators.csv

import glob
import argparse
import time
import pandas as pd
import xml.etree.ElementTree as ET
from utilities import convert_to_hexadecimal, create_folder_if_not_exists

def parse_qml_ranges_ranges(renderer_element):
    ranges_dict = {}
    ranges_element = renderer_element.find('ranges')
    if ranges_element is not None:
        for range_element in ranges_element.findall('range'):
            label = range_element.get('label')
            upper = float(range_element.get('upper'))
            lower = float(range_element.get('lower'))
            symbol = int(range_element.get('symbol'))
            ranges_dict[symbol] = {'label': label, 'minvalue': lower, 'maxvalue': upper, 'symbol': symbol}
    return ranges_dict

def parse_qml_symbols(renderer_element):
    symbols_dict = {}
    symbols_element = renderer_element.find('symbols')
    if symbols_element is not None:
        for symbol_element in symbols_element.findall('symbol'):
            symbol_id = int(symbol_element.get('name'))
            symbol_properties = {}
            layer_element = symbol_element.find('layer')
            if layer_element is not None:
                options_element = layer_element.find('Option')
                if options_element is not None:
                    for option_element in options_element.findall('Option'):
                        prop_name = option_element.get('name')
                        if prop_name == 'color':
                            prop_value = option_element.get('value')
                            symbol_properties[prop_name] = convert_to_hexadecimal(prop_value)
                            symbol_properties['symbol_id'] = symbol_id
                            break
            symbols_dict[symbol_id] = symbol_properties
    return symbols_dict

def parse_qml_file(qml_file_path):
    qml_dict = {}
    tree = ET.parse(qml_file_path)
    root = tree.getroot()
    for child in root:
        if child.tag == 'renderer-v2':
            qml_dict['ranges'] = parse_qml_ranges_ranges(child)
            qml_dict['symbols'] = parse_qml_symbols(child)
    return qml_dict

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
        print("Complete output file path:", f"{output_folder_path}/{output_file}")

    create_folder_if_not_exists(output_folder_path)
    qml_files = glob.glob(qml_files, recursive=True)
    print(f'Found {len(qml_files)} QML files')

    column_relation_data = {
        'id': [],
        'label': [],
        'color': [],
        'minvalue': [],
        'maxvalue': [],
        'legend_id': [],
        'indicator': [],
        'tag': [],
        'order': []
    }

    df_final = pd.DataFrame(column_relation_data)
    dumb_index = 100

    for i, full_path_qml in enumerate(qml_files):
        print(f"\nStarting processing for indicator {i}: {full_path_qml}")

        path_qml = full_path_qml.split('/')[-1]
        path_qml = path_qml.replace('.qml', '')
        df_local = pd.DataFrame(column_relation_data)

        qml_content = parse_qml_file(full_path_qml)
        data = []
        
        for symbol_id, symbol_properties in qml_content['symbols'].items():
            label = qml_content['ranges'][symbol_id]['label']
            minvalue = qml_content['ranges'][symbol_id]['minvalue']
            maxvalue = qml_content['ranges'][symbol_id]['maxvalue']
            color = symbol_properties.get('color', '')

            data.append((dumb_index, label, color, minvalue, maxvalue, i+10, path_qml))
            dumb_index += 1

        df_local = df_local.append(pd.DataFrame(data, columns=['id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id', 'indicator']), ignore_index=True)
        df_local = df_local.sort_values(by=['minvalue'])
        df_local['order'] = range(1, len(df_local) + 1)
        df_local['tag'] = df_local['order']

        df_final = df_final.append(df_local, ignore_index=True)

    # Change data types
    df_final['id'] = df_final['id'].astype(int)
    df_final['legend_id'] = df_final['legend_id'].astype(int)
    df_final['order'] = df_final['order'].astype(int)
    df_final['tag'] = df_final['tag'].astype(int) # @assismauro veriricar se isso é necessário

    # Save the final dataframe
    df_final.to_csv(f'{output_folder_path}/{output_file}', index=False)
    print(f"File {output_file} saved in {output_folder_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--qml_files", required=True,
                        help="Path to the directory where the QML files are located. Use glob patterns to find the QML files.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--output_folder", default='output', required=True,
                        help="Path to the directory where the generated files will be saved.")
    parser.add_argument("--output_file", default='legends_indicators.csv', required=False,
                        help="Name of the output file.")
    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"\nTotal time: {total_time_in_minutes} minutes")
