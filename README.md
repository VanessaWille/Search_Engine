# Algoritmo de busca: Find my Pasta
Repositório para disciplina Projetos em Ciência de Dados, na qual o objetivo é desenvolver um sistema de busca eficiente que permita aos usuários pesquisar receitas por meio de diversos atributos associados, tais como nome, descrição, ingredientes, instruções, categorias (tags), avaliações e informações nutricionais. A search engine foi desenvolvida utilizando uma base de dados de receitas organizada, a fim de simular arquivos realistas e possibilitar o desenvolvimento do sistema. 

## Principais arquivos:
 - ```app.py```: Contem o codigo necessário para levantar uma interface web com backend flask para o buscador.
 - ```Ollama_connection.py```: Lib com a classe utilizada para acessar a API do Ollama e fazer queries dinamicamente para um LLM.
 - ```fill_in_missing_reviews.py```: Codigo para preencher com um LLM as notas faltantes para os pares de query-resposta dados pelos modelos de busca.
 - ```models_comparison.ipynb```: Notebook de relatório para comparar o desempenho de diferentes modelos de busca.


## Grupo
- Gustavo Ramalho
- Gustavo Sanches Costa
- Lucas Bryan Treuke
- Rodrigo Gomes Hutz Pintucci
- Vanessa Berwanger Wille
