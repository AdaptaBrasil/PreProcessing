#!/usr/bin/env python
# coding: utf-8

# Example: python3 fix_legends_from_csv.py --debug --output_folder=output/export_legends --output_file=fixed_legends_from_csv_indicators.csv --settings_labels=data/settings_labels.csv --to_fix=local_data/impactos_economicos_csv/input_values_ie.csv

import glob
import argparse
import time
import pandas as pd
from utilities import create_folder_if_not_exists, generate_value_pairs_fixed_zero, trunc

def truncate_numbers(lista, x):
    # Função para truncar um único número
    def truncate_number(n, x):
        if n is None:
            return None
        n_str = f"{n:.{x+10}f}"  # Converte para string com algumas casas decimais a mais
        point_index = n_str.find('.')  # Encontra a posição do ponto decimal
        if point_index != -1:
            truncated_str = n_str[:point_index + x + 1]  # Trunca a string mantendo 'x' casas decimais
            return float(truncated_str)  # Converte de volta para float
        else:
            return n  # Retorna o número original se não houver ponto decimal

    # Aplica a função de truncar a cada número na lista de listas
    truncated_list = [[truncate_number(num, x) for num in sublist] for sublist in lista]
    return truncated_list

def verify_list(lista, precision):
    for i in range(len(lista)):
        # Verifica se o par é [None, None]
        if lista[i] == [None, None]:
            return False
        
        # Para todos os itens, exceto o último, verifica se o próximo começa com o valor esperado
        if i < len(lista) - 1:
            current_end = lista[i][1]
            next_start = lista[i+1][0]
            
            # Calcula o valor esperado para o início do próximo item
            expected_start = current_end + precision
            
            # Verifica se o valor atual é diferente do esperado
            if abs(next_start - expected_start) > 1e-9:  # Usa uma pequena margem para evitar erros de ponto flutuante
                return False
    
    return True

def fix_precision_interval_min_max_list(lista, precision):
    # Remove os pares [None, None]
    lista = [par for par in lista if par != [None, None]]
    
    # Corrige os valores com base na precisão
    for i in range(1, len(lista)):
        prev_end = lista[i-1][1]
        current_start = lista[i][0]
        
        # Verifica se o item atual começa com o valor esperado; ajusta se necessário
        expected_start = prev_end + precision
        if current_start != expected_start:
            lista[i][0] = expected_start
    
    return lista

def main(args):
    debug = args.debug
    output_folder_path = args.output_folder
    output_file = args.output_file
    path_settings_labels = args.settings_labels
    file_to_fix = args.to_fix

    if debug:
        print("Passed arguments:")
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
    control_index_id = 1
    control_legend_id = 1
    PRECISION = 0.01
    TRUNC_DECIMAL = 2
    is_valid_overlapping = True
    count_indicators = 0
        
    size_t = 5 # Intervalo de valores

    # for in df_files_to_fix
    for line in df_files_to_fix.itertuples():
        count_indicators += 1
        # indicator_id|min|max|legend_id

        indicator_id = line.indicator_id
        min_value = line.min
        max_value = line.max

        print(f"\nFix indicator_id: {indicator_id}")
        data = []
        # Ler no padrão eua
        df_local = pd.DataFrame(column_relation_data)
        # Converter os números para float
        df_local['minvalue'] = df_local['minvalue'].astype(float)

        # Create a list with 5 values between [minimum and maximum]
        # Verificar se o min_value e o max_value são None ou Nan
        if pd.isnull(min_value) or pd.isnull(max_value):
            print(f"min_value or max_value is null. New indicator_id: {indicator_id}")
            # Criar interval_min_max_list com 5 valores [None, None]
            interval_min_max_list = [[None, None]] * size_t
            is_valid_overlapping = is_valid_overlapping and True
        else:
            # Set type to float
            min_value = float(min_value)
            max_value = float(max_value)
            interval_min_max_list = generate_value_pairs_fixed_zero(min_value, max_value, size_t)

            # Equanto verify_list não for True, continue ajustando
            while not verify_list(interval_min_max_list, PRECISION):
                interval_min_max_list = fix_precision_interval_min_max_list(interval_min_max_list, PRECISION)
                interval_min_max_list = truncate_numbers(interval_min_max_list, TRUNC_DECIMAL)
                print("Ajustando valores...")
            is_valid_overlapping = is_valid_overlapping and verify_list(interval_min_max_list, PRECISION)
        interval_min_max_list.append([None, None])
        
        if debug:
            print(interval_min_max_list)

        # Iterate through the settings_labels.csv and create a list of values for each row
        quant_labels = len(setting_labels)
        for index_s, row in setting_labels.iterrows():
            label = row['label']
            color = row['color']
            order = row['order']
            tag = row['tag']  

            minvalue = interval_min_max_list[index_s][0]
            maxvalue = interval_min_max_list[index_s][1]
            
            final_char = ", "
            if index_s == quant_labels - 1:
                tag = 'None'
                final_char = ""

            #print([minvalue, maxvalue], end=final_char)
            
            data.append((control_index_id, label, color, minvalue, maxvalue, control_legend_id, order, tag, indicator_id))
        
            control_index_id += 1
        control_legend_id += 1
        print()

        # Versão com append
        # df_local = df_local.append(pd.DataFrame(data, columns=['id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id','order', 'tag', 'indicator_id']), ignore_index=True)
        # df_final = df_final.append(df_local, ignore_index=True)

        # Versão com concat
        df_local = pd.concat([df_local, pd.DataFrame(data, columns=['id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id','order', 'tag', 'indicator_id'])], ignore_index=True)
        df_final = pd.concat([df_final, df_local], ignore_index=True)

    # Save the final dataframe
    # Change data types
    df_final['id'] = df_final['id'].astype(int)
    df_final['legend_id'] = df_final['legend_id'].astype(int)
    df_final['order'] = df_final['order'].astype(int)

    # Save the final dataframe. Save in encoding='utf-8'
    df_final.to_csv(f'{output_folder_path}/{output_file}', index=False, encoding='utf-8')
    print(f"File saved in: {output_folder_path}/{output_file}")
    # count_indicators
    print(f"Total of indicators: {count_indicators}")
    # IS VALID OVERLAPPING
    if is_valid_overlapping:
        print("Todos os intervalos estão corretos.")
    else:
        print("Há intervalos incorretos.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
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
