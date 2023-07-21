#!/usr/bin/env python
# coding: utf-8
# Example: python3 merge_rasters_malha.py --mascara_indicadores=rasters/*.tif --arquivo_malha=malha/ferrovias.shp --arquivo_relacao=relacao_arquivos_colunas_malha_rodovias.xlsx --nova_malha=indicadores_rodovias.shp --media

# Bibliotecas de processamento de dados geoespaciais
import rasterio as rio
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import MultiPolygon, Polygon

# Bibliotecas de processamento numérico
import numpy as np
import cv2

# Bibliotecas de manipulação de dados
import pandas as pd

# Bibliotecas úteis do sistema
import os
import glob
from datetime import datetime
import argparse
import time
import traceback

# Bibliotecas de úteis
from progress.bar import Bar


# Ignorar warnings
import warnings
warnings.filterwarnings("ignore")


DEBUG = True

DEFAULT_CRS = 5880


def carregaMalha(caminho_malha):
    malha = gpd.read_file(caminho_malha)

    if 'objectid' not in malha.columns:
        malha.columns = ['objectid', *malha.columns[1:]]

    if malha.crs.to_epsg() != DEFAULT_CRS:
        print("CRS atual:", malha.crs)
        # Mudar para a CRS EPSG DEFAULT_CRS
        malha = malha.to_crs(CRS.from_epsg(DEFAULT_CRS))  # <- Verificar se o padrão está correto e se vai precisar de ajustes

        # malha['geometry'] = malha.geometry.buffer(10, cap_style=2)

        # Imprimir a nova CRS
        print("Nova CRS:", malha.crs)
        # Quantidade de itens na malha
        print("Quantidade de itens na malha: ", len(malha))
    if 'I_1' in malha.columns:
        lastCol = malha.columns[len(malha.columns)-2]
        nextColId = int(lastCol[2:]) + 1
    else:
        nextColId = 1
    return nextColId, malha

# Verifica se a pasta output existe, se não, cria
def verificaPastaOutput():
    if not os.path.exists('output'):
        os.makedirs('output')
    if not os.path.exists('temp'):
        os.makedirs('temp')

def convert_multi_to_single_polygon(geometry):
    if isinstance(geometry, MultiPolygon):
        # Se for um MultiPolygon, combine todos os polígonos em um único polígono
        return Polygon([p for polygon in geometry for p in polygon.exterior.coords])
    # Caso contrário, retorne a geometria original
    return geometry

def main(args):

    verificaPastaOutput()

    # Coletanto todos os argumentos passados
    mascara_arquivos_indicadores = args.mascara_indicadores
    caminho_arquivo_malha = args.arquivo_malha
    nome_arquivo_relacao_colunas = args.arquivo_relacao
    caminho_nova_malha_atualizada = args.nova_malha
    is_media = args.media
    
    if DEBUG:
        print("Argumentos passados:")
        print("Máscara de arquivos indicadores: ", mascara_arquivos_indicadores)
        print("Arquivo de malha: ", caminho_arquivo_malha)
        print("Arquivo de relação de colunas: ", nome_arquivo_relacao_colunas)
        print("Arquivo de malha atualizada: ", caminho_nova_malha_atualizada)
        print("Média: ", is_media, "\n")


    # Concatena o nome output/ com o nome do arquivo de saída
    caminho_nova_malha_atualizada = os.path.join(
        'output', caminho_nova_malha_atualizada)
    nome_arquivo_relacao_colunas = os.path.join(
        'output', nome_arquivo_relacao_colunas)

    nextColId, malha = carregaMalha(caminho_arquivo_malha)

    if nextColId > 1:
        df_dados_relacao = pd.read_excel(nome_arquivo_relacao_colunas)
    else:
        dados_relacao = {
            'nome_arquivo': [],
            'coluna': []
        }
        df_dados_relacao = pd.DataFrame(dados_relacao)
    print(df_dados_relacao.head())

    arquivos_tif = glob.glob(mascara_arquivos_indicadores, recursive=True)

    print("Quantidade de arquivos de volumes encontrados: ", len(arquivos_tif))

    
    # Imprimir os nomes dos arquivos .shp encontrados
    for i, caminho_arquivo_indicador in enumerate(arquivos_tif):
        try:
            # O nome do arquivo, pois a variavel  contém o caminho inteiro
            nome_arquivo_solo = os.path.basename(
                caminho_arquivo_indicador).split('.')[0]

            print(
                f"\nIniciando o processamento do arquivo {nextColId + i}: {caminho_arquivo_indicador} {datetime.now()}")

            indicador = rio.open(caminho_arquivo_indicador)
            pixel_values = indicador.read(1)

            crs_inteiro_indicador = int(indicador.crs.to_epsg())

            # Imprimir a CRS atual
            if DEBUG:
                print("CRS atual do indicador:", crs_inteiro_indicador)

            malha = malha.to_crs(crs_inteiro_indicador)
            # malha['geometry'] = malha.geometry.buffer(10, cap_style=2)
            
            # Imprimir a CRS atual da malha
            if DEBUG:
                print("CRS atual da malha:", malha.crs)

            if DEBUG:
                print(f"Shape do indicador {i}: {pixel_values.shape}")

            
            # Chave para a coluna
            chave_coluna_i = 'I_' + str(i)
            # Criar a nova coluna "I_i" e atribuir um valor float
            malha[chave_coluna_i] = -1.0  # Por exemplo, atribuir o valor -1 a todos os registros

            # Exibir o GeoDataFrame com a nova coluna
            if DEBUG:
                print(f"Coluna {chave_coluna_i} em malha: ", malha[chave_coluna_i])
            
            # Transformar tudo em Polygons
            # malha = malha.explode(ignore_index=True)

            # Trazer os valores em graus para o plano cartesiano
            min_lat,max_lon,max_lat,min_lon = indicador.bounds

            min_x, min_y = indicador.index(min_lat, min_lon)
            max_x, max_y = indicador.index(max_lat, max_lon)
            width, height = int(max_x-min_x), int(max_y-min_y)

            numero_polygonos = len(malha.geometry)
            # Criar um indicador de progresso com o numero de poligonos e mostrar o tempo que se passou ao lado do valor

            with Bar(f'Processando {numero_polygonos} polígonos do indicador {i}', max=numero_polygonos) as bar:
                for idx, geometry in enumerate(malha.geometry):                
                    # Verifica se é um MultiPolygon
                    geometry = convert_multi_to_single_polygon(geometry)
                    
                    polygons = np.zeros((width, height), dtype=np.uint8)
                    pts = np.array([indicador.index(point[0], point[1]) for point in geometry.exterior.coords[:]], np.int32)[:, ::-1]
                    pts = pts - np.array([min_y, min_x])
                    
                    cv2.fillPoly(polygons, [pts], 1) #mask
                    
                    x, y = np.where(polygons == 1)
                    values = pixel_values[x, y]
                    # Remover todos os valores negativos da lista de valores
                    values = values[values >= 0]
                    
                    # Verifica se a lista de valores não está vazia
                    if len(values) > 0:
                        maximo_valor = np.nanmax(values)
                        # Realizar os cálculos
                        media_aritmetica = np.mean(values)
                    else:
                        # Define um valor padrão para maximo_valor quando a lista está vazia (por exemplo, -1)
                        maximo_valor = -1.0
                        # Define um valor padrão para media_aritmetica quando a lista está vazia (por exemplo, -1)
                        media_aritmetica = -1.0

                    # Inserir o valor da média ou do máximo na coluna
                    malha.at[idx, chave_coluna_i] = media_aritmetica if args.media else maximo_valor
                    
                    # Atualizar a barra de progresso
                    bar.next()
                    
                    # if DEBUG:
                        # print(f"Valores dos pixels para o polígono {idx}: {values}. Média: {media_aritmetica} Valor máximo: {maximo_valor}")
                
                # Nova linha a ser adicionada
                nova_linha = {'nome_arquivo': nome_arquivo_solo, 'coluna': chave_coluna_i}

                # Adicionar a nova linha ao DataFrame
                df_dados_relacao = df_dados_relacao._append(nova_linha, ignore_index=True)

                # Salvar o DataFrame em um arquivo Excel
                df_dados_relacao.to_excel(nome_arquivo_relacao_colunas, index=False)

                # Mudar o CRS da malha para o CRS padrão
                malha = malha.to_crs(CRS.from_epsg(DEFAULT_CRS))  # <- Verificar se o padrão está correto e se vai precisar de ajustes

                # Salvar malha
                malha.to_file(caminho_nova_malha_atualizada)

                print("\nNova malha atualizada salva em: ", caminho_nova_malha_atualizada)
                print("Arquivo relacao colunas salvo em: ", nome_arquivo_relacao_colunas)

                # Fechar o indicador
                indicador.close()
            

        except Exception as ex:
            print(f'ERRO: {ex}\n')
            # Imprimir a linha do erro
            print(traceback.format_exc())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--mascara_indicadores", required=True,
                        help="Caminho da máscara de arquivos indicadores. Será usado o glob para encontrar os arquivos indicadores. Exemplo: diretório/*.tif")
    
    parser.add_argument("--arquivo_malha", required=True,
                        help="Caminho do arquivo de malha. Exemplo: malha.shp")
    
    parser.add_argument("--arquivo_relacao", required=True,
                        help="Caminho do arquivo em que será salva a relação de colunas. Exemplo: relacao.xlsx")
    
    parser.add_argument("--nova_malha", required=True,
                        help="Caminho do novo arquivo de malha atualizado. Exemplo: nova_malha_atualizada.shp")
    
    parser.add_argument("--media", required=False, help="Realizar a média dos valores dos pixels dentro de cada polígono da malha. Se False pegar o valor máximo.",
                        # action=argparse.BooleanOptionalAction,
                        # type=bool,
                        action='store_true'
                        )
    args = parser.parse_args()

    main(args)


