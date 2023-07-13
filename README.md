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

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](./LICENSE) para obter mais informações.