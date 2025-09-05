from dotenv import load_dotenv
from app.biblia_api import (
    buscar_versiculo,
    pesquisar_termo,
    listar_biblias,
    listar_livros,
    buscar_conteudo_multimidia,
    buscar_audio_timestamps,
    listar_idiomas,
    listar_paises
)

load_dotenv()

# Exemplo de parâmetros reais
LANGUAGE_CODE = "por"  # português
BOOK_ID = "GEN"        # Gênesis
CHAPTER_ID = 1
VERSE_NUMBER = 1

print("Testando buscar_versiculo...")
versiculo = buscar_versiculo(LANGUAGE_CODE, BOOK_ID, CHAPTER_ID, VERSE_NUMBER)
print("Versículo:", versiculo)

print("\nTestando pesquisar_termo...")
pesquisa = pesquisar_termo("amor")
print("Pesquisa:", pesquisa)

print("\nTestando listar_biblias...")
biblias = listar_biblias()
print("Bíblias:", biblias)

if biblias and isinstance(biblias, list):
    bible_id = biblias[0].get("id")
    print(f"\nTestando listar_livros para a bíblia {bible_id}...")
    livros = listar_livros(bible_id)
    print("Livros:", livros)
else:
    print("Não foi possível obter ID de bíblia para listar livros.")

print("\nTestando buscar_conteudo_multimidia...")
# Exemplo fictício de fileset_id, ajuste conforme sua base
fileset_id = "GEN1TXT"  # Exemplo
conteudo = buscar_conteudo_multimidia(fileset_id, BOOK_ID, CHAPTER_ID)
print("Conteúdo multimídia:", conteudo)

print("\nTestando buscar_audio_timestamps...")
audio_timestamps = buscar_audio_timestamps(fileset_id, BOOK_ID, CHAPTER_ID)
print("Timestamps de áudio:", audio_timestamps)

print("\nTestando listar_idiomas...")
idiomas = listar_idiomas()
print("Idiomas:", idiomas)

print("\nTestando listar_paises...")
paises = listar_paises()
print("Países:", paises)
