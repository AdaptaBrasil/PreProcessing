#!/usr/bin/env python
# coding: utf-8

# Example: python3 fix_legends_from_xlsx.py --xlsx_files=local_data/legendas/entrada1/*.xlsx --debug --output_folder=output/export_legends --output_file=fixed_legends_indicators.csv --settings_labels=data/settings_labels.csv --to_fix=local_data/legendas/entrada2/legendas.csv

import glob
import argparse
import time
import pandas as pd
import xml.etree.ElementTree as ET
from utilities import convert_to_hexadecimal, create_folder_if_not_exists, generate_value_pairs

def main(args):
    xlsx_files = args.xlsx_files
    debug = args.debug
    output_folder_path = args.output_folder
    output_file = args.output_file
    path_settings_labels = args.settings_labels
    file_to_fix = args.to_fix

    if debug:
        print("Passed arguments:")
        print("XLSX files mask:", xlsx_files)
        print("File to fix:", file_to_fix)
        print("Settings labels file:", path_settings_labels)
        print("Debug mode:", debug)
        print("Output folder:", output_folder_path)
        print("Output file:", output_file)
        print("Complete output file path:", f"{output_folder_path}/{output_file}")

    setting_labels = pd.read_csv(path_settings_labels, sep=';')
    df_files_to_fix = pd.read_csv(file_to_fix, sep='|')
    # Imprimir Tipos de cada coluna: indicator_id|min|max|legend_id

    create_folder_if_not_exists(output_folder_path)
    xlsx_files = glob.glob(xlsx_files, recursive=True)
    print(f'Found {len(xlsx_files)} XLSX files')

    column_relation_data = {
        'id': [],
        'label': [],
        'color': [],
        'minvalue': [],
        'maxvalue': [],
        'legend_id': [],
        'indicator_id': [],
        'tag': [],
        'order': []
    }

    df_final = pd.DataFrame(column_relation_data)
    control_index_legend = 1000
    new_legend_id = 141
    size_t = 5 # Intervalo de valores

    # for in df_files_to_fix
    for line in df_files_to_fix.itertuples():
        # indicator_id|min|max|legend_id

        indicator_id = line.indicator_id
        min_value = line.min
        max_value = line.max
        legend_id = line.legend_id
        # Verifica se o legend_id é None ou Nan 
        if pd.isnull(legend_id):
            print(f"legend_id is null. New legend_id: {legend_id}")
            data = []
            df_local = pd.DataFrame(column_relation_data)

            # Create a list with 5 values between [minimum and maximum]
            interval_min_max_list = generate_value_pairs(min_value, max_value, size_t)
            # bsucar a key no df_files_to_fix 'indicator_id'
            if debug:
                print(f"Interval min max list: {interval_min_max_list}")
            interval_min_max_list.append([None, None])

            # Iterate through the settings_labels.csv and create a list of values for each row
            quant_labels = len(setting_labels)
            for index_s, row in setting_labels.iterrows():
                label = row['label']
                color = row['color']
                order = row['order']
                tag = row['tag']  

                minvalue = interval_min_max_list[index_s][0]
                maxvalue = interval_min_max_list[index_s][1]        
                
                control_index_legend += 1

                if index_s == quant_labels - 1:
                    tag = None
                
                data.append((control_index_legend, label, color, minvalue, maxvalue, new_legend_id, order, tag, indicator_id))
            
                control_index_legend += 1

            df_local = df_local.append(pd.DataFrame(data, columns=['id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id','order', 'tag', 'indicator_id']), ignore_index=True)

            df_final = df_final.append(df_local, ignore_index=True)
            new_legend_id += 1


    # Save the final dataframe
    # Change data types
    df_final['id'] = df_final['id'].astype(int)
    # df_final['legend_id'] = df_final['legend_id'].astype(int)
    df_final['order'] = df_final['order'].astype(int)

    # Save the final dataframe. Save in encoding='utf-8'
    df_final.to_csv(f'{output_folder_path}/{output_file}', index=False, encoding='utf-8')
    print(f"File {output_file} saved in {output_folder_path}")

    exit()

    for i, full_path_xlsx in enumerate(xlsx_files):
        print(f"\nStarting processing for indicator_id {i}: {full_path_xlsx}")

        

        # Read the input XLSX file using pandas
        df_values = pd.read_excel(full_path_xlsx, engine='openpyxl')

        # Sort by column name
        df_values = df_values.sort_index(axis=1)

        # Exclude columns without numbers in the name
        df_values = df_values[df_values.columns[df_values.columns.str.contains('\d')]]

        # Pattern of column name xxxx-yyyy or xxxx-yyyy-z: find all columns with the same number at the beginning of the name up to the hyphen and group them
        # Create a dictionary with the column name and its value. The value should be a list of values from each row that had the column name pattern

        df_local = pd.DataFrame(column_relation_data)
        data = []

        # Populando dict_columns com os valores da coluna indicator_id
        lista_indicator_id = df_files_to_fix['indicator_id'].unique()

        for key in lista_indicator_id:
          
            # Buscar a linha em df_files_to_fix com o indicator_id = key
            df_values_columns = df_values[key]
            print(f"df_values_columns: {df_values_columns}")
            exit()
            
            min_value = df_values_columns.min().min()
            max_value = df_values_columns.max().max()
            if debug:
                print(f"\nMin value: {min_value}")
                print(f"Max value: {max_value}")
            
            # Verify if the minimum or maximum value is None or nan
            if pd.isnull(min_value) or pd.isnull(max_value):
                # Create a list with 5 values between [minimum and maximum]
                interval_min_max_list = generate_value_pairs(min_value, max_value, size_t)
                # bsucar a key no df_files_to_fix 'indicator_id'
                if debug:
                    print(f"Interval min max list: {interval_min_max_list}")
                interval_min_max_list.append([None, None])

                # Iterate through the settings_labels.csv and create a list of values for each row
                quant_labels = len(setting_labels)
                for index_s, row in setting_labels.iterrows():
                    label = row['label']
                    color = row['color']
                    order = row['order']
                    tag = row['tag']  

                    minvalue = interval_min_max_list[index_s][0]
                    maxvalue = interval_min_max_list[index_s][1]        
                    
                    control_index_legend += 1

                    if index_s == quant_labels - 1:
                        tag = None
                    
                    data.append((control_index_legend, label, color, minvalue, maxvalue, legend_id, order, tag, key))
                
                    control_index_legend += 1
                legend_id += 1
        df_local = df_local.append(pd.DataFrame(data, columns=['id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id','order', 'tag', 'indicator_id']), ignore_index=True)

        df_final = df_final.append(df_local, ignore_index=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--xlsx_files", required=True,
                        help="Path to the directory where the XLSX files are located. Use glob patterns to find the XLSX files.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--settings_labels", default='settings_labels.csv', required=False,
                        help="Name of the settings_labels.csv file. Labels for the legends: label, color, order, tag.")
    parser.add_argument("--to_fix", required=True,
                        help="File to fix.") 
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
