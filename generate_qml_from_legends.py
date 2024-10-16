#!/usr/bin/env python

# Run: python3 generate_qml_from_legends.py --output_dir=output/output_qmls --file_legends=local_data/qml_from_legends/csv2/legendas.csv 
# Opcional: --file_scenarios=local_data/qml_from_legends/csv2/cenarios.csv

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import argparse
import uuid
from decimal import Decimal


# COnvert hex to rgba
def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    myTuple = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)
    # Convert to string separated by commas
    return ",".join(map(str, myTuple))

# Função para criar o arquivo QML
def create_qml_with_scenarios(legend_data, scenario_data, output_dir):
    for _, row in scenario_data.iterrows():
        
        indicator_id = row['INDICATOR_ID']
        scenario_id = row['SCENARIO_ID']
        year = row['YEAR']

        # Filtrar as legendas para o indicador específico
        legend_subset = legend_data[legend_data['LEGEND_ID'] == indicator_id]
        # Se o subconjunto de legendas estiver vazio, pular para o próximo indicador
        if legend_subset.empty:
            continue


        # Criar o nome do arquivo QML
        indicator_id = int(indicator_id) - 201000
        year = int(year)
        scenario_id = int(scenario_id) if pd.notna(scenario_id) else None

        print("\nProcessando o indicador:", str(indicator_id), ", cenário:", str(scenario_id), "e ano:", str(year))

        qml_filename = f"{indicator_id}.qml"

        qml_path = os.path.join(output_dir, qml_filename)


        # Criar a estrutura do QML

        renderer_v2 = ET.Element("renderer-v2", attrib={})

        ranges = ET.SubElement(renderer_v2, "ranges")

        for idx, legend_row in legend_subset.iterrows():
            
            # If not dado indisponível, label = "Dado indisponível"
            if legend_row['SYMBOL'] == "Dado indisponivel":
                label = "Dado indisponível"
                symbol = "Dado indisponivel"
            else:
                # New label: label="-0,032 - -0,014"
                minValue = str(legend_row['MINVALUE']).replace(".", ",")
                maxValue = str(legend_row['MAXVALUE']).replace(".", ",")

                label = f"{minValue} - {maxValue}"
                symbol = legend_row['SYMBOL']
            # If nan, continue
            if pd.isna(legend_row['MINVALUE']) or pd.isna(legend_row['MAXVALUE']):
                pass
            range_elem = ET.SubElement(ranges, "range", attrib={
                "lower": f"{legend_row['MINVALUE']:.3f}" if pd.notna(legend_row['MINVALUE']) else "",
                "symbol": symbol,
                "label": label,
                "uuid": str(uuid.uuid4()),
                "render": "true",
                "upper": f"{legend_row['MAXVALUE']:.3f}" if pd.notna(legend_row['MAXVALUE']) else ""
            })

        symbols = ET.SubElement(renderer_v2, "symbols")
        
        myUUID = uuid.uuid4()

        for idx, legend_row in legend_subset.iterrows():
            # If nan, continue
            if pd.isna(legend_row['MINVALUE']) or pd.isna(legend_row['MAXVALUE']):
                pass
                
            # If not dado indisponível, label = "Dado indisponível"
            if legend_row['SYMBOL'] == "Dado indisponivel":
                name = "Dado indisponivel"
            else:
                # New label: label="-0,032 - -0,014"
                name = legend_row['SYMBOL']
                
            symbol = ET.SubElement(symbols, "symbol", attrib={
                "alpha": "1",
                "clip_to_extent": "1",
                "frame_rate": "10",
                "force_rhr": "0",
                "type": "fill",
                "name": name,
                "is_animated": "0"
            })

            data_defined_properties = ET.SubElement(symbol, "data_defined_properties")
            option = ET.SubElement(data_defined_properties, "Option", attrib={"type": "Map"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "name", "value": ""})
            ET.SubElement(option, "Option", attrib={"name": "properties"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "type", "value": "collection"})
            layer = ET.SubElement(symbol, "layer", attrib={
                "locked": "0",
                "pass": "0",
                "enabled": "1",
                "class": "SimpleFill",
                "id": f"{myUUID}"
            })

            option = ET.SubElement(layer, "Option", attrib={"type": "Map"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "border_width_map_unit_scale", "value": "3x:0,0,0,0,0,0"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "color", "value": hex_to_rgba(legend_row['COLOR'], 255)})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "joinstyle", "value": "bevel"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "offset", "value": "0,0"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "offset_map_unit_scale", "value": "3x:0,0,0,0,0,0"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "offset_unit", "value": "MM"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_color", "value": "35,35,35,255"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_style", "value": "solid"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_width", "value": "0.26"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_width_unit", "value": "MM"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "style", "value": "solid"})

            data_defined_properties = ET.SubElement(layer, "data_defined_properties")
            option = ET.SubElement(data_defined_properties, "Option", attrib={"type": "Map"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "name", "value": ""})
            ET.SubElement(option, "Option", attrib={"name": "properties"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "type", "value": "collection"})

        # Salvar o arquivo QML
        tree = ET.ElementTree(renderer_v2)
        xml_str = minidom.parseString(ET.tostring(renderer_v2)).toprettyxml(indent="  ")
        # Remove as duas primeiras linhas e a última linha
        xml_str = "\n".join(xml_str.split("\n")[2:-2])

        # Lê o conteúdo do arquivo base
        with open("data/qml_base.qml", 'r') as file:
            content = file.read()

        # Substitui o marcador {{RANGES_SYMBOLS}} pelo nome inserido
        novo_conteudo = content.replace("{{RANGES_SYMBOLS}}", xml_str)

        # Salva o novo conteúdo em um arquivo novo
        with open(qml_path, 'w') as new_file:
            new_file.write(novo_conteudo)
        
        print(f"Gerando o arquivo QML salvo em {qml_path}")

    
    print(f"\nProcesso concluído! Todos os arquivos QML foram salvos em {output_dir}")

def validate_legend_values(legend_data):
    
    # Loop pelos dados agrupados pelo LEGEND_ID
    for legend_id, group in legend_data.groupby('LEGEND_ID'):
        previous_max_value = None
        is_valid = True
        
        # Loop pelos registros de cada grupo (exceto quando o SYMBOL for "Dado indisponivel")
        for idx, row in group.iterrows():
            symbol = row['SYMBOL']
            if symbol == 'Dado indisponivel':
                continue  # Pular registro de dados indisponíveis

            min_value = row['MINVALUE']
            max_value = row['MAXVALUE']
            
            # Verificar se MINVALUE e MAXVALUE não são nulos
            if pd.isnull(min_value) or pd.isnull(max_value):
                print(f"Erro no registro ID {row['LEGEND_ID']}: MINVALUE ou MAXVALUE nulos no LEGEND_ID {legend_id}")
                is_valid = False
                continue
            
            # Converter para Decimal
            min_value = Decimal(min_value) * 100
            max_value = Decimal(max_value) * 100

            # Aredondar para 1 casa decimal
            min_value = min_value.quantize(Decimal('0'))
            max_value = max_value.quantize(Decimal('0'))
            
            # Converter pra interiro 
            min_value = int(min_value)
            max_value = int(max_value)

            
            # Regra 1: MINVALUE deve ser menor que MAXVALUE
            if min_value >= max_value:
                print(f"Erro LEGEND_ID {legend_id}:  MINVALUE{min_value} >= MAXVALUE{max_value}")
                is_valid = False
            
            # Regra 2: MAXVALUE anterior deve ser igual a MINVALUE atual + 0.01
            if previous_max_value is not None:
                expected_min_value = previous_max_value + 1
                if min_value != expected_min_value:
                    print(f"Erro no registro ID {row['LEGEND_ID']}: MINVALUE {min_value} não segue MAXVALUE anterior {previous_max_value} + 0.01 no LEGEND_ID {legend_id}")
                    is_valid = False
            
            # Atualiza o MAXVALUE anterior para o próximo registro
            previous_max_value = max_value
        
        if is_valid:
            print(f"Todos os valores de legendas estão corretos para o LEGEND_ID: {legend_id}")

    return is_valid

# Função para criar o arquivo QML
def create_qml(legend_data, output_dir):
    lista_unica_legend_id = legend_data['LEGEND_ID'].unique().tolist()
    print(f"Lista de legendas únicas: {lista_unica_legend_id}")
    all_valid_legends = True
    legends_erros = []
    for indicator_id in lista_unica_legend_id:

        # Filtrar as legendas para o indicador específico
        legend_subset = legend_data[legend_data['LEGEND_ID'] == indicator_id]
        
        # Se o subconjunto de legendas estiver vazio, pular para o próximo indicador
        if legend_subset.empty:
            continue

        # Criar o nome do arquivo QML
        print("\n-------------------------------------------------------------------------")
        print("Processando o indicador:", str(indicator_id))

        # Validar os valores das legendas
        print(f"Validando os valores das legendas para o indicador {indicator_id}")
        is_valid = validate_legend_values(legend_subset)
        if not is_valid:
            all_valid_legends = False
            legends_erros.append(indicator_id)
            continue

        qml_filename = f"{indicator_id}.qml"
        qml_path = os.path.join(output_dir, qml_filename)

        # Criar a estrutura do QML
        renderer_v2 = ET.Element("renderer-v2", attrib={})
        ranges = ET.SubElement(renderer_v2, "ranges")
        for idx, legend_row in legend_subset.iterrows():
            
            # If not dado indisponivel, label = "Dado indisponivel"
            if legend_row['SYMBOL'] == "Dado indisponivel":
                label = "Dado indisponível"
                symbol = "Dado indisponivel"
            else:
                # New label: label="-0,032 - -0,014"
                minValue = str(legend_row['MINVALUE']).replace(".", ",")
                maxValue = str(legend_row['MAXVALUE']).replace(".", ",")

                label = f"{minValue} - {maxValue}"
                symbol = legend_row['SYMBOL']
            # If nan, continue
            if pd.isna(legend_row['MINVALUE']) or pd.isna(legend_row['MAXVALUE']):
                pass
            range_elem = ET.SubElement(ranges, "range", attrib={
                "lower": f"{legend_row['MINVALUE']:.3f}" if pd.notna(legend_row['MINVALUE']) else "",
                "symbol": symbol,
                "label": label,
                "uuid": str(uuid.uuid4()),
                "render": "true",
                "upper": f"{legend_row['MAXVALUE']:.3f}" if pd.notna(legend_row['MAXVALUE']) else ""
            })

        symbols = ET.SubElement(renderer_v2, "symbols")
        
        myUUID = uuid.uuid4()

        for idx, legend_row in legend_subset.iterrows():
            # If nan, continue
            if pd.isna(legend_row['MINVALUE']) or pd.isna(legend_row['MAXVALUE']):
                pass
                
            # If not dado indisponivel, label = "Dado indisponivel"
            if legend_row['SYMBOL'] == "Dado indisponivel":
                name = "Dado indisponivel"
            else:
                # New label: label="-0,032 - -0,014"
                name = legend_row['SYMBOL']
                
            symbol = ET.SubElement(symbols, "symbol", attrib={
                "alpha": "1",
                "clip_to_extent": "1",
                "frame_rate": "10",
                "force_rhr": "0",
                "type": "fill",
                "name": name,
                "is_animated": "0"
            })

            data_defined_properties = ET.SubElement(symbol, "data_defined_properties")
            option = ET.SubElement(data_defined_properties, "Option", attrib={"type": "Map"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "name", "value": ""})
            ET.SubElement(option, "Option", attrib={"name": "properties"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "type", "value": "collection"})
            layer = ET.SubElement(symbol, "layer", attrib={
                "locked": "0",
                "pass": "0",
                "enabled": "1",
                "class": "SimpleFill",
                "id": f"{myUUID}"
            })

            option = ET.SubElement(layer, "Option", attrib={"type": "Map"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "border_width_map_unit_scale", "value": "3x:0,0,0,0,0,0"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "color", "value": hex_to_rgba(legend_row['COLOR'], 255)})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "joinstyle", "value": "bevel"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "offset", "value": "0,0"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "offset_map_unit_scale", "value": "3x:0,0,0,0,0,0"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "offset_unit", "value": "MM"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_color", "value": "35,35,35,255"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_style", "value": "solid"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_width", "value": "0.26"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "outline_width_unit", "value": "MM"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "style", "value": "solid"})

            data_defined_properties = ET.SubElement(layer, "data_defined_properties")
            option = ET.SubElement(data_defined_properties, "Option", attrib={"type": "Map"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "name", "value": ""})
            ET.SubElement(option, "Option", attrib={"name": "properties"})
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": "type", "value": "collection"})

        # Salvar o arquivo QML
        tree = ET.ElementTree(renderer_v2)
        xml_str = minidom.parseString(ET.tostring(renderer_v2)).toprettyxml(indent="  ")
        # Remove as duas primeiras linhas e a última linha
        xml_str = "\n".join(xml_str.split("\n")[2:-2])

        # Lê o conteúdo do arquivo base
        with open("data/qml_base.qml", 'r') as file:
            content = file.read()

        # Substitui o marcador {{RANGES_SYMBOLS}} pelo nome inserido
        novo_conteudo = content.replace("{{RANGES_SYMBOLS}}", xml_str)

        # Salva o novo conteúdo em um arquivo novo
        with open(qml_path, 'w') as new_file:
            new_file.write(novo_conteudo)
        
        print(f"Gerando o arquivo QML salvo em {qml_path}")

    
    if all_valid_legends:
        print(f"\nProcesso concluído! Todos os arquivos QML foram salvos em {output_dir}")
    else:
        print(f"\nProcesso concluído! Alguns arquivos QML não foram salvos devido a erros nos valores das legendas: {legends_erros}")


# Função principal
def main(output_dir, file_legends, file_scenarios):
    # Carregar os dados das planilhas CSV
    legends_df = pd.read_csv(file_legends)

    # Criar o diretório de saída se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Gerar os arquivos QML
    # Verifica se o arquivo de cenários foi fornecido
    if file_scenarios:
        scenarios_df = pd.read_csv(file_scenarios)
        create_qml_with_scenarios(legends_df, scenarios_df, output_dir)
    else:
        create_qml(legends_df, output_dir)

# Executar o script
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, help="Output directory")
    parser.add_argument("--file_legends", type=str, help="Legends file")
    parser.add_argument("--file_scenarios", type=str, help="Scenarios file", default=None)

    args = parser.parse_args()

    output_dir = args.output_dir
    file_legends = args.file_legends
    file_scenarios = args.file_scenarios

    main(output_dir, file_legends, file_scenarios)