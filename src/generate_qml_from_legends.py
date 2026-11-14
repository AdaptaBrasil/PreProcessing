#!/usr/bin/env python

# Run: python3 generate_qml_from_legends.py --output_dir=output/output_qmls --file_legends=local_data/qml_from_legends/csv2/legendas.csv
# Opcional: --file_scenarios=local_data/qml_from_legends/csv2/cenarios.csv

import argparse
import os
import uuid
import xml.etree.ElementTree as ET
from decimal import Decimal
from xml.dom import minidom

import pandas as pd

QML_BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'qml_base.qml')
UNAVAILABLE_SYMBOLS = {"Dado indisponivel", "Dado indisponível"}
UNAVAILABLE_SYMBOL_NAME = "Dado indisponivel"
UNAVAILABLE_LABEL = "Dado indisponível"


def hex_to_rgba(hex_color, alpha):
    """'#FF8300' -> '255,131,0,<alpha>'"""
    hex_color = hex_color.lstrip("#")
    return ",".join(map(str, [int(hex_color[i:i + 2], 16) for i in (0, 2, 4)] + [alpha]))


def format_number(value):
    """Decimal text without float noise: 0.30000000000000004 -> '0.3', 0.0 -> '0.0'."""
    text = repr(round(float(value), 10))
    return format(Decimal(text), 'f') if 'e' in text else text


def _add_data_defined_properties(parent):
    data_defined_properties = ET.SubElement(parent, "data_defined_properties")
    option = ET.SubElement(data_defined_properties, "Option", attrib={"type": "Map"})
    ET.SubElement(option, "Option", attrib={"type": "QString", "name": "name", "value": ""})
    ET.SubElement(option, "Option", attrib={"name": "properties"})
    ET.SubElement(option, "Option", attrib={"type": "QString", "name": "type", "value": "collection"})


def build_renderer_xml(legend_subset):
    """Build the <ranges> and <symbols> XML for one legend."""
    renderer_v2 = ET.Element("renderer-v2", attrib={})

    ranges = ET.SubElement(renderer_v2, "ranges")
    for _, legend_row in legend_subset.iterrows():
        if legend_row['SYMBOL'] in UNAVAILABLE_SYMBOLS:
            label = UNAVAILABLE_LABEL
            symbol = UNAVAILABLE_SYMBOL_NAME
        else:
            # label="-0,032 - -0,014"
            label = (f"{format_number(legend_row['MINVALUE']).replace('.', ',')} - "
                     f"{format_number(legend_row['MAXVALUE']).replace('.', ',')}")
            symbol = str(legend_row['SYMBOL'])
        ET.SubElement(ranges, "range", attrib={
            "lower": f"{legend_row['MINVALUE']:.3f}" if pd.notna(legend_row['MINVALUE']) else "",
            "symbol": symbol,
            "label": label,
            "uuid": str(uuid.uuid4()),
            "render": "true",
            "upper": f"{legend_row['MAXVALUE']:.3f}" if pd.notna(legend_row['MAXVALUE']) else ""
        })

    symbols = ET.SubElement(renderer_v2, "symbols")
    layer_id = str(uuid.uuid4())
    for _, legend_row in legend_subset.iterrows():
        name = UNAVAILABLE_SYMBOL_NAME if legend_row['SYMBOL'] in UNAVAILABLE_SYMBOLS else str(legend_row['SYMBOL'])
        symbol = ET.SubElement(symbols, "symbol", attrib={
            "alpha": "1",
            "clip_to_extent": "1",
            "frame_rate": "10",
            "force_rhr": "0",
            "type": "fill",
            "name": name,
            "is_animated": "0"
        })
        _add_data_defined_properties(symbol)
        layer = ET.SubElement(symbol, "layer", attrib={
            "locked": "0",
            "pass": "0",
            "enabled": "1",
            "class": "SimpleFill",
            "id": layer_id
        })
        option = ET.SubElement(layer, "Option", attrib={"type": "Map"})
        for name_, value in [
            ("border_width_map_unit_scale", "3x:0,0,0,0,0,0"),
            ("color", hex_to_rgba(legend_row['COLOR'], 255)),
            ("joinstyle", "bevel"),
            ("offset", "0,0"),
            ("offset_map_unit_scale", "3x:0,0,0,0,0,0"),
            ("offset_unit", "MM"),
            ("outline_color", "35,35,35,255"),
            ("outline_style", "solid"),
            ("outline_width", "0.26"),
            ("outline_width_unit", "MM"),
            ("style", "solid"),
        ]:
            ET.SubElement(option, "Option", attrib={"type": "QString", "name": name_, "value": value})
        _add_data_defined_properties(layer)

    xml_str = minidom.parseString(ET.tostring(renderer_v2)).toprettyxml(indent="  ")
    # Drop the XML declaration and the <renderer-v2> wrapper lines
    return "\n".join(xml_str.split("\n")[2:-2])


def write_qml(qml_path, legend_subset):
    with open(QML_BASE_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    with open(qml_path, 'w', encoding='utf-8') as new_file:
        new_file.write(content.replace("{{RANGES_SYMBOLS}}", build_renderer_xml(legend_subset)))
    print(f"Gerando o arquivo QML salvo em {qml_path}")


def create_qml_with_scenarios(legend_data, scenario_data, output_dir):
    # The legend depends only on the indicator, so each indicator's QML is written once
    written = set()
    for _, row in scenario_data.iterrows():
        legend_subset = legend_data[legend_data['LEGEND_ID'] == row['INDICATOR_ID']]
        if legend_subset.empty:
            continue

        indicator_id = int(row['INDICATOR_ID']) - 201000
        scenario_id = int(row['SCENARIO_ID']) if pd.notna(row['SCENARIO_ID']) else None
        print("\nProcessando o indicador:", indicator_id, ", cenário:", scenario_id, "e ano:", int(row['YEAR']))
        if indicator_id in written:
            continue

        write_qml(os.path.join(output_dir, f"{indicator_id}.qml"), legend_subset)
        written.add(indicator_id)

    print(f"\nProcesso concluído! Todos os arquivos QML foram salvos em {output_dir}")


def validate_legend_values(legend_data):
    """Check, per LEGEND_ID, that MINVALUE < MAXVALUE and that each class starts
    0.01 after the previous one ends. Returns True if every legend is valid."""
    all_valid = True
    for legend_id, group in legend_data.groupby('LEGEND_ID'):
        previous_max_value = None
        is_valid = True

        for _, row in group.iterrows():
            if row['SYMBOL'] in UNAVAILABLE_SYMBOLS:
                continue

            min_value = row['MINVALUE']
            max_value = row['MAXVALUE']
            if pd.isnull(min_value) or pd.isnull(max_value):
                print(f"Erro no registro ID {row['LEGEND_ID']}: MINVALUE ou MAXVALUE nulos no LEGEND_ID {legend_id}")
                is_valid = False
                continue

            # Compare in hundredths as integers to avoid float noise
            min_value = int((Decimal(min_value) * 100).quantize(Decimal('0')))
            max_value = int((Decimal(max_value) * 100).quantize(Decimal('0')))

            if min_value >= max_value:
                print(f"Erro LEGEND_ID {legend_id}:  MINVALUE{min_value} >= MAXVALUE{max_value}")
                is_valid = False

            if previous_max_value is not None and min_value != previous_max_value + 1:
                print(f"Erro no registro ID {row['LEGEND_ID']}: MINVALUE {min_value} não segue MAXVALUE anterior {previous_max_value} + 0.01 no LEGEND_ID {legend_id}")
                is_valid = False

            previous_max_value = max_value

        if is_valid:
            print(f"Todos os valores de legendas estão corretos para o LEGEND_ID: {legend_id}")
        all_valid = all_valid and is_valid

    return all_valid


def create_qml(legend_data, output_dir):
    legend_ids = legend_data['LEGEND_ID'].unique().tolist()
    print(f"Lista de legendas únicas: {legend_ids}")
    legends_erros = []
    for indicator_id in legend_ids:
        legend_subset = legend_data[legend_data['LEGEND_ID'] == indicator_id]
        if legend_subset.empty:
            continue

        print("\n-------------------------------------------------------------------------")
        print("Processando o indicador:", str(indicator_id))
        print(f"Validando os valores das legendas para o indicador {indicator_id}")
        if not validate_legend_values(legend_subset):
            legends_erros.append(indicator_id)
            continue

        write_qml(os.path.join(output_dir, f"{indicator_id}.qml"), legend_subset)

    if not legends_erros:
        print(f"\nProcesso concluído! Todos os arquivos QML foram salvos em {output_dir}")
    else:
        print(f"\nProcesso concluído! Alguns arquivos QML não foram salvos devido a erros nos valores das legendas: {legends_erros}")


def main(output_dir, file_legends, file_scenarios):
    legends_df = pd.read_csv(file_legends)
    os.makedirs(output_dir, exist_ok=True)

    if file_scenarios:
        create_qml_with_scenarios(legends_df, pd.read_csv(file_scenarios), output_dir)
    else:
        create_qml(legends_df, output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--file_legends", type=str, required=True, help="Legends file")
    parser.add_argument("--file_scenarios", type=str, help="Scenarios file", default=None)
    args = parser.parse_args()

    main(args.output_dir, args.file_legends, args.file_scenarios)
