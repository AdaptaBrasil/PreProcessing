# Vetores, matrizes, visualização e manipulação de dados
import pandas as pd

# Ferramentas do GeoPandas e CRS
import geopandas as gpd
from pyproj import CRS

# Bibliotecas úteis do sistema
import os
import glob
from datetime import datetime
import warnings
# Ignorar warnings
warnings.filterwarnings("ignore")

MASCARA_ARQUIVOS_INDICADORES = r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\01_RODOVIA_Adriano\04_BASE_DE_DADOS\**\*.shp"
CAMINHO_ARQUIVO_MALHA =  r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\indicadores_rodovias_malha.shp"
NOME_ARQUIVO_RELACAO_COLUNAS = r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\relacao_arquivos_colunas_malha_rodovias.xlsx"

# Arquivo final gerado de ferrovias
CAMINHO_NOVO_ARQUIVO_MALHA_ATUALIZADO = 'D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\indicadores_rodovias.shp'

DEBUG = False

def carregaMalha():
    malha = gpd.read_file(CAMINHO_ARQUIVO_MALHA)

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
    if 'I_0' in malha.columns:
        lastCol = malha.columns[len(malha.columns)-2]
        nextColId = int(lastCol[2:]) + 1
    else:
        nextColId = 1
    return nextColId, malha

# Encontra a coluna de valor do indicador:
# - Testa nomes "padrão".
# - Encontra a primeira coluna float a pesquisando partir da última coluna para a primeira.
# - Caso exista, testa se os valores da coluna estão entre 0 e 1.
# - Se sim, retorna o nome da coluna, se não retorna erro.
def encontraColunaIndicador(indicador: pd.DataFrame) -> str:
    padroes = ['CL_ORIG', 'CL_N_ORIG', 'N_ORIG']
    for padrao in padroes:
        if padrao in indicador.columns:
            return padrao
    for i, dtype in enumerate(reversed(indicador.dtypes)):
        if dtype == float:
            coltest = indicador.columns[len(indicador.columns)-i-1]
            if len(indicador.query(f'{coltest} >= 0 and {coltest} <= 1.0')) == len(indicador):
                return coltest
    return 'ERRO: coluna de indicador não encontrada!'

if __name__ == "__main__":
    nextColId, malha = carregaMalha()
    if nextColId > 1:
        df_dados_relacao = pd.read_excel(NOME_ARQUIVO_RELACAO_COLUNAS)
    else:
        dados_relacao = {
            'nome_arquivo': [],
            'coluna': []
        }
        df_dados_relacao = pd.DataFrame(dados_relacao)
    print(df_dados_relacao.head())

    arquivos_shp = glob.glob(MASCARA_ARQUIVOS_INDICADORES, recursive=True)

    print("Quantidade de arquivos de volumes encontrados: ", len(arquivos_shp))

    # Imprimir os nomes dos arquivos .shp encontrados
    for i, caminho_arquivo_indicador in enumerate(arquivos_shp):
      try:
          # O nome do arquivo, pois a variavel  contém o caminho inteiro
          nome_arquivo_solo = os.path.basename(caminho_arquivo_indicador).split('.')[0]

          print(f"\nIniciando o processamento do arquivo {nextColId + i}: {caminho_arquivo_indicador} {datetime.now()}")
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
              df_dados_relacao = df_dados_relacao.append(nova_linha, ignore_index=True)
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
          chave_coluna_i = 'I_' + str(i + nextColId)
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
              if DEBUG:
                print(f"\nObjectID: {objectid_i_malha}")
                print("Quantidade de linhas em intersecoes:", quant_linhas)

              # Variáveis para cálculo da média ponderada
              soma_valores = 0
              soma_areas = 0

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

                  # Atualizar as somas
                  if DEBUG:
                    print("area_interseccao: ", area_interseccao)
                  soma_valores += CL_ORIG * area_interseccao
                  soma_areas += area_interseccao

              # Calcular a média ponderada
              media_ponderada = soma_valores / soma_areas
              if DEBUG:
                print(f"Média ponderada para {indice_malha + nextColId}:", media_ponderada)

              # Inserir o valor da média ponderada na coluna valor_indi da tabela malha
              malha.at[indice_malha, chave_coluna_i] = media_ponderada

          # Nova linha a ser adicionada
          nova_linha = {'nome_arquivo': nome_arquivo_solo, 'coluna': chave_coluna_i}

          # Adicionar a nova linha ao DataFrame
          df_dados_relacao = df_dados_relacao.append(nova_linha, ignore_index=True)
          # break

          # Salvar o DataFrame em um arquivo Excel
          df_dados_relacao.to_excel(NOME_ARQUIVO_RELACAO_COLUNAS, index=False)

          # Salvar malha
          malha.to_file(CAMINHO_NOVO_ARQUIVO_MALHA_ATUALIZADO)
      except Exception as ex:
          print(f'ERRO: {ex}\n')
