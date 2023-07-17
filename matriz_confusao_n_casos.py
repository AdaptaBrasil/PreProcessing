# Example: python3 matriz_confusao_n_casos.py --arquivo_malha=malha/ferrovias.shp  --mascara_indicadores=indicadores/*.shp --planilha_indicadores=planilhas/solução_risco_desl_para_matriz.xlsx

import geopandas as gpd
from pyproj import CRS
import pandas as pd
import os
import seaborn as sns
import glob
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import argparse 

DEBUG = True

def carregaMalha(caminho_malha):
    """Carrega a malha a partir de um arquivo shapefile.

    Args:
        caminho_malha (str): Caminho para o arquivo shapefile da malha.

    Returns:
        gpd.GeoDataFrame: O dataframe da malha carregada.
    """
    malha = gpd.read_file(caminho_malha)

    if 'objectid' not in malha.columns:
        malha.columns = ['objectid', *malha.columns[1:]]

    if malha.crs.to_epsg() != 5880:
        print("CRS atual:", malha.crs)
        # Mudar para a CRS EPSG 5880
        malha = malha.to_crs(CRS.from_epsg(5880))  # <- Verificar se o padrão está correto e se vai precisar de ajustes

        malha['geometry'] = malha.geometry.buffer(10, cap_style=2)

        # Imprimir a nova CRS
        print("Nova CRS:", malha.crs)
        # Quantidade de itens na malha
        print("Quantidade de itens na malha: ", len(malha))

    return malha

def verificaPastaOutput():
    """Verifica se a pasta 'output' existe, se não, cria."""
    if not os.path.exists('output'):
        os.makedirs('output')

def funcaoRetornaCaminho(string, lista):
    """Busca uma string em uma lista de strings e retorna o item que contém a string.

    Args:
        string (str): String a ser buscada.
        lista (list): Lista de strings.

    Returns:
        str or None: O item da lista que contém a string, ou None se a string não for encontrada.
    """
    for item in lista:
        if string in item:
            return item
    return None  # Return None if the string is not found in any item

def matrizConfusao(classe_original, classe_ponderada, display_labels: list, indicador: str, arquivo_saida: str):
    """Gera a matriz de confusão e salva uma imagem com o resultado.

    Args:
        classe_original (pd.Series): Série contendo as classes originais.
        classe_ponderada (pd.Series): Série contendo as classes ponderadas.
        display_labels (list): Lista de rótulos para as classes na matriz.
        indicador (str): Nome do indicador usado para a geração da matriz.
        arquivo_saida (str): Caminho do arquivo de saída onde a imagem da matriz será salva.
    """
    cfm = confusion_matrix(classe_original, classe_ponderada, normalize='all', labels=display_labels).round(4) * 100
    f, ax = plt.subplots(1, 1, figsize=(8, 6))
    sns.heatmap(cfm, annot=True, fmt='g', ax=ax)

    # labels, title and ticks
    ax.set_xlabel('Classe Original')
    ax.set_ylabel('Classe Ponderada')
    ax.set_title(f'Matriz de Confusão (%)\n{indicador}')
    ax.xaxis.set_ticklabels(display_labels)
    ax.yaxis.set_ticklabels(display_labels)
    plt.savefig(arquivo_saida)
    ax.remove()
    plt.clf()

def main(args):
    verificaPastaOutput()

    # Arquivos de entrada com os dados dos shapefiles dos indicadores e malha
    caminho_arquivo_malha = args.arquivo_malha
    mascara_arquivos_indicadores = args.mascara_indicadores

    # Arquivos de saída com os dados dos shapefiles dos indicadores e relações
    planilha_indicadores = args.planilha_indicadores

    # Carregar a malha
    malha = carregaMalha(caminho_arquivo_malha)

    lista_indicadores_shp = glob.glob(mascara_arquivos_indicadores, recursive=True)

    df_planilha_indicadores = pd.read_excel(planilha_indicadores)
    if DEBUG:
        print("Cabeça da planilha de indicadores:  ", df_planilha_indicadores.head())

    # Remove the row at index 0 from the dataframe
    df_planilha_indicadores = df_planilha_indicadores.drop(df_planilha_indicadores.index[0])

    # Reorder the index
    df_planilha_indicadores.index = range(len(df_planilha_indicadores))

    # Renomear a primeira coluna para objectid
    df_planilha_indicadores = df_planilha_indicadores.rename(columns={df_planilha_indicadores.columns[0]: 'objectid'})

    # Extract column 0 to create a new dataframe
    df_coluna_objectid = df_planilha_indicadores.iloc[:, [0]].copy()

    # Remova a coluna objectid da planilha de indicadores
    df_planilha_indicadores = df_planilha_indicadores.drop(columns=[df_planilha_indicadores.columns[0]])

    # Andar em cada coluna com for
    for i_coluna, nome_indicador in enumerate(df_planilha_indicadores.columns):
        # Imprimir o nome da coluna
        print(f"\nIniciando o processamento para o indicador {i_coluna}: {nome_indicador}")

        # Verifica se o nome_indicador está contido nas strings da lista de indicadores (lista_indicadores_shp)
        caminho_arquivo_shp = funcaoRetornaCaminho(nome_indicador, lista_indicadores_shp)
        if caminho_arquivo_shp is None:
            print(f"ERRO: indicador {nome_indicador} não encontrado!")
            continue

        # Criar um novo daframe com a coluna objectid e a coluna do indicador
        df_indicador = pd.concat([df_coluna_objectid, df_planilha_indicadores.iloc[:, [i_coluna]]], axis=1)
        
        # Renomear as colunas do df_indicador para objectid valores
        df_indicador.columns = ['objectid', 'valores']

        indicador = gpd.read_file(caminho_arquivo_shp)

        if DEBUG:
            print("CRS atual do indicador:", indicador.crs)

        # Mudar para a CRS EPSG 5880
        indicador = indicador.to_crs(CRS.from_epsg(5880))

        if DEBUG:
            print("Novo CRS do indicador:", indicador.crs)

        # Primeiro junta indicador com a ferrovia, obtendo as geometrias.
        malha_merge = malha.merge(df_indicador, on='objectid', how='inner')
        # Depois, junta indicador+ferrovias com o valor original do indicador.
        intersecao = gpd.sjoin(indicador, malha_merge, how='inner', predicate='intersects')



        # Rotina que gera a matriz de confusão.
        CONFUSION_BINS =   [0, 0.01, 0.25, 0.50, 0.75, 1]
        CONFUSION_LABELS = ['0.00 a 0.01', '0.01 a 0.25', '0.25 a 0.50', '0.50 a 0.75', '0.75 a 1']
        # BUG a partir daqui
        intersecao['label_indicador'] = pd.cut(x=intersecao['CL_N_ORIG'], bins=CONFUSION_BINS,
                                       labels=CONFUSION_LABELS)
        intersecao['label_estimativa'] = pd.cut(x=intersecao['valores'], bins=CONFUSION_BINS,
                                       labels=CONFUSION_LABELS)

        caminho_saida_matriz_indicador_i = f'output/matriz_confusao_indicador_{i_coluna}_{nome_indicador}.png'
        matrizConfusao(intersecao['label_indicador'],
                       intersecao['label_estimativa'],
                       CONFUSION_LABELS,
                       nome_indicador, caminho_saida_matriz_indicador_i)
        del intersecao
        del df_indicador
        del caminho_arquivo_shp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arquivo_malha", required=True, help="Caminho do arquivo de malha")
    parser.add_argument("--mascara_indicadores", required=True, help="Caminho do diretório onde estão as máscaras de arquivos indicadores. Será usado o glob para encontrar os arquivos indicadores")
    parser.add_argument("--planilha_indicadores", required=True, help="Caminho da plainilha com as relações de indicadores por colunas")
    args = parser.parse_args()

    main(args)
