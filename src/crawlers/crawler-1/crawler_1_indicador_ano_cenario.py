import time

import pandas as pd
import requests

REQUEST_TIMEOUT = 60  # seconds


def get_indicator_data(indicator_id, year, scenario):
    
    params = {}
    url = f"https://sistema.adaptabrasil.mcti.gov.br/api/mapa-dados/BR/municipio/{indicator_id}/{year}/{scenario}"
    print(f"Fetching data for indicator in URL: {url}")
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print(f"Request error for indicator {indicator_id}, year {year}, scenario {scenario}: {e}
")
        return None

    if response.ok:
        return response.json()
    else:
        print(f"Failed to fetch data for indicator {indicator_id}, year {year}, scenario {scenario}")
        print("Error URL: ", url,"\n")
        return None


def get_data_for_indicators(indicators):
    data = []

    for indicator in indicators:
        years = [y.strip() for y in str(indicator["years"]).split(",") if y.strip()]

        indicator_id = indicator["indicator_id"]

        for year in years:
            if int(year) < 2023:
                scenario = "null"
                data_for_year = get_indicator_data(indicator_id, year, scenario)
                if data_for_year:
                    data.extend(data_for_year)
            elif year in ["2030", "2050"]:
                for i in range(1, 3):
                    scenario = f"{i}"
                    data_for_year = get_indicator_data(indicator_id, year, scenario)
                    if data_for_year:
                        data.extend(data_for_year)
        print("\n")

    return data


def get_indicators(api_url):
    params = {}

    try:
        response = requests.get(api_url, params=params, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            indicator_data = []

            for item in data:
                if item.get("sep_id") == 6 and (item.get("level") or 0) >= 2:
                    indicator_data.append({
                        "indicator_id": item["id"],
                        "sep_id": item["sep_id"],
                        "level": item["level"],
                        "years": item["years"]
                    })

            return indicator_data
        else:
            print(f"Request failed. Status code: {response.status_code}")
            return None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def save_to_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, columns=[
        "indicator_id", "geocod_ibge", "year", "scenario_id", "value"], index=False)


def main():
    api_url_hierarchy = "https://sistema.adaptabrasil.mcti.gov.br/api/hierarquia"
    data_indicators = get_indicators(api_url_hierarchy)

    if data_indicators is None:
        print("Failed to retrieve indicator data.")
    else:
        print(f"Found {len(data_indicators)} indicators.")
        df_indicators = pd.DataFrame(data_indicators)
        df_indicators.to_csv("data_indicators.csv", index=False)
        print("Indicator data saved to data_indicators.csv.")

        indicator_records = df_indicators.to_dict('records')
        data = get_data_for_indicators(indicator_records)

        if data:
            save_to_csv(data, "final_results.csv")
            print("Data saved to final_results.csv.")

if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print(f"Total time: {end - start} seconds")
