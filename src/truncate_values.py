#!/usr/bin/env python
# coding: utf-8

"""
Truncate float values in Excel file to specified decimal places without rounding.

Example:
python3 src/truncate_values.py --input_file valores.xlsx --decimal_places 2
"""

import argparse
import pandas as pd
import numpy as np
import math
import os


def truncate_float(value, decimal_places):
    """
    Truncate a float value to specified decimal places without rounding.
    
    Args:
        value: The float value to truncate
        decimal_places: Number of decimal places to keep
        
    Returns:
        Truncated float value
    """
    multiplier = 10 ** decimal_places
    return math.floor(value * multiplier) / multiplier


def process_cell_value(value, decimal_places):
    """
    Process a single cell value according to the rules:
    - Float values: truncate to decimal_places without rounding
    - 'DI' values: keep as is
    - Non-numeric values (except 'DI'): raise error
    
    Args:
        value: Cell value to process
        decimal_places: Number of decimal places for truncation
        
    Returns:
        Processed value
        
    Raises:
        ValueError: If value is non-numeric and not 'DI'
    """
    # Handle NaN values
    if pd.isna(value):
        return value
    
    # Handle 'DI' values (case insensitive)
    if isinstance(value, str) and value.upper() == 'DI':
        return value
    
    # Handle numeric values (including numpy types)
    if isinstance(value, (int, float, np.integer, np.floating)):
        # Convert numpy types to native Python types
        if isinstance(value, (np.integer, np.floating)):
            value = value.item()
        
        # If it's an integer, return as is
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return int(value)
        # If it's a float, truncate
        return truncate_float(value, decimal_places)
    
    # Handle string representations of numbers
    if isinstance(value, str):
        try:
            # Try to convert to float
            float_value = float(value)
            if float_value.is_integer():
                return int(float_value)
            return truncate_float(float_value, decimal_places)
        except ValueError:
            # If conversion fails and it's not 'DI', raise error
            raise ValueError(f"Non-numeric value found: '{value}'. Only numeric values and 'DI' are allowed.")
    
    # For any other type, raise error
    raise ValueError(f"Unsupported value type: {type(value)} with value '{value}'. Only numeric values and 'DI' are allowed.")


def main():
    parser = argparse.ArgumentParser(description="Truncate float values in Excel file to specified decimal places without rounding.")
    
    parser.add_argument("--input_file", required=True,
                        help="Path to the input Excel file (valores.xlsx)")
    parser.add_argument("--decimal_places", type=int, default=2,
                        help="Number of decimal places to truncate to (default: 2)")
    parser.add_argument("--output_file", 
                        help="Path to output file (default: valores_truncados.xlsx in same directory as input)")
    
    args = parser.parse_args()
    
    input_file = args.input_file
    decimal_places = args.decimal_places
    
    # Generate output filename if not provided
    if args.output_file:
        output_file = args.output_file
    else:
        input_dir = os.path.dirname(input_file)
        output_file = os.path.join(input_dir, "valores_truncados.xlsx")
    
    print(f"Reading input file: {input_file}")
    print(f"Decimal places: {decimal_places}")
    print(f"Output file: {output_file}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(input_file, engine='openpyxl')
        
        print(f"Original dataframe shape: {df.shape}")
        print("Processing values...")
        
        # Create a copy to avoid modifying original during iteration
        df_truncated = df.copy()
        
        # Process each cell in the dataframe (skip 'id' column)
        for col in df_truncated.columns:
            if col.lower() == 'id':
                print(f"Skipping column: {col} (ID column)")
                continue
                
            print(f"Processing column: {col}")
            for idx in df_truncated.index:
                original_value = df_truncated.loc[idx, col]
                try:
                    processed_value = process_cell_value(original_value, decimal_places)
                    df_truncated.loc[idx, col] = processed_value
                except ValueError as e:
                    print(f"Error in column '{col}', row {idx}: {e}")
                    raise
        
        # Save the processed dataframe
        df_truncated.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"Successfully saved truncated values to: {output_file}")
        print(f"Processed {df.shape[0]} rows and {df.shape[1]} columns")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return 1
    except Exception as e:
        print(f"Error processing file: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
