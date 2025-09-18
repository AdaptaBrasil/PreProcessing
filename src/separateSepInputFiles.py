import os
import shutil
import pandas as pd
import numpy as np

input_file_path = r"D:\Atrium\Projects\AdaptaBrasil\Data\DADOS_2024_02_19_Adapta"
indicadores_fname = r"descricao.csv"
composicoes_fname = r"composicao.csv"
valores_fname = r"valores.csv"
proporcionalidades_fname = r"proporcionalidades.csv"
setores_fname = r"setores.csv"
output_path = "D:\Atrium\Projects\AdaptaBrasil\Data\DADOS_2024_02_19_Adapta"

def separateIndicators(indicadores, setores_id):
    try:
        for row in setores_id:
            indicadores_sep = indicadores.loc[indicadores['sep'] == row[0]]
            dir = rf"{output_path}\{setores.loc[setores['id'] == row[0]].iloc[0]['nome']}"
            shutil.rmtree(dir, ignore_errors=True)
            os.makedirs(dir)
            indicadores_sep.to_csv(rf"{dir}\{indicadores_fname}", encoding='cp1252',sep='|', na_rep='')
    except Exception as e:
        print(e)
        raise(e)

def separateIndicatorsIndicators(indicadores, setores_id):
    composicoes = pd.read_csv(rf"{input_file_path}\{composicoes_fname}", sep='|', low_memory=False)
    try:
        for row in setores_id:
            composicoes_sep = composicoes.copy()
            composicoes_sep.drop(list(composicoes_sep.filter(regex='Unnamed')), axis=1, inplace=True)
            indicadores_sep = indicadores.loc[indicadores['sep'] == row[0]]['id']
            composicoes_sep = pd.merge(composicoes_sep, indicadores_sep, left_on='Indicador pai', right_on='id')
            dir = rf"{output_path}\{setores.loc[setores['id'] == row[0]].iloc[0]['nome']}"
            composicoes_sep.to_csv(rf"{dir}\{composicoes_fname}", encoding='Latin-1', sep='|', na_rep='', columns=composicoes_sep.columns[:2])
    except Exception as e:
        print(e)
        raise(e)


def separateValues(indicadores, setores_id):
    valores = pd.read_csv(rf"{input_file_path}\{valores_fname}", sep='|', low_memory=False)
    try:
        for row in setores_id:
            valores_sep = valores.copy()
            indicadores_sep = indicadores.loc[indicadores['sep'] == row[0]]['id']
            col_index = 3
            for column in valores_sep.columns[3:]:
                val_id = int(column[0:column.index('-')])
                if val_id not in indicadores_sep.values:
                    valores_sep.drop(valores_sep.columns[col_index], axis=1, inplace=True)
                else:
                    col_index += 1
            dir = rf"{output_path}\{setores.loc[setores['id'] == row[0]].iloc[0]['nome']}"
            # shutil.rmtree(dir, ignore_errors=True)
            # os.makedirs(dir)
            valores_sep.to_csv(rf"{dir}\{valores_fname}", encoding='Latin-1',sep='|', na_rep='')
    except Exception as e:
        print(e)
        raise(e)

def separateProporcionalidades(indicadores, setores_id):
    proporcionalidades = pd.read_csv(rf"{input_file_path}\{proporcionalidades_fname}", sep='|', low_memory=False)
#    header_proporcionalidades = pd.read_csv(rf"{input_file_path}\{proporcionalidades_fname}", sep='|', header=None, nrows=1)
    try:
        for row in setores_id:
            proporcionalidades_sep = proporcionalidades.copy()
            indicadores_sep = indicadores.loc[indicadores['sep'] == row[0]]['id']
            col_index = 3
            while col_index < len(proporcionalidades_sep.columns):
                column = proporcionalidades_sep.iloc[0][col_index]
                if len(column) == 0:
                    break
                val_id = int(column[0:column.index('-')])
                if val_id not in indicadores_sep.values:
                    proporcionalidades_sep.drop(proporcionalidades_sep.columns[col_index], axis=1, inplace=True)
                else:
                    col_index += 1
            dir = rf"{output_path}\{setores.loc[setores['id'] == row[0]].iloc[0]['nome']}"
            # shutil.rmtree(dir, ignore_errors=True)
            # os.makedirs(dir)
            proporcionalidades_sep.columns = ['' if c.startswith('Unnamed') else c for c in
                                              proporcionalidades_sep.columns]
            proporcionalidades_sep.to_csv(rf"{dir}\{proporcionalidades_fname}", encoding='Latin-1',sep='|', na_rep='')
    except Exception as e:
        print(e)
        raise(e)

if __name__ == "__main__":
    indicadores = pd.read_csv(rf"{input_file_path}\{indicadores_fname}", sep='|', low_memory=False)
    indicadores.drop(list(indicadores.filter(regex='Unnamed')), axis=1, inplace=True)
    setores = pd.read_csv(rf"{input_file_path}\{setores_fname}", sep='|', low_memory=False)
    setores_id = np.unique(indicadores[['sep']], axis=0)
    # separateIndicators(indicadores, setores_id)
    separateIndicatorsIndicators(indicadores, setores_id)
    separateValues(indicadores, setores_id)
    # separateProporcionalidades(indicadores, setores_id)
    pass


