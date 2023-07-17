# Merge de Indicadores em Malha

Este repositório contém um script Python chamado `merge_indicadores_malha.py` que realiza a junção de indicadores em uma malha geoespacial. O script utiliza a biblioteca `geopandas` para manipulação de dados espaciais e `pandas` para manipulação de dados tabulares.

## Requisitos

Certifique-se de ter os seguintes requisitos instalados:

- Python 3
- Bibliotecas Python: `pandas`, `geopandas`, `pyproj`

Você pode instalar as bibliotecas necessárias executando o seguinte comando:

```shell
pip install -r requirements.txt
```

Isso irá instalar todas as dependências listadas no arquivo `requirements.txt`.

## Instalação

1. Clone este repositório para o seu ambiente local.
2. Navegue até o diretório do repositório.

## Uso

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

# Matriz de Confusão para N Casos

Este código permite gerar a matriz de confusão para N casos, comparando os valores estimados de indicadores espaciais com os valores originais. Ele utiliza arquivos shapefiles que contêm informações espaciais e colunas de valores dos indicadores. Além disso, o código requer uma planilha que relaciona os indicadores às colunas utilizadas na matriz de confusão.

## Requisitos

- Python 3.x
- Bibliotecas: geopandas, pyproj, pandas, os, seaborn, glob, matplotlib, sklearn

## Como usar

Execute o seguinte comando para rodar o script:

```
python3 matriz_confusao_n_casos.py --arquivo_malha=<arquivo_malha> --mascara_indicadores=<mascara_indicadores> --planilha_indicadores=<planilha_indicadores>
```

- `<arquivo_malha>`: Caminho para o arquivo shapefile da malha espacial.
- `<mascara_indicadores>`: Caminho do diretório onde estão as máscaras de arquivos indicadores. O script usará o glob para encontrar os arquivos indicadores.
- `<planilha_indicadores>`: Caminho da planilha que contém as relações de indicadores por colunas.

## Funcionamento

O script carrega a malha espacial a partir do arquivo shapefile especificado. Em seguida, lê os arquivos indicadores (shapefiles) a partir do diretório indicado pela máscara. Ele também lê a planilha que contém as relações entre os indicadores e as colunas utilizadas na matriz de confusão.

Para cada indicador, o script faz o merge com a malha e realiza a interseção para obter os valores originais e estimados. Em seguida, gera a matriz de confusão comparando esses valores. A matriz de confusão é salva como uma imagem no diretório de saída.

## Observações

- O código realiza ajustes no CRS (Coordinate Reference System) da malha para EPSG 5880, se necessário.
- A matriz de confusão é gerada com rótulos específicos (0.00 a 0.01, 0.01 a 0.25, 0.25 a 0.50, 0.50 a 0.75, 0.75 a 1), que podem ser personalizados conforme necessário.
- O script ignora warnings durante a execução.

## Saída

- Imagens da matriz de confusão: Para cada indicador, uma imagem da matriz de confusão é salva no diretório 'output'. Os nomes dos arquivos de saída seguem o padrão `matriz_confusao_indicador_<i>_<nome_indicador>.png`, onde `<i>` é o índice do indicador e `<nome_indicador>` é o nome do indicador usado para a geração da matriz.

## Exemplo de Uso

```
python3 matriz_confusao_n_casos.py --arquivo_malha=malha/ferrovias.shp --mascara_indicadores=indicadores/*.shp --planilha_indicadores=planilhas/solução_risco_desl_para_matriz.xlsx
```

Esse comando realiza a geração da matriz de confusão para os indicadores contidos na pasta `indicadores/`, utilizando o arquivo de malha `malha/ferrovias.shp`. As informações sobre os indicadores e colunas utilizadas são lidas a partir da planilha `solução_risco_desl_para_matriz.xlsx`. As imagens da matriz de confusão são salvas no diretório `output/`.

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](./LICENSE) para obter mais informações.

# Erros communs
####  rtree
Talves seja necessário instalar umas dependências Linux:
```shell
pip uninstall rtree
sudo apt install libspatialindex-dev
pip install rtree
```
