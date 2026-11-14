#!/usr/bin/env python
# coding: utf-8

# Examples: python3 merge_shapefiles_mesh.py --mesh_file=local_data/malha/ferrovias.shp --indicator_files_mask=local_data/indicadores/*.shp --column_relation_file=relacao_arquivos_colunas_malha_rodovias.xlsx --new_mesh_file=indicadores_rodovias.shp --average --debug --output_folder=output/result_shapefiles_mesh
#           python3 merge_shapefiles_mesh.py --mesh_file=D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\Ferrovias\FerroviasEmOperacao.shp --indicator_files_mask=D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\02_FERROVIAS_Adriano\04_BASE_DE_DADOS/*.shp --column_relation_file=teste.xlsx --new_mesh_file=indicadores_ferrovias_teste.shp --average --debug --output_folder=D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\output\teste

import argparse
import glob
import os
import time
import traceback
from datetime import datetime

import geopandas as gpd
import pandas as pd
from pyproj import CRS

import config
from utilities import create_folder_if_not_exists, find_indicator_column, load_shapefile, next_indicator_column_id

MESH_PK = 'mesh_file_pk'


def area_weighted_mean(mesh, indicator):
    """Mean of CL_ORIG per mesh feature, weighted by the area each indicator
    feature overlaps it. Falls back to a plain mean where all overlaps have
    zero area (e.g. point/line indicators)."""
    indicator = indicator[indicator['CL_ORIG'].notna()]
    pieces = gpd.overlay(mesh[[MESH_PK, 'geometry']], indicator[['CL_ORIG', 'geometry']],
                         how='intersection', keep_geom_type=False)
    pieces['weight'] = pieces.geometry.area
    pieces['weighted'] = pieces['CL_ORIG'] * pieces['weight']
    sums = pieces.groupby(MESH_PK)[['weighted', 'weight']].sum()
    result = sums['weighted'] / sums['weight'].where(sums['weight'] > 0)
    return result.fillna(pieces.groupby(MESH_PK)['CL_ORIG'].mean())


def main(args):
    indicator_files_mask = args.indicator_files_mask
    mesh_file_path = args.mesh_file
    mesh_file_pk = args.mesh_file_pk
    column_relation_file_name = args.column_relation_file
    updated_mesh_file_path = args.new_mesh_file
    is_average = args.average
    debug = args.debug
    output_folder_path = args.output_folder
    target_filters = args.target_filters

    if debug:
        print("\nCommand line arguments:")
        print("Indicator files mask:", indicator_files_mask)
        print("Mesh file:", mesh_file_path)
        print("Columns relation file:", column_relation_file_name)
        print("Updated mesh file:", updated_mesh_file_path)
        print("Average:", is_average)
        print("Debug mode:", debug)
        print("Output folder:", output_folder_path)
        print("Target Filters:", target_filters)
        print("Default CRS:", config.DEFAULT_CRS, "\n")

    create_folder_if_not_exists(output_folder_path)

    updated_mesh_file_path = os.path.join(output_folder_path, updated_mesh_file_path)
    column_relation_file_name = os.path.join(output_folder_path, column_relation_file_name)

    # Mesh line features are buffered by 10 m so they have an area to intersect
    mesh = load_shapefile(mesh_file_path, debug=debug, change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=True)
    print("Number of items in the mesh: ", len(mesh), "\n")
    if mesh_file_pk not in mesh.columns:
        raise SystemExit(f"Primary key column '{mesh_file_pk}' not found in the mesh. "
                         f"Available columns: {list(mesh.columns)}")
    mesh = mesh.rename(columns={mesh_file_pk: MESH_PK})  # force unique name for mesh pk
    # remove CL_ORIG column, if exists, to not make a mess with indicator CL_ORIG column.
    mesh = mesh.drop(columns=['CL_ORIG'], errors='ignore')

    next_col_id = next_indicator_column_id(mesh.columns)
    if debug:
        print("Next column ID: ", next_col_id)

    # Only resume from the relation file when the mesh already carries I_<n> columns
    # (i.e. the mesh passed in is the output of a previous run).
    if next_col_id > 0 and os.path.exists(column_relation_file_name):
        print("Columns relation file exists. Opening...")
        df_column_relation = pd.read_excel(column_relation_file_name)
    else:
        print("Columns relation file doesn't exist. Creating...")
        df_column_relation = pd.DataFrame({'file_name': [], 'column': []})

    if debug:
        print("Columns relation file head:  ", df_column_relation.head())

    indicator_shapefiles = sorted(glob.glob(indicator_files_mask, recursive=True))
    print("Number of indicator files found: ", len(indicator_shapefiles))

    def record(file_name, column):
        nonlocal df_column_relation
        df_column_relation = pd.concat(
            [df_column_relation, pd.DataFrame([{'file_name': file_name, 'column': column}])],
            ignore_index=True)
        df_column_relation.to_excel(column_relation_file_name, index=False)

    for indicator_file_path in indicator_shapefiles:
        try:
            file_name_only = os.path.basename(indicator_file_path).split('.')[0]
            if (df_column_relation['file_name'] == file_name_only).any():
                continue

            print(f"\nStarting the processing of file {indicator_file_path} {datetime.now()}")
            indicator = gpd.read_file(indicator_file_path)

            if 'ID' not in indicator.columns:
                indicator.insert(0, 'ID', range(1, len(indicator) + 1))

            col_name = find_indicator_column(['CL_ORIG', 'CL_N-0ORIG', 'N_ORIG'], indicator)
            if col_name is None:
                print(f'ERROR: Indicator column not found in {indicator_file_path}')
                record(file_name_only, None)
                continue
            indicator = indicator.rename(columns={col_name: "CL_ORIG"})

            # TODO: target_filters is not applied yet; it is only printed.
            if target_filters is not None:
                for i_filter, filter_name in enumerate(target_filters.split(",")):
                    print(f"Filtro {i_filter}: {filter_name}")
                print("\nColumns: ", indicator.columns)

            # FILT_RISC rule: drop features flagged 'Nao'
            for filter_column in ('FILT_RISC', 'FILT_RIS'):
                if filter_column in indicator.columns:
                    indicator = indicator[indicator[filter_column] != 'Nao']
                    break

            if debug:
                print("Old CRS of the indicator:", indicator.crs)
            indicator = indicator.to_crs(CRS.from_epsg(config.DEFAULT_CRS))
            if debug:
                print("New CRS of the indicator:", indicator.crs)

            if is_average:
                values = area_weighted_mean(mesh, indicator)
            else:
                intersection = gpd.sjoin(mesh, indicator, how='inner', predicate='intersects')
                values = intersection.groupby(MESH_PK)['CL_ORIG'].max()

            column_key = f'I_{next_col_id}'
            mesh[column_key] = mesh[MESH_PK].map(values)
            next_col_id += 1

            record(file_name_only, column_key)
            mesh.to_file(updated_mesh_file_path)

            print("\nUpdated mesh saved to: ", updated_mesh_file_path)
            print("Columns relation file saved to: ", column_relation_file_name)

        except Exception as ex:
            print(f'ERROR: {ex}\n')
            print(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh_file", required=True,
                        help="Path to the mesh file.")
    parser.add_argument("--mesh_file_pk", default='objectid',
                        help="Primary key field name of mesh file.")
    parser.add_argument("--indicator_files_mask", required=True,
                        help="Path to the indicator files mask. The glob function will be used to find the indicator files.")
    parser.add_argument("--column_relation_file", required=True,
                        help="Path to the columns relation file.")
    parser.add_argument("--new_mesh_file", required=True,
                        help="Path to the new updated mesh file.")
    parser.add_argument("--average", action='store_true',
                        help="Area-weighted average of the indicator values intersecting each mesh feature. If False, take the maximum value.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--output_folder", default='output',
                        help="Path to the directory that will be used to save the generated files (default: output).")
    parser.add_argument("--target_filters", default=None, required=False,
                        help="Filter columns (not applied yet)")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    total_time_in_minutes = (time.time() - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")
