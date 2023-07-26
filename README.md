# Projeto: Análise Espacial de Indicadores

## Introdução

O Projeto de Análise Espacial de Indicadores é uma iniciativa que visa aprimorar a análise e visualização de dados espaciais, permitindo a junção de indicadores em malhas geoespaciais, geração de matrizes de confusão para N casos e o merge de indicadores raster em malhas. O projeto utiliza ferramentas e bibliotecas Python, como `geopandas`, `pandas`, `pyproj`, `rasterio`, entre outras, para manipulação e processamento de dados tabulares e espaciais.

## Menu

Aqui estão os capítulos disponíveis para explorar neste projeto:

- [Projeto: Análise Espacial de Indicadores](#projeto-análise-espacial-de-indicadores)
  - [Introdução](#introdução)
  - [Menu](#menu)
  - [Merge de Indicadores em Malha](#merge-de-indicadores-em-malha)
    - [Requisitos](#requisitos)
    - [Instalação](#instalação)
    - [Uso](#uso)
  - [Matriz de Confusão para N Casos](#matriz-de-confusão-para-n-casos)
    - [Requisitos](#requisitos-1)
    - [Como usar](#como-usar)
    - [Funcionamento](#funcionamento)
    - [Observações](#observações)
    - [Saída](#saída)
    - [Exemplo de Uso](#exemplo-de-uso)
  - [Merge de Indicadores Rasters em Malha](#merge-de-indicadores-rasters-em-malha)
    - [Requisitos](#requisitos-2)
    - [Instalação](#instalação-1)
    - [Uso](#uso-1)
    - [Saída](#saída-1)
  - [Licença ](#licença-)
  - [Erros Comuns ](#erros-comuns-)
      - [Erro do rtree ](#erro-do-rtree-)
      - [Erro do progress bar ](#erro-do-progress-bar-)

## Merge de Indicadores em Malha

Este repositório contém um script Python chamado `merge_indicadores_malha.py` que realiza a junção de indicadores em uma malha geoespacial. O script utiliza a biblioteca `geopandas` para manipulação de dados espaciais e `pandas` para manipulação de dados tabulares.

### Requisitos

Certifique-se de ter os seguintes requisitos instalados:

- Python 3
- Bibliotecas Python: `pandas`, `geopandas`, `pyproj`

Você pode instalar as bibliotecas necessárias executando o seguinte comando:

```shell
pip install -r requirements.txt
```

Isso irá instalar todas as dependências listadas no arquivo `requirements.txt`.

### Instalação

1. Clone este repositório para o seu ambiente local.
2. Navegue até o diretório do repositório.

### Uso

Execute o script `merge_indicadores_malha.py` passando os argumentos necessários. O script requer os seguintes argumentos:

- `--mascara_indicadores`: Caminho para a máscara de arquivos indicadores. Será usado o `glob` para encontrar os arquivos indicadores.
- `--arquivo_malha`: Caminho do arquivo de malha.
- `--arquivo_relacao`: Caminho do arquivo de relação de colunas.
- `--nova_malha`: Caminho do novo arquivo de malha atualizado.

Aqui está um exemplo de como executar o script:

```shell
python3 merge_indicadores_malha.py --mascara_indicadores=indicadores/*.shp --arquivo_malha=malha/ferrovias.shp --arquivo_relacao=relacao_arquivos_colunas_malha_rodovias.xlsx --nova_malha=indicadores_rodovias.shp
```

Certifique-se de fornecer os caminhos corretos para os arquivos indicadores, arquivo de malha, arquivo de relação de colunas e o novo arquivo de malha atualizado.

## Matriz de Confusão para N Casos

Este código permite gerar a matriz de confusão para N casos, comparando os valores estimados de indicadores espaciais com os valores originais. Ele utiliza arquivos shapefiles que contêm informações espaciais e colunas de valores dos indicadores. Além disso, o código requer uma planilha que relaciona os indicadores às colunas utilizadas na matriz de confusão.

### Requisitos

- Python 3.x
- Bibliotecas: geopandas, pyproj, pandas, os, seaborn, glob, matplotlib, sklearn

### Como usar

Execute o seguinte comando para rodar o script:

```
python3 matriz_confusao_n_casos.py --arquivo_malha=<arquivo_malha> --mascara_indicadores=<mascara_indicadores> --planilha_indicadores=<planilha_indicadores>
```

- `<arquivo_malha>`: Caminho para o arquivo shapefile da malha espacial.
- `<mascara_indicadores>`: Caminho do diretório onde estão as máscaras de arquivos indicadores. O script usará o glob para encontrar os arquivos indicadores.
- `<planilha_indicadores>`: Caminho da planilha que contém as relações de indicadores por colunas.

### Funcionamento

O script carrega a malha espacial a partir do arquivo shapefile especificado. Em seguida, lê os arquivos indicadores (shapefiles) a partir do diretório indicado pela máscara. Ele também lê a planilha que contém as relações entre os indicadores e as colunas utilizadas na matriz de confusão.

Para cada indicador, o script faz o merge com a malha e realiza a interseção para obter os valores originais e estimados. Em seguida, gera a matriz de confusão comparando esses valores. A matriz de confusão é salva como uma imagem no diretório de saída.

### Observações

- O código realiza ajustes no CRS (Coordinate Reference System) da malha para EPSG 5880, se necessário.
- A matriz de confusão é gerada com rótulos específicos (0.00 a 0.01, 0.01 a 0.25, 0.25 a 0.50, 0.50 a 0.75, 0.75 a 1), que podem ser personalizados conforme necessário.
- O script ignora warnings durante a execução.

### Saída

- Imagens da matriz de confusão: Para cada indicador, uma imagem da matriz de confusão é salva no diretório 'output'. Os nomes dos arquivos de saída seguem o padrão `matriz_confusao_indicador_<i>_<nome_indicador>.png`, onde `<i>` é o índice do indicador e `<nome_indicador>` é o nome do indicador usado para a geração da matriz.

### Exemplo de Uso

```
python3 matriz_confusao_n_casos.py --arquivo_malha=malha/ferrovias.shp --mascara_indicadores=indicadores/*.shp --planilha_indicadores=planilhas/solução_risco_desl_para_matriz.xlsx
```

Esse comando realiza a geração da matriz de confusão para os indicadores contidos na pasta `indicadores/`, utilizando o arquivo de malha `malha/ferrovias.shp`. As informações sobre os indicadores e colunas utilizadas são lidas a partir da planilha `solução_risco_desl_para_matriz.xlsx`. As imagens da

 matriz de confusão são salvas no diretório `output/`.

## Merge de Indicadores Rasters em Malha

Este script Python, chamado `merge_rasters_malha.py`, permite a realização do merge de indicadores raster em uma malha geoespacial. O código utiliza bibliotecas como `geopandas`, `rasterio`, `numpy`, `cv2`, `pandas`, entre outras, para manipulação e processamento dos dados espaciais e tabulares.

### Requisitos

Certifique-se de ter os seguintes requisitos instalados:

- Python 3
- Bibliotecas Python: `pandas`, `geopandas`, `pyproj`, `rasterio`

Você pode instalar as bibliotecas necessárias executando o seguinte comando:

```shell
pip install -r requirements.txt
```

Isso irá instalar todas as dependências listadas no arquivo `requirements.txt`.

### Instalação

1. Clone este repositório para o seu ambiente local.
2. Navegue até o diretório do repositório.

### Uso

Execute o script `merge_rasters_malha.py` passando os argumentos necessários. O script requer os seguintes argumentos:

- `--mascara_indicadores`: Caminho para a máscara de arquivos indicadores. Será usado o `glob` para encontrar os arquivos indicadores.
- `--arquivo_malha`: Caminho do arquivo de malha.
- `--arquivo_relacao`: Caminho do arquivo de relação de colunas.
- `--nova_malha`: Caminho do novo arquivo de malha atualizado.
- `--media`: Opção para realizar a média dos valores dos pixels dentro de cada polígono da malha. Se não for fornecida, o valor máximo será considerado.

Aqui está um exemplo de como executar o script:

```shell
python3 merge_rasters_malha.py --mascara_indicadores=rasters/*.tif --arquivo_malha=malha/ferrovias.shp --arquivo_relacao=relacao_arquivos_colunas_malha_rodovias.xlsx --nova_malha=indicadores_rodovias.shp --media
```

Certifique-se de fornecer os caminhos corretos para os arquivos indicadores, arquivo de malha, arquivo de relação de colunas e o novo arquivo de malha atualizado.

### Saída

A saída deste script inclui a criação de um novo arquivo de malha atualizado, contendo as informações dos indicadores raster agregados aos polígonos da malha geoespacial. Além disso, é gerado um arquivo de relação de colunas, no formato Excel, que mostra a correspondência entre o nome dos arquivos indicadores e as colunas associadas na malha. Durante a execução, o script também apresenta informações sobre o progresso do processamento, incluindo o número de polígonos processados e o tempo decorrido. Eventuais erros e exceções são mostrados para facilitar a depuração e o ajuste necessário no processo de mesclagem. Ao final da execução bem-sucedida, uma mensagem indica que a nova malha atualizada e o arquivo de relação de colunas foram salvos nos respectivos caminhos especificados.

## Licença <a name="licenca"></a>

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](./LICENSE) para obter mais informações.

## Erros Comuns <a name="erros-comuns"></a>

Talvez seja necessário instalar algumas dependências no Linux e versões específicas de pacotes:

#### Erro do rtree <a name="erro-do-rtree"></a>
```shell
pip3 uninstall rtree
sudo apt install libspatialindex-dev
pip3 install rtree==1.0.1
```
#### Erro do progress bar <a name="erro-do-progress-bar"></a>
```shell
pip3 install progress progressbar2 alive-progress tqdm
```
