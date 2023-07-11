# JupyterAdaptaBrasil

#### Cruzamento de indicadores sobre uma malha

Este repositório contém um código em Python que realiza a manipulação e processamento de dados espaciais utilizando as bibliotecas `geopandas`, `pandas` e `pyproj`. O objetivo principal do código é realizar a interseção de geometrias e realizar cálculos de média ponderada para atribuir valores a uma coluna específica de um arquivo shapefile.

## Requisitos

Antes de executar o código, certifique-se de ter instalado as seguintes bibliotecas:

- `pandas`
- `geopandas`
- `pyproj`

Você pode instalar as bibliotecas executando os seguintes comandos:

```shell
pip install pandas geopandas pyproj
```

## Uso

1. Certifique-se de ter os arquivos necessários no diretório especificado pelo caminho definido nas variáveis `MASCARA_ARQUIVOS_INDICADORES`, `CAMINHO_ARQUIVO_MALHA` e `NOME_ARQUIVO_RELACAO_COLUNAS`.

2. Execute o arquivo Python:

```shell
python main.py
```

## Configuração

Antes de executar o código, você pode ajustar as seguintes variáveis de acordo com suas necessidades:

- `MASCARA_ARQUIVOS_INDICADORES`: Caminho da máscara para localizar os arquivos de indicadores.
- `CAMINHO_ARQUIVO_MALHA`: Caminho do arquivo shapefile da malha.
- `NOME_ARQUIVO_RELACAO_COLUNAS`: Caminho do arquivo Excel que contém a relação de colunas e arquivos processados.
- `CAMINHO_NOVO_ARQUIVO_MALHA_ATUALIZADO`: Caminho para salvar o arquivo shapefile da malha atualizada.
- `DEBUG`: Variável booleana para ativar/desativar o modo de depuração.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo `LICENSE` para obter mais informações.

Fim