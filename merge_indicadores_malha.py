# Example: python3 merge_indicadores_malha.py --mascara_indicadores=indicadores/*.shp --arquivo_malha=malha/ferrovias.shp --arquivo_relacao=relacao_arquivos_colunas_malha_rodovias.xlsx --nova_malha=indicadores_rodovias.shp

import pandas as pd
import geopandas as gpd
from pyproj import CRS

import openpyxl

# Bibliotecas úteis do sistema
import os
import glob
from datetime import datetime
import argparse

import warnings
# Ignorar warnings
warnings.filterwarnings("ignore")

DEBUG = True

def carregaMalha(caminho_malha):
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
    if 'I_1' in malha.columns:
        lastCol = malha.columns[len(malha.columns)-2]
        nextColId = int(lastCol[2:]) + 1
    else:
        nextColId = 1
    return nextColId, malha

def encontraColunaIndicador(indicador: pd.DataFrame) -> str:
    """
    Encontra a coluna de valor do indicador.

    Esta função realiza as seguintes etapas para encontrar a coluna de valor do indicador:
    1. Testa nomes "padrão" fornecidos na lista de padrões.
    2. Encontra a primeira coluna float ao pesquisar da última coluna para a primeira.
    3. Verifica se os valores da coluna estão entre 0 e 1.
    4. Se os valores estão dentro do intervalo, retorna o nome da coluna.
    5. Caso a coluna não seja encontrada, retorna uma mensagem de erro.

    Parâmetros:
    indicador (pd.DataFrame): O DataFrame contendo os dados do indicador a ser analisado.

    Retorna:
    str: O nome da coluna do indicador que satisfaz as condições, ou uma mensagem de erro caso não seja encontrada.

    Exemplo:
    >>> df = pd.DataFrame({'CL_ORIG': [0.1, 0.5, 0.9], 'CL_DEST': [0.2, 0.6, 0.8]})
    >>> encontraColunaIndicador(df)
    'CL_ORIG'

    >>> df = pd.DataFrame({'CL_ORIGEM': [0.1, 0.5, 0.9], 'CL_DESTINO': [0.2, 0.6, 0.8]})
    >>> encontraColunaIndicador(df)
    'ERRO: coluna de indicador não encontrada!'
    """
    padroes = ['CL_ORIG', 'CL_N_ORIG', 'N_ORIG']
    for padrao in padroes:
        if padrao in indicador.columns:
            return padrao
    for i, dtype in enumerate(reversed(indicador.dtypes)):
        if dtype == float:
            coltest = indicador.columns[len(indicador.columns) - i - 1]
            if len(indicador.query(f'{coltest} >= 0 and {coltest} <= 1.0')) == len(indicador):
                return coltest
    return 'ERRO: coluna de indicador não encontrada!'


# Verifica se a pasta output existe, se não, cria
def verificaPastaOutput():
    if not os.path.exists('output'):
        os.makedirs('output')
def main(args):

    verificaPastaOutput()

    # Arquivos de entrada com os dados dos shapefiles dos indicadores e malha
    mascara_arquivos_indicadores = args.mascara_indicadores
    caminho_arquivo_malha = args.arquivo_malha

    # Arquivos de saída com os dados dos shapefiles dos indicadores e relações
    nome_arquivo_relacao_colunas = args.arquivo_relacao
    caminho_nova_malha_atualizada = args.nova_malha

    # Concatena o nome output/ com o nome do arquivo de saída
    caminho_nova_malha_atualizada = os.path.join('output', caminho_nova_malha_atualizada)
    nome_arquivo_relacao_colunas = os.path.join('output', nome_arquivo_relacao_colunas)

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

    arquivos_shp = glob.glob(mascara_arquivos_indicadores, recursive=True)

    print("Quantidade de arquivos de volumes encontrados: ", len(arquivos_shp))

    # Imprimir os nomes dos arquivos .shp encontrados
    for i, caminho_arquivo_indicador in enumerate(arquivos_shp):
      try:
          # O nome do arquivo, pois a variavel  contém o caminho inteiro
          nome_arquivo_solo = os.path.basename(caminho_arquivo_indicador).split('.')[0]
          ja_processado = df_dados_relacao.loc[df_dados_relacao['nome_arquivo'] == nome_arquivo_solo]
          if len(ja_processado) > 0:
              continue
          print(f"\nIniciando o processamento do arquivo {i}: {caminho_arquivo_indicador} {datetime.now()}")
          indicador = gpd.read_file(caminho_arquivo_indicador)
            # Imprimir a CRS atual
          if DEBUG:
            print("CRS atual:", indicador.crs)

          # Mudar para a CRS EPSG 5880
          indicador = indicador.to_crs(CRS.from_epsg(5880))

          # Adicionar ID caso não exista
          if not('ID' in indicador.columns):
              indicador.insert(0, 'ID', range(1, len(indicador)+1))
          colName = encontraColunaIndicador(indicador)
          if not(colName.startswith('ERRO":')):
              indicador.rename(columns={colName: "CL_ORIG"}, inplace=True)
          else:
              print(colName)
              nova_linha = {'nome_arquivo': nome_arquivo_solo, 'coluna': colName}
              df_dados_relacao = df_dados_relacao._append(nova_linha, ignore_index=True)
              continue

          # Imprimir a nova CRS
          if DEBUG:
            print("Nova CRS:", indicador.crs)

          # Realizar a junção espacial baseada na interseção de geometrias
          intersecao = gpd.sjoin(malha, indicador, how='inner', op='intersects')

          # Criar GeoDataFrame com os campos desejados

          gdf = gpd.GeoDataFrame(intersecao[['ID', 'objectid']], geometry=intersecao.geometry)

          # Salvar o GeoDataFrame em um arquivo shapefile
          # caminho_salvar_interseccao = caminho_arquivo_volume.replace(".shp", "")
          # gdf.to_file(f'{caminho_salvar_interseccao}_intersecao.shp')

          # Quantidade de malha
          if DEBUG:
            print(f"Quantidade de volumes para {i}: ", len(indicador))
            print(f"Quantidade de intersecoes para {i}: ", len(intersecao))

          # Chave para a coluna
          chave_coluna_i = 'I_' + str(i)
          # Criar a nova coluna "I_i" e atribuir um valor float
          malha[chave_coluna_i] = -1.0  # Por exemplo, atribuir o valor 10 a todos os registros

          # Exibir o GeoDataFrame com a nova coluna
          if DEBUG:
            print(f"Coluna {chave_coluna_i} em malha: ", malha[chave_coluna_i])
          # Percorrer cada linha do GeoDataFrame
          j = 0
          for indice_malha, linha_i_malha in malha.iterrows():
              # Acessar os valores das colunas para cada linha
              objectid_i_malha = linha_i_malha['objectid']
              geometry_i_fmalha = linha_i_malha['geometry']
              if (j % 1000) == 0:
                  print(j)
                  # if j > 0:
                  #     break
              j+=1
              # Buscar todas as linhas em intersecoes que têm o mesmo objectid
              linhas_intersecoes = intersecao.loc[intersecao['objectid'] == objectid_i_malha]

              quant_linhas = len(linhas_intersecoes)
              # Evita divisão por zero
              if quant_linhas <= 0:
                continue

              # Imprimir as linhas encontradas
              # if DEBUG:
              #   print(f"\nObjectID: {objectid_i_malha}")
              #   print("Quantidade de linhas em intersecoes:", quant_linhas)

              # Variáveis para cálculo da média ponderada
              soma_valores = 0
              soma_areas = 0
              max_valor = -1

              for _, linha_j_intersecao in linhas_intersecoes.iterrows():
                  ID_j_intersecao = linha_j_intersecao['ID']
                  objectid_j_intersecao = linha_j_intersecao['objectid']
                  geometry_j_intersecacao = linha_j_intersecao['geometry']

                  # Buscar a linha em volumes com o valor desse ID
                  linha_volume = indicador.loc[indicador['ID'] == ID_j_intersecao]

                  # Obter a área da interseção
                  area_interseccao = geometry_i_fmalha.intersection(geometry_j_intersecacao).area

                  # Obter o valor de CL_ORIG
                  CL_ORIG = linha_volume['CL_ORIG'].values[0]

                  soma_valores += CL_ORIG * area_interseccao
                  soma_areas += area_interseccao

                  max_valor = CL_ORIG if CL_ORIG > max_valor else max_valor

              # Calcular a média ponderada
              media_ponderada = soma_valores / soma_areas
              # Inserir o valor da média ponderada na coluna valor_indi da tabela malha
              malha.at[indice_malha, chave_coluna_i] = media_ponderada if args.media else max_valor
              # if DEBUG:
              #   print(f"Valores para {indice_malha + nextColId}: Média: {media_ponderada} Máxima: {max_valor}")


          # Nova linha a ser adicionada
          nova_linha = {'nome_arquivo': nome_arquivo_solo, 'coluna': chave_coluna_i}

          # Adicionar a nova linha ao DataFrame
          df_dados_relacao = df_dados_relacao._append(nova_linha, ignore_index=True)
          # break

          # Salvar o DataFrame em um arquivo Excel
          df_dados_relacao.to_excel(nome_arquivo_relacao_colunas, index=False)

          # Salvar malha
          malha.to_file(caminho_nova_malha_atualizada)

          print("\nNova malha atualizada salva em: ", caminho_nova_malha_atualizada)
          print("Arquivo relacao colunas salvo em: ", nome_arquivo_relacao_colunas)
      except Exception as ex:
          print(f'ERRO: {ex}\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mascara_indicadores", required=True, help="Caminho da máscara de arquivos indicadores. Será usado o glob para encontrar os arquivos indicadores")
    parser.add_argument("--arquivo_malha", required=True, help="Caminho do arquivo de malha")
    parser.add_argument("--arquivo_relacao", required=True, help="Caminho do arquivo de relação de colunas")
    parser.add_argument("--nova_malha", required=True, help="Caminho do novo arquivo de malha atualizado")
    parser.add_argument("--media", required=True, help="Calcular pelo valor máximo, não pela média.",
                        type=bool,
                        action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    main(args)