#!/usr/bin/env python
# coding: utf-8

# Example: python3 reproject_shapefiles.py --input_mask=local_data/indicadores/*.shp --target_epsg=4326 --suffix=_shpreprojected --output_dir=output/new_shapefiles

import os
import argparse
import geopandas as gpd
from tqdm import tqdm
import glob
import time

def reproject_shapefiles(input_mask, target_epsg, suffix, output_dir=None):
    if output_dir is None:
        output_dir = os.path.dirname(input_mask)
    else:
        os.makedirs(output_dir, exist_ok=True)

    shapefiles = [f for f in glob.glob(input_mask, recursive=True) if f.lower().endswith('.shp')]

    for shapefile in tqdm(shapefiles, desc="Reprojecting shapefiles"):
        gdf = gpd.read_file(shapefile)
        # Check if the shapefile is already in the desired EPSG
        if gdf.crs.to_epsg() == target_epsg:
            print("Already in the desired EPSG. Skipping...")
            reprojected_gdf = gdf
        else:
            print("Not in the desired EPSG. Reprojecting...")
            print(f"Reprojecting {shapefile}. Old EPSG: {gdf.crs.to_epsg()}. New EPSG: {target_epsg}")
            reprojected_gdf = gdf.to_crs(epsg=target_epsg)

        filename, ext = os.path.splitext(os.path.basename(shapefile))
        new_filename = f"{filename}_{suffix}{ext}" if suffix else f"{filename}{ext}"
        print(f"\nSaving reprojected shapefile to {new_filename}")

        output_path = os.path.join(output_dir, new_filename)
        reprojected_gdf.to_file(output_path)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input_mask", required=True,
                        help="File mask to search for shapefiles (including subdirectories).")
    parser.add_argument("--target_epsg", type=int, required=True,
                        help="Target EPSG code for reprojection.")
    parser.add_argument("--suffix", required=False,
                        help="Suffix to be added to the output shapefile names.")
    parser.add_argument("--output_dir", required=False,
                        help="Output directory for the reprojected shapefiles.")

    args = parser.parse_args()

    reproject_shapefiles(args.input_mask, args.target_epsg, args.suffix, args.output_dir)

if __name__ == "__main__":
    start_time = time.time()
    main()
    final_time = time.time()
    total_time = (final_time - start_time) / 60
    print(f"Total time: {total_time} minutes")
