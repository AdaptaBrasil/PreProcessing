# !/usr/bin/env python
# coding: utf-8

"""
Example:

python3 src/generate_legends_description_from_values.py \
    --values_file local_data/novos_dados/impactos3_1709_seg_hid/valores.xlsx \
    --description_file local_data/novos_dados/impactos3_1709_seg_hid/descricao.xlsx \
    --output_folder=local_data/temp/impactos3_1709_seg_hid/ \
    --settings_labels=data/settings_labels.csv

"""
import argparse
import time
import pandas as pd
import math
from utilities import generate_continuous_intervals, validate_continuous_intervals, trunc


class ModelMinMax:
    def __init__(self, code, min_value, max_value):
        self.code = code
        self.min_value = min_value
        self.max_value = max_value
        
class ListMinMax:
    def __init__(self):
        self.list_min_max = []
        
    def add(self, code, min_value, max_value):
        found = False
        for item in self.list_min_max:
            if item.code == code:
                found = True
                if min_value < item.min_value:
                    item.min_value = min_value
                if max_value > item.max_value:
                    item.max_value = max_value
                break
        if not found:
            self.list_min_max.append(ModelMinMax(code, min_value, max_value))
            
    def sort(self):
        self.list_min_max.sort(key=lambda x: x.code)

    def print(self):
        for item in self.list_min_max:
            print(f"Code: {item.code}, Min: {item.min_value}, Max: {item.max_value}")


def main(args):
    values_file = args.values_file
    description_file = args.description_file
    debug = args.debug
    output_folder = args.output_folder
    path_settings_labels = args.settings_labels
    DECIMAL_PLACES = 1

    if debug:
        print("Passed arguments:")
        print("values_file:", values_file)
        print("description_file:", description_file)
        print("Settings labels file:", path_settings_labels)
        print("Debug mode:", debug)
        print("Output folder:", output_folder)
        
    # Cria a pasta de saída se não existir
    import os
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # READ
    print("\n0. Reading input files...")
    try: 
        setting_labels = pd.read_csv(path_settings_labels, sep=';')
        df_values = pd.read_excel(values_file, engine='openpyxl')
        df_description = pd.read_excel(description_file, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Error reading input files: {e}")
    
    if df_values.empty or df_description.empty or setting_labels.empty:
        raise ValueError("One of the input files is empty.")

    # CONFIGURE DATAFRAME
    column_relation_data = {
        'codigo': pd.Series(dtype='int'),
        'indicator_id': pd.Series(dtype='int'),
        'label': pd.Series(dtype='str'),
        'cor': pd.Series(dtype='str'),
        'minimo': pd.Series(dtype='float'),
        'maximo': pd.Series(dtype='float'),
        'ordem': pd.Series(dtype='int')
    }
    
    # CLEAN DATAFRAME
    df_final = pd.DataFrame(column_relation_data)
    df_values = df_values.drop(columns=['id'])
    df_values = df_values.dropna(how='all')
    
    # MODEL MIN MAX
    list_min_max = ListMinMax()
    
    print("\n\n1. Read values from the input file and determine min and max for each indicator: ")
    for nome_coluna, coluna_series in df_values.items():
        print(f"Processing column: {nome_coluna}")
        
        code = nome_coluna.split('-')[0]
    
        minimo = coluna_series.min()
        max_value = coluna_series.max()
        
        if math.isnan(minimo) or math.isnan(max_value):
            raise ValueError(f"Column {nome_coluna} has NaN values for min or max.")
        
        list_min_max.add(code, minimo, max_value)
        
    print("\n\n2. Create legends for indicators: ")
    legend_id = 1
    for model in list_min_max.list_min_max:
        code = model.code
        
        if math.isnan(model.min_value) or math.isnan(model.max_value):
            raise ValueError(f"Indicator {code} has NaN for min value.")
        values = generate_continuous_intervals(model.min_value, model.max_value, 5)
        
        # Validate continuity of intervals
        is_valid, error_messages = validate_continuous_intervals(values)
        if not is_valid:
            print(f"Validation errors for indicator {code}:")
            for error in error_messages:
                print(error)
            raise ValueError(f"Intervals for indicator {code} are not continuous.")
        else:
            print(f"Intervals for indicator {code} are continuous and valid.")
        
        for j, sl in setting_labels.iterrows():
            
            minimo = ""
            maximo = ""
            if sl.label != 'Dado indisponível':
                minimo = trunc(values[j][0], DECIMAL_PLACES)
                maximo = trunc(values[j][1], DECIMAL_PLACES)

            new_row = {
                'codigo': legend_id,
                'indicator_id': code,
                'label': sl.label,
                'cor': sl.color,
                'minimo': minimo,
                'maximo': maximo,
                'ordem': sl.order
            }
            df_final = df_final._append(new_row, ignore_index=True)
        legend_id+=1
    
    
    print("\n3. Final dataframe:")
    print(df_final.head(10))
    
    
    # ADD COLUMN 'legenda' IN df_description:
    # Fazer o match entre df_description['codigo'] e df_final['indicator_id'] e
    # preencher df_description['legenda'] com df_final['codigo'] (id da legenda).
    # Em caso de não haver match, preencher com string vazia e emitir warning.

    # 1) Normaliza tipos para garantir match confiável
    df_final['indicator_id'] = pd.to_numeric(df_final['indicator_id'], errors='coerce')
    df_description['codigo'] = pd.to_numeric(df_description['codigo'], errors='coerce')

    # 2) Mapeia indicator_id -> legenda (codigo da legenda), removendo duplicatas
    legend_map = (
        df_final[['indicator_id', 'codigo']]
        .drop_duplicates(subset=['indicator_id'])
        .rename(columns={'codigo': 'legenda'})
    )

    # 3) Merge vectorizado para evitar loops linha-a-linha
    df_description = df_description.merge(
        legend_map,
        left_on='codigo',
        right_on='indicator_id',
        how='left'
    )

    # 4) Limpa coluna auxiliar criada pelo merge e trata ausências
    if 'indicator_id' in df_description.columns:
        df_description = df_description.drop(columns=['indicator_id'])

    missing_mask = df_description['legenda'].isna()
    if missing_mask.any():
        missing_ids = df_description.loc[missing_mask, 'codigo'].dropna().unique()
        for mid in missing_ids:
            print(f"Warning: No matching legend found for indicator_id {int(mid)} in description file.")
    df_description['legenda'] = df_description['legenda'].fillna("")

    # Excluir a coluna indicator_id se existir de df_final
    if 'indicator_id' in df_final.columns:
        df_final = df_final.drop(columns=['indicator_id'])
    # Save the final dataframe. Save in encoding='utf-8'
    print("\n4. Saving output files...")
    df_final.to_excel(f'{output_folder}/legenda.xlsx', index=False)
    print(f"File {output_folder}/legenda.xlsx saved.")
    
    # Salva df_description atualizado
    df_description.to_excel(f'{output_folder}/descricao.xlsx', index=False)
    print(f"File {output_folder}/descricao.xlsx saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--values_file", required=True,
                        help="Entry file to be processed, with columns: id, indicator1, indicator2, ...")
    parser.add_argument("--description_file", required=True,
                        help="Description file with legends information.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--settings_labels", default='settings_labels.csv', required=False,
                        help="Name of the settings_labels.csv file. Labels for the legends: label, color, order, tag.")
    parser.add_argument("--output_folder", default='local_data/temp/', required=False,
                        help="Name of the output folder.")
    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"\nTotal time: {total_time_in_minutes} minutes")
