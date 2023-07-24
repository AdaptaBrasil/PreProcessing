#!/usr/bin/env python
# coding: utf-8

# Example: python3 merge_shapefiles_mesh.py --mesh_file=malha/ferrovias.shp --indicator_files_mask=indicadores/*.shp --column_relation_file=relacao_arquivos_colunas_malha_rodovias.xlsx --new_mesh_file=indicadores_rodovias.shp --average --debug --output_folder=output/confusion_shapefiles_mesh

import pandas as pd
import geopandas as gpd
from pyproj import CRS
import os
import glob
from datetime import datetime
import argparse
from utilities import create_folder_if_not_exists, load_shapefile, find_indicator_column
import config
import warnings
import time

# Ignore warnings
warnings.filterwarnings("ignore")


def main(args):
    # Input files with shapefile data for indicators and mesh
    indicator_files_mask = args.indicator_files_mask
    mesh_file_path = args.mesh_file
    column_relation_file_name = args.column_relation_file
    updated_mesh_file_path = args.new_mesh_file
    is_average = args.average
    debug = args.debug
    output_folder_path = args.output_folder

    if debug:
        print("Passed arguments:")
        print("Indicator files mask:", indicator_files_mask)
        print("Mesh file:", mesh_file_path)
        print("Columns relation file:", column_relation_file_name)
        print("Updated mesh file:", updated_mesh_file_path)
        print("Average:", is_average)
        print("Debug mode:", debug)
        print("Output folder:", output_folder_path)
        print("Default CRS:", config.DEFAULT_CRS, "\n")

    # Create output folder if it doesn't exist
    create_folder_if_not_exists(output_folder_path)

    # Concatenate the output/ with the output file name
    updated_mesh_file_path = os.path.join(
        f'{output_folder_path}', updated_mesh_file_path)
    column_relation_file_name = os.path.join(
        f'{output_folder_path}', column_relation_file_name)

    # Load the shapefile mesh
    mesh = load_shapefile(mesh_file_path, debug=debug,
                          change_crs=True, epsg=config.DEFAULT_CRS, set_buffer=True)
    print("Number of items in the mesh: ", len(mesh), "\n")

    # Get next column ID
    nextColId = 1
    if 'I_1' in mesh.columns:
        lastCol = mesh.columns[len(mesh.columns)-2]
        nextColId = int(lastCol[2:]) + 1

    print("Próximo ID de coluna: ", nextColId)

    # Verify if the columns relation file exists.
    if nextColId > 1:
        print("Columns relation file exists. Opening...")
        # Load the columns relation file
        df_column_relation = pd.read_excel(column_relation_file_name)
    else:
        print("Columns relation file doesn't exist. Creating...")
        # Create the columns relation file
        column_relation_data = {
            'file_name': [],
            'column': []
        }
        df_column_relation = pd.DataFrame(column_relation_data)

    if debug:
        print("Columns relation file head:  ", df_column_relation.head())

    indicator_shapefiles = glob.glob(indicator_files_mask, recursive=True)

    print("Number of indicator files found: ", len(indicator_shapefiles))

    # Print the names of the .shp files found
    for i, indicator_file_path in enumerate(indicator_shapefiles):
        try:
            # Get the file name without extension
            file_name_only = os.path.basename(
                indicator_file_path).split('.')[0]
            already_processed = df_column_relation.loc[df_column_relation['file_name']
                                                       == file_name_only]
            if len(already_processed) > 0:
                continue

            print(
                f"\nStarting the processing of file {i}: {indicator_file_path} {datetime.now()}")
            indicator = gpd.read_file(indicator_file_path)

            if debug:
                print("Old CRS of the indicator:", indicator.crs)

            # Change to EPSG 5880 CRS or Default CRS
            indicator = indicator.to_crs(CRS.from_epsg(config.DEFAULT_CRS))

            # Add ID column if it doesn't exist
            if not 'ID' in indicator.columns:
                indicator.insert(0, 'ID', range(1, len(indicator)+1))

            col_name = find_indicator_column(['CL_ORIG', 'CL_N-0ORIG', 'N_ORIG'], indicator)
            if col_name is None:
                if debug:
                    print(f'ERROR: Column not found in {indicator_file_path}')
                new_row = {'file_name': file_name_only, 'column': col_name}
                df_column_relation = df_column_relation.append(
                    new_row, ignore_index=True)
                continue
            else:
                indicator.rename(columns={col_name: "CL_ORIG"}, inplace=True)

            if debug:
                print("New CRS of the indicator:", indicator.crs)

            # Perform the spatial join based on geometry intersection
            intersection = gpd.sjoin(
                mesh, indicator, how='inner', op='intersects')

            # Create GeoDataFrame with desired fields
            gdf = gpd.GeoDataFrame(
                intersection[['ID', 'objectid']], geometry=intersection.geometry)
            
            if debug:
                print(f"Quantidade de volumes para {i}: ", len(indicator))
                print(f"Quantidade de intersecoes para {i}: ", len(intersection))

            # Next column ID to be added to the mesh table
            column_key = 'I_' + str(i)

            # Create the new column "I_i" and set a float value
            # For example, set the value -1 to all records
            mesh[column_key] = -1.0

            # Exibir o GeoDataFrame com a nova coluna
            if debug:
                print(f"Coluna {column_key} em malha: ",
                      mesh[column_key])

            # Iterate over each row in the GeoDataFrame
            j = 0
            for mesh_index, mesh_row in mesh.iterrows():
                # Access the values of the columns for each row
                objectid_i_mesh = mesh_row['objectid']
                geometry_i_mesh = mesh_row['geometry']
                if (j % 1000) == 0:
                    print(j)
                    # if j > 0:
                    #     break
                j += 1

                # Find all rows in the intersection that have the same objectid
                intersection_rows = intersection.loc[intersection['objectid']
                                                     == objectid_i_mesh]

                quant_rows = len(intersection_rows)
                # Avoid division by zero
                if quant_rows <= 0:
                    continue

                # Variables for weighted average calculation
                sum_values = 0
                sum_areas = 0
                max_value = -1

                for _, intersection_row in intersection_rows.iterrows():
                    ID_j_intersection = intersection_row['ID']
                    objectid_j_intersection = intersection_row['objectid']
                    geometry_j_intersection = intersection_row['geometry']

                    # Find the row in the indicator with the value of this ID
                    indicator_row = indicator.loc[indicator['ID']
                                                  == ID_j_intersection]

                    # Get the area of the intersection
                    intersection_area = geometry_i_mesh.intersection(
                        geometry_j_intersection).area

                    # Get the value of CL_ORIG
                    CL_ORIG = indicator_row['CL_ORIG'].values[0]

                    sum_values += CL_ORIG * intersection_area
                    sum_areas += intersection_area

                    max_value = CL_ORIG if CL_ORIG > max_value else max_value

                # Calculate the weighted average
                weighted_average = sum_values / sum_areas

                # Insert the value of the weighted average into the column of the mesh table
                mesh.at[mesh_index,
                        column_key] = weighted_average if is_average else max_value

            # New row to be added
            new_row = {'file_name': file_name_only, 'column': column_key}

            # Add the new row to the DataFrame
            df_column_relation = df_column_relation.append(
                new_row, ignore_index=True)

            # Save the DataFrame to an Excel file
            df_column_relation.to_excel(column_relation_file_name, index=False)

            # Save the updated mesh
            mesh.to_file(updated_mesh_file_path)

            print("\nUpdated mesh saved to: ", updated_mesh_file_path)
            print("Columns relation file saved to: ", column_relation_file_name)

        except Exception as ex:
            print(f'ERROR: {ex}\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh_file", required=True,
                        help="Path to the mesh file.")
    parser.add_argument("--indicator_files_mask", required=True,
                        help="Path to the indicator files mask. The glob function will be used to find the indicator files.")
    parser.add_argument("--column_relation_file", required=True,
                        help="Path to the columns relation file.")
    parser.add_argument("--new_mesh_file", required=True,
                        help="Path to the new updated mesh file.")
    parser.add_argument("--average", action='store_true',
                        help="Calculate the average of the pixel values within each mesh polygon. If False, take the maximum value.")
    parser.add_argument("--debug", action='store_true',
                        help="Activate debug mode.")
    parser.add_argument("--output_folder", default='output', required=True,
                        help="Path to the directory that will be used to save the generated files.")

    args = parser.parse_args()

    initial_time = time.time()
    main(args)
    final_time = time.time()
    total_time_in_minutes = (final_time - initial_time) / 60
    print(f"Total time: {total_time_in_minutes} minutes")