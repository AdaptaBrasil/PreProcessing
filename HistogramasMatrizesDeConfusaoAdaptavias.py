from sqlalchemy import create_engine
from glob import glob
import geopandas as gpd
import pandas as pd
import os
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

MASCARA_ARQUIVOS_INDICADORES = r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\01_RODOVIA_Adriano\04_BASE_DE_DADOS\**\*.shp"
CAMINHO_ARQUIVO_MALHA =  r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\indicadores_rodovias_malha.shp"
NOME_ARQUIVO_RELACAO_COLUNAS = r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\relacao_arquivos_colunas_malha_rodovias.xlsx"
PATH_IMAGENS = 'D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\imagens'
#CAMINHO_NOVO_ARQUIVO_MALHA_ATUALIZADO = 'D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\indicadores_rodovias.shp'

from matplotlib.ticker import PercentFormatter

def histogram(df: pd.DataFrame, title: str):

    # def to_percent(y, n):
    #     s = str(round(100 * y / n, 1))
    #
    #     if matplotlib.rcParams['text.usetex']:
    #         return s + r'$\%$'
    #
    #     return s + '%'

    def plotting_hist(data, title):
        f, ax = plt.subplots(figsize=(5, 5))
        ax.set_title(label=title)

        values, bins, bars = ax.hist(data,
                bins=10, weights=np.ones(len(data)) / len(data))
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        ax.set_ylim([0, 1])
        ax.set_xlim([-1, 1])

        rects = ax.patches
        labels = []
        for value in bars.datavalues:
            labels.append(f"{value/len(data)*100:.1f}" if abs(value/len(data)) > 0.10 else "")
        for rect, label in zip(rects, labels):
            height = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2, height + 5, label, ha="center", va="bottom",
                size=6, fontdict=None
            )
            plt.savefig(fr"{PATH_IMAGENS}\{title}.png")

    data = df.diff.to_list()
    plotting_hist(data, title)
    plt.clf()

def encontraColunaIndicador(indicador: pd.DataFrame) -> str:
    for i, dtype in enumerate(reversed(indicador.dtypes)):
        if dtype == float:
            coltest = indicador.columns[len(indicador.columns)-i-1]
            if len(indicador.query(f'{coltest} >= 0 and {coltest} <= 1.0')) == len(indicador):
                return coltest
    return 'ERRO: coluna de indicador não encontrada!'

if __name__ == "__main__":
    arquivos_indicadores = glob.glob(MASCARA_ARQUIVOS_INDICADORES, recursive=True)
    indicadores_malha = gpd.read_file(CAMINHO_ARQUIVO_MALHA)
    relacao_indicadores = pd.DataFrame(NOME_ARQUIVO_RELACAO_COLUNAS)
    for indicador in arquivos_indicadores:
        indicadores_malha = gpd.read_file(indicador)
        intersecao = gpd.sjoin(indicadores_malha, indicador, how='inner', op='intersects')
        intersecao['diff'] = intersecao['']
