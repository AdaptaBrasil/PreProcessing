# Projeto: Análise Espacial de Indicadores

## Introdução

O Projeto de Análise Espacial de Indicadores é uma iniciativa que visa aprimorar a análise e visualização de dados espaciais, permitindo a junção de indicadores em malhas geoespaciais, geração de matrizes de confusão para N casos e o merge de indicadores raster em malhas. O projeto utiliza ferramentas e bibliotecas Python, como `geopandas`, `pandas`, `pyproj`, `rasterio`, entre outras, para manipulação e processamento de dados tabulares e espaciais.

## Menu

Aqui estão os capítulos disponíveis para explorar neste projeto:

- [Projeto: Análise Espacial de Indicadores](#projeto-análise-espacial-de-indicadores)
  - [Introdução](#introdução)
  - [Menu](#menu)
  - [Merge de Indicadores Shapefiles em Malha](#merge-de-indicadores-shapefiles-em-malha)
    - [Requisitos](#requisitos)
    - [Como usar](#como-usar)
    - [Funcionamento](#funcionamento)
    - [Observações](#observações)
    - [Saída](#saída)
    - [Exemplo de Uso](#exemplo-de-uso)
  - [Merge de Indicadores Rasters em Malha](#merge-de-indicadores-rasters-em-malha)
    - [Requisitos](#requisitos-1)
    - [Como usar](#como-usar-1)
    - [Funcionamento](#funcionamento-1)
    - [Observações](#observações-1)
    - [Saída](#saída-1)
    - [Exemplo de Uso](#exemplo-de-uso-1)
  - [Geração de Histogramas e Matrizes de Confusão](#geração-de-histogramas-e-matrizes-de-confusão)
    - [Requisitos](#requisitos-2)
    - [Como usar](#como-usar-2)
    - [Funcionamento](#funcionamento-2)
    - [Observações](#observações-2)
    - [Saída](#saída-2)
    - [Exemplo de Uso](#exemplo-de-uso-2)
  - [Matriz de Confusão para N Casos](#matriz-de-confusão-para-n-casos)
    - [Requisitos](#requisitos-3)
    - [Como usar](#como-usar-3)
    - [Funcionamento](#funcionamento-3)
    - [Observações](#observações-3)
    - [Saída](#saída-3)
    - [Exemplo de Uso](#exemplo-de-uso-3)
  - [Geração de legendas QML para CSV](#geração-de-legendas-qml-para-csv)
    - [Descrição](#descrição)
    - [Requisitos](#requisitos-4)
    - [Como usar](#como-usar-4)
    - [Funcionamento](#funcionamento-4)
    - [Observações](#observações-4)
    - [Saída](#saída-4)
    - [Exemplo de Uso](#exemplo-de-uso-4)
  - [Licença ](#licença-)
  - [Erros Comuns ](#erros-comuns-)
      - [Erro do rtree ](#erro-do-rtree-)
      - [Erro do progress bar ](#erro-do-progress-bar-)

## Merge de Indicadores Shapefiles em Malha

Este script Python, chamado `merge_shapefiles_mesh.py`, permite realizar o merge de indicadores armazenados em arquivos Shapefile com uma malha geoespacial. O script utiliza diversas bibliotecas Python, como `pandas`, `geopandas`, `pyproj`, entre outras, para manipulação e processamento dos dados espaciais e tabulares.

### Requisitos
Certifique-se de ter os seguintes requisitos instalados:

- Python 3
- Bibliotecas Python: `pandas`, `geopandas`, `pyproj`, `glob3`, `progress`

Você pode instalar as bibliotecas necessárias executando o seguinte comando:

```shell
pip install -r requirements.txt
```

### Como usar

Para executar o script, utilize o seguinte comando:

```shell
python3 merge_shapefiles_mesh.py --mesh_file=<mesh_file_path> --mesh_file_pk=<mesh_file_pk> --indicator_files_mask=<indicator_files_mask> --column_relation_file=<column_relation_file_name> --new_mesh_file=<updated_mesh_file_path> --average --debug --output_folder=<output_folder_path>
```

- `--mesh_file`: Caminho para o arquivo Shapefile que contém a malha geoespacial.
- `--mesh_file_pk`: Nome do campo que serve como chave primária (ID) na malha.
- `--indicator_files_mask`: Caminho para a máscara de arquivos dos indicadores. O script usará a função `glob` para encontrar os arquivos indicadores.
- `--column_relation_file`: Caminho para o arquivo que contém a relação entre os nomes dos arquivos indicadores e as colunas associadas na malha.
- `--new_mesh_file`: Caminho para o novo arquivo Shapefile atualizado, que conterá as informações dos indicadores raster agregados aos polígonos da malha geoespacial.
- `--average`: Parâmetro opcional para calcular a média dos valores dos pixels dentro de cada polígono da malha. Se não for fornecido, o valor máximo será considerado.
- `--debug`: Parâmetro opcional para ativar o modo de depuração, exibindo informações adicionais durante a execução.
- `--output_folder`: Caminho para o diretório onde os arquivos de saída serão salvos. O diretório será criado caso não exista.

### Funcionamento

O script realiza o seguinte processo:

1. Carrega a malha geoespacial a partir do arquivo Shapefile especificado.
2. Verifica se existe um arquivo de relação de colunas. Se não existir, cria um novo.
3. Procura e carrega os arquivos dos indicadores (Shapefiles) baseados na máscara fornecida.
4. Itera sobre cada arquivo de indicador, realizando as etapas de pré-processamento e junção (interseção) com a malha.
5. Calcula a média ponderada ou o valor máximo dos indicadores para cada polígono da malha, dependendo do valor do parâmetro `--average`.
6. Atualiza a malha com os novos valores dos indicadores.
7. Salva o novo arquivo da malha atualizado e o arquivo de relação de colunas.

### Observações

- Certifique-se de que o ambiente Python tenha as bibliotecas necessárias instaladas. Caso não tenha, você pode instalar as dependências listadas anteriormente.
- O script suporta apenas arquivos Shapefile (.shp) para a malha e os indicadores.

### Saída

A saída deste script inclui a criação de um novo arquivo Shapefile atualizado, contendo as informações dos indicadores raster agregados aos polígonos da malha geoespacial. Além disso, é gerado um arquivo de relação de colunas, no formato Excel, que mostra a correspondência entre os nomes dos arquivos indicadores e as colunas associadas na malha. Durante a execução, o script também apresenta informações sobre o progresso do processamento, incluindo o número de arquivos de indicadores processados e o tempo decorrido. Eventuais erros e exceções são mostrados para facilitar a depuração e o ajuste necessário no processo de mesclagem.

### Exemplo de Uso

```shell
python3 merge_shapefiles_mesh.py --mesh_file=local_data/malha/ferrovias.shp --mesh_file_pk=object_id --indicator_files_mask=local_data/indicadores/*.shp --column_relation_file=relacao_arquivos_colunas_malha_rodovias.xlsx --new_mesh_file=indicadores_rodovias.shp --average --debug --output_folder=output/result_shapefiles_mesh
```

Neste exemplo, o script será executado com o arquivo Shapefile da malha em `local_data/malha/ferrovias.shp`, usando o campo `object_id` como chave primária na malha. Os arquivos indicadores serão procurados na pasta `local_data/indicadores/`, e as informações sobre os indicadores e as colunas utilizadas serão lidas a partir do arquivo `relacao_arquivos_colunas_malha_rodovias.xlsx`. O novo arquivo Shapefile da malha atualizada será salvo em `output/result_shapefiles_mesh`, com a opção de calcular a média dos valores dos pixels dentro de cada polígono ativada (`--average`). O modo de depuração será ativado para exibir informações adicionais durante a execução (`--debug`).

## Merge de Indicadores Rasters em Malha

Este script Python, denominado `merge_rasters_mesh.py`, permite realizar o merge de indicadores armazenados em arquivos Raster com uma malha geoespacial. O script utiliza bibliotecas Python como `rasterio`, `numpy`, `pandas`, `cv2` (OpenCV), entre outras, para processar dados espaciais e tabulares.

### Requisitos
Certifique-se de ter os seguintes requisitos instalados:

- Python 3
- Bibliotecas Python: `rasterio`, `numpy`, `pandas`, `opencv-python-headless`, `progress`, `pyproj`

Você pode instalar as bibliotecas necessárias executando o seguinte comando:

```shell
pip install -r requirements.txt
```

### Como usar

Para executar o script, utilize o seguinte comando:

```shell
python3 merge_rasters_mesh.py --indicator_files_mask=<indicator_files_mask> --mesh_file=<mesh_file_path> --column_relation_file=<column_relation_file_name> --new_mesh_file=<updated_mesh_file_path> --average --debug --output_folder=<output_folder_path>
```

- `--indicator_files_mask`: Caminho para a máscara de arquivos dos indicadores. A função `glob` será usada para encontrar os arquivos indicadores. Exemplo: `directory/*.tif`.
- `--mesh_file`: Caminho para o arquivo Shapefile que contém a malha geoespacial. Exemplo: `mesh.shp`.
- `--column_relation_file`: Caminho para o arquivo que contém a relação entre os nomes dos arquivos indicadores e as colunas associadas na malha. Exemplo: `relation.xlsx`.
- `--new_mesh_file`: Caminho para o novo arquivo Shapefile atualizado, que conterá as informações dos indicadores Raster agregados aos polígonos da malha geoespacial. Exemplo: `new_updated_mesh.shp`.
- `--average`: Parâmetro opcional para calcular a média dos valores dos pixels dentro de cada polígono da malha. Se não for fornecido, o valor máximo será considerado.
- `--debug`: Parâmetro opcional para ativar o modo de depuração, exibindo informações adicionais durante a execução.
- `--output_folder`: Caminho para o diretório onde os arquivos de saída serão salvos. O diretório será criado caso não exista.

### Funcionamento

O script realiza o seguinte processo:

1. Carrega a malha geoespacial a partir do arquivo Shapefile especificado.
2. Verifica se existe um arquivo de relação de colunas. Se não existir, cria um novo.
3. Procura e carrega os arquivos dos indicadores Raster baseados na máscara fornecida.
4. Itera sobre cada arquivo de indicador Raster, realizando as etapas de pré-processamento e junção com a malha geoespacial.
5. Calcula a média ponderada ou o valor máximo dos indicadores para cada polígono da malha, dependendo do valor do parâmetro `--average`.
6. Atualiza a malha com os novos valores dos indicadores.
7. Salva o novo arquivo da malha atualizado e o arquivo de relação de colunas.

### Observações

- Certifique-se de que o ambiente Python tenha as bibliotecas necessárias instaladas. Caso não tenha, você pode instalar as dependências listadas anteriormente.
- O script suporta apenas arquivos Raster (.tif) para os indicadores e arquivos Shapefile (.shp) para a malha.

### Saída

A saída deste script inclui a criação de um novo arquivo Shapefile atualizado, contendo as informações dos indicadores Raster agregados aos polígonos da malha geoespacial. Além disso, é gerado um arquivo de relação de colunas, no formato Excel, que mostra a correspondência entre os nomes dos arquivos indicadores e as colunas associadas na malha. Durante a execução, o script também apresenta informações sobre o progresso do processamento, incluindo o número de arquivos de indicadores processados e o tempo decorrido. Eventuais erros e exceções são mostrados para facilitar a depuração e o ajuste necessário no processo de mesclagem.

### Exemplo de Uso

```shell
python3 merge_rasters_mesh.py --indicator_files_mask=local_data/rasters/*.tif --mesh_file=local_data/malha/ferrovias.shp --column_relation_file=relacao_arquivos_colunas_malha_rodovias.xlsx --new_mesh_file=indicadores_rodovias.shp --average --debug --output_folder=output/result_rasters_mesh
```

Neste exemplo, o script será executado com a máscara `local_data/rasters/*.tif` para encontrar os arquivos indicadores Raster na pasta `local_data/rasters/`, utilizando o arquivo Shapefile da malha em `local_data/malha/ferrovias.shp`. As informações sobre os indicadores e as colunas utilizadas serão lidas a partir do arquivo `relacao_arquivos_colunas_malha_rodovias.xlsx`. O novo arquivo Shapefile da malha atualizada será salvo em `output/result_rasters_mesh`, com a opção de calcular a média dos valores dos pixels dentro de cada polígono ativada (`--average`). O modo de depuração será ativado para exibir informações adicionais durante a execução (`--debug`).

## Geração de Histogramas e Matrizes de Confusão

### Requisitos
- Python 3.x
- Bibliotecas listadas no arquivo `requirements.txt`
- Shapefile da malha (arquivo .shp)
- Shapefiles dos indicadores (arquivos .shp)
- Planilha de relação dos indicadores com as colunas da malha (arquivo .xlsx)

### Como usar
O script `generate_histograms_matrices.py` é utilizado para gerar histogramas e matrizes de confusão a partir de dados geoespaciais contidos em shapefiles. Ele aceita os seguintes argumentos:

```bash
python3 generate_histograms_matrices.py --mesh_file=path/to/mesh_file.shp --indicator_files_mask=path/to/indicator_files/*.shp --indicators_spreadsheet=path/to/indicators_spreadsheet.xlsx --m --h --debug --output_folder=path/to/output_folder
```

- `--mesh_file`: Caminho para o arquivo shapefile da malha.
- `--indicator_files_mask`: Caminho para o diretório contendo os shapefiles dos indicadores, que será usado com a função glob para encontrar os arquivos.
- `--indicators_spreadsheet`: Caminho para a planilha Excel que contém a relação dos indicadores com as colunas da malha.
- `--m`: Parâmetro opcional para gerar as matrizes de confusão.
- `--h`: Parâmetro opcional para gerar os histogramas.
- `--right_cut`: Parâmetro opcional para definir o valor máximo do eixo x dos histogramas.
- `--debug`: Ativar o modo de depuração para exibir informações adicionais.
- `--output_folder`: Caminho para o diretório onde os arquivos de saída serão salvos.

### Funcionamento
O script realiza o processamento dos indicadores e da malha para gerar as matrizes de confusão e histogramas.

 Ele executa as seguintes etapas:

1. Carrega as bibliotecas e realiza os imports necessários.
2. Carrega os parâmetros passados na linha de comando.
3. Cria os diretórios de saída caso não existam.
4. Encontra os arquivos dos indicadores usando a função glob.
5. Carrega a malha e os indicadores a partir dos arquivos shapefile.
6. Realiza a transformação da malha para o CRS padrão (5880).
7. Verifica a relação entre os indicadores e as colunas da malha.
8. Define padrões para encontrar a coluna do indicador.
9. Realiza a junção (interseção) entre a malha e os indicadores.
10. Define os intervalos de bins para as matrizes de confusão.
11. Gera as matrizes de confusão e os histogramas para cada indicador.
12. Salva os resultados nos diretórios de saída.

### Observações
- Certifique-se de que o ambiente Python tenha as bibliotecas necessárias instaladas. Caso não tenha, você pode instalar as dependências listadas no arquivo `requirements.txt`.
- O script suporta apenas arquivos shapefile (.shp) para a malha e os indicadores e uma planilha Excel (.xlsx) para a relação entre os indicadores e as colunas da malha.

### Saída
O script gera dois tipos de saída:

1. Matrizes de Confusão: São salvas no diretório `confusion_matrices` dentro do diretório de saída definido.
2. Histogramas: São salvos no diretório `histograms` dentro do diretório de saída definido.

### Exemplo de Uso
```bash
python3 generate_histograms_matrices.py --mesh_file=data/mesh/mesh_file.shp --indicator_files_mask=data/indicators/*.shp --indicators_spreadsheet=data/planilhas/indicators_spreadsheet.xlsx --m --h --debug --output_folder=output/result_histograms_matrices
```

Neste exemplo, o script será executado com o arquivo shapefile da malha em `data/mesh/mesh_file.shp`, os shapefiles dos indicadores em `data/indicators/*.shp`, a planilha de relação dos indicadores em `data/planilhas/indicators_spreadsheet.xlsx`, e irá gerar as matrizes de confusão e os histogramas em `output/result_histograms_matrices`.

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

Esse comando realiza a geração da matriz de confusão para os indicadores contidos na pasta `indicadores/`, utilizando o arquivo de malha `malha/ferrovias.shp`. As informações sobre os indicadores e colunas utilizadas são lidas a partir da planilha `solução_risco_desl_para_matriz.xlsx`. As imagens da matriz de confusão são salvas no diretório `output/`.

## Geração de legendas QML para CSV

Este repositório contém um script Python chamado `generate_legends.py` que permite a geração de legendas QML para um arquivo CSV. O script analisa os arquivos QML, que contêm informações de estilo para representação de dados geoespaciais, e extrai as informações relevantes para criar uma tabela em formato CSV.

### Descrição

O script `generate_legends.py` é usado para processar arquivos QML e extrair informações de estilo, como cores e valores mínimos e máximos de legendas. Esses dados são então organizados em uma tabela CSV que pode ser usada para criar legendas em visualizações de dados geoespaciais.

### Requisitos

Certifique-se de ter os seguintes requisitos instalados:

- Python 3.x
- Bibliotecas Python: `pandas`

Você pode instalar as bibliotecas necessárias executando o seguinte comando:

```shell
pip install -r requeriments.txt
```

### Como usar

Execute o script `generate_legends.py` passando os argumentos necessários. O script requer os seguintes argumentos:

- `--qml_files`: Caminho para o diretório onde os arquivos QML estão localizados. Use padrões glob para encontrar os arquivos QML.
- `--debug`: Ativa o modo de depuração.
- `--output_folder`: Caminho para o diretório onde os arquivos gerados serão salvos.
- `--output_file`: Nome do arquivo de saída.

Aqui está um exemplo de como executar o script:

```shell
python3 generate_legends.py --qml_files=local_data/qml/**/*.qml --debug --output_folder=output/export_legends --output_file=legends_indicators.csv
```

Certifique-se de fornecer os caminhos corretos para os arquivos QML, o diretório de saída e o nome do arquivo de saída.

### Funcionamento

O script começa lendo os argumentos fornecidos e iniciando o processamento. Ele utiliza a biblioteca `xml.etree.ElementTree` para analisar os arquivos QML e extrair informações relevantes, como as cores dos símbolos e os valores das legendas. As informações extraídas são então organizadas em uma tabela CSV.

### Observações

- O modo de depuração (`--debug`) fornece informações adicionais durante a execução do script, facilitando a verificação do progresso e dos resultados.
- O script cria uma pasta de saída especificada, se ela ainda não existir.

### Saída

A saída deste script é um arquivo CSV que contém as informações de estilo extraídas dos arquivos QML. O arquivo CSV terá as colunas: 'id', 'label', 'color', 'minvalue', 'maxvalue', 'legend_id', 'indicator', 'tag', 'order'.

### Exemplo de Uso

```
python3 generate_legends.py --qml_files=local_data/qml/**/*.qml --debug --output_folder=output/export_legends --output_file=legends_indicators.csv
```

Esse comando processará os arquivos QML encontrados no diretório `local_data/qml/` e seus subdiretórios, ativando o modo de depuração. Os resultados serão salvos na pasta `output/export_legends` com o nome do arquivo de saída `legends_indicators.csv`.

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