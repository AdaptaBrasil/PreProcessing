# Leia o arquivo local_data/file.txt e exclua a primeira linha e segunda linha e ultima. Em seguida, salve o arquivo como local_data/new_file.txt.
import os

file_base = "data/qml_base.qml"
new_file = "local_data/new_file.txt"

"""with open(file, "r") as f:
    lines = f.readlines()

with open(new_file, "w") as f:
    f.writelines(lines[2:-1])
    """

# Lê o conteúdo do arquivo base
with open(file_base, 'r') as file:
    content = file.read()

# Solicita ao usuário que insira um nome
nome = input("Por favor, insira o seu nome: ")

# Substitui o marcador {{NOME_AQUI}} pelo nome inserido
novo_conteudo = content.replace("{{NOME_AQUI}}", nome)

# Salva o novo conteúdo em um arquivo novo
with open(new_file, 'w') as new_file:
    new_file.write(novo_conteudo)

print("O nome foi inserido e o arquivo foi salvo como 'novo_file.txt'.")
