from sqlalchemy import create_engine
from glob import glob
import geopandas as gpd
import pandas as pd
import os
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pyproj import CRS
from sklearn.metrics import confusion_matrix

# Ignorar warnings
import warnings
warnings.filterwarnings("ignore")

MASCARA_ARQUIVOS_INDICADORES = r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\02_FERROVIAS_Adriano\04_BASE_DE_DADOS\**\*.shp"
CAMINHO_ARQUIVO_MALHA =  r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\indicadores_ferrovias.shp"
NOME_ARQUIVO_RELACAO_COLUNAS = r"D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\relacao_arquivos_colunas_malha_ferrovias.xlsx"
PATH_IMAGENS_HISTOGRAMA = r'D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\imagens\ferrovias\histogramas'
PATH_IMAGENS_MATRIZ_CONFUSAO = r'D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\imagens\FERROVIAS\matrizes_confusao'

#CAMINHO_NOVO_ARQUIVO_MALHA_ATUALIZADO = 'D:\Atrium\Projects\AdaptaBrasil\Data\Adaptavias\indicadores_rodovias.shp'

"""
	when cl_n_orig_media_classe <= 0.01 then '0.00 a 0.01'
	when cl_n_orig_media_classe > 0.01 and cl_n_orig_media_classe <= 0.25 then '0.01 a 0.25'
	when cl_n_orig_media_classe > 0.25 and cl_n_orig_media_classe <= 0.50 then '0.25 a 0.50'
	when cl_n_orig_media_classe > 0.50 and cl_n_orig_media_classe <= 0.75 then '0.50 a 0.75'
	when cl_n_orig_media_classe > 0.75 then '0.75 a 1'
"""

CONFUSION_BINS =   [0, 0.01, 0.25, 0.50, 0.75, 1]
CONFUSION_LABELS = ['0.00 a 0.01', '0.01 a 0.25', '0.25 a 0.50', '0.50 a 0.75', '0.75 a 1']

from matplotlib.ticker import PercentFormatter

def histogram(data: list, title: str):

    # def to_percent(y, n):
    #     s = str(round(100 * y / n, 1))
    #
    #     if matplotlib.rcParams['text.usetex']:
    #         return s + r'$\%$'
    #
    #     return s + '%'

    def plotting_hist(data: list, title: str):
        f, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(label=title+'\n')

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
        plt.savefig(fr"{PATH_IMAGENS_HISTOGRAMA}\{title}.png")

    plotting_hist(data, title)
    plt.clf()

def matrizConfusao(classe_original, classe_ponderada, display_labels: list, indicador: str):
    cfm=confusion_matrix(classe_original, classe_ponderada, normalize='all', labels=display_labels).round(4)*100
    f, ax = plt.subplots(1, 1, figsize=(8, 6))
    sns.heatmap(cfm, annot=True, fmt='g', ax=ax) #annot=True to annotate cells, ftm='g' to disable scientific notation

    # labels, title and ticks
    ax.set_xlabel('Classe Original')
    ax.set_ylabel('Classe Ponderada')
    ax.set_title(f'Matriz de Confusão (%)\n{indicador}')
    ax.xaxis.set_ticklabels(display_labels)
    ax.yaxis.set_ticklabels(display_labels)
    plt.savefig(fr"{PATH_IMAGENS_MATRIZ_CONFUSAO}\{indicador}.png")
    ax.remove()
    plt.clf()

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
    display_labels_matriz_confusao=['0.00 a 0.01','0.01 a 0.25','0.25 a 0.50','0.50 a 0.75','0.75 a 1.00']
    arquivos_indicadores = glob(MASCARA_ARQUIVOS_INDICADORES, recursive=True)
    indicadores_malha = gpd.read_file(CAMINHO_ARQUIVO_MALHA)
    relacao_indicadores = pd.read_excel(NOME_ARQUIVO_RELACAO_COLUNAS)
    for i,fname_indicador in enumerate(arquivos_indicadores):


        fname_indicador = arquivos_indicadores[i]

        print(f"Arquivo {i}/{len(arquivos_indicadores)}: {fname_indicador}")
        try:
            indicador = gpd.read_file(fname_indicador)
            indicador = indicador.to_crs(CRS.from_epsg(5880))
            nome_arquivo_solo = os.path.basename(fname_indicador).split('.')[0]
            coluna_malha = (relacao_indicadores.query(f"nome_arquivo == '{nome_arquivo_solo}'")['coluna']).values[0]
            coluna_indicador = encontraColunaIndicador(indicador)
            intersecao = gpd.sjoin(indicadores_malha, indicador, how='inner', op='intersects')
            # df['Label'] = pd.cut(x=df['Age'], bins=[0, 3, 17, 63, 99],
            #                      labels=['Baby/Toddler', 'Child', 'Adult',
            #                              'Elderly'])
            intersecao['label_indicador'] = pd.cut(x=intersecao[coluna_indicador], bins=CONFUSION_BINS,
                                                   labels=CONFUSION_LABELS)
            intersecao['label_malha'] = pd.cut(x=intersecao[coluna_malha], bins=CONFUSION_BINS,
                                                   labels=CONFUSION_LABELS)
            intersecao = intersecao.dropna(subset=['label_indicador', 'label_malha'])
            intersecao['label_indicador'] = intersecao['label_indicador'].values.astype('string')
            intersecao['label_malha'] = intersecao['label_malha'].values.astype('string')
            matrizConfusao(intersecao['label_indicador'],
                           intersecao['label_malha'],
                           CONFUSION_LABELS,
                           nome_arquivo_solo)
            # intersecao['diff'] = intersecao[coluna_indicador] - intersecao[coluna_malha]
            # histogram(intersecao['diff'].to_list(), nome_arquivo_solo)
        except Exception as ex:
            print(f'ERRO: {ex}\n')
