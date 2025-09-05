import os
import requests
from typing import List, Optional, Dict, Any

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

BIBLE_API_URL = os.getenv("BIBLE_API_URL", "https://4.dbt.io/api")
BIBLE_API_KEY = os.getenv("BIBLE_API_KEY", "")


def buscar_versos_por_palavra(
    palavra: str,
    idiomas: Optional[List[str]] = None,
    limite: int = 50
) -> List[Dict[str, Any]]:
    """
    Busca todos os versos que contenham a palavra,
    em todos os idiomas especificados.
    """
    resultados = []
    idiomas = idiomas or ["por", "spa", "eng", "ell", "heb"]
    for idioma in idiomas:
        params = {
            "key": BIBLE_API_KEY,
            "query": palavra,
            "language_code": idioma,
            "limit": limite
        }
        url = f"{BIBLE_API_URL}/search"
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            versos = data.get("verses", [])
            for v in versos:
                resultados.append({
                    "idioma": idioma,
                    "referencia": v.get("reference"),
                    "texto": v.get("text"),
                    "bible_id": v.get("bible_id"),
                    "livro": v.get("book_id"),
                    "capitulo": v.get("chapter"),
                    "versiculo": v.get("verse"),
                    "recursos": buscar_recursos_extras(
                        v.get("bible_id"),
                        v.get("book_id"),
                        v.get("chapter")
                    )
                })
    return resultados


def buscar_verso_por_referencia(
    language_code: str,
    book_id: str,
    chapter_id: str,
    verse_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Busca um verso específico por referência.
    """
    url = (
        f"{BIBLE_API_URL}/bibles/verses/"
        f"{language_code}/{book_id}/{chapter_id}"
    )
    if verse_number:
        url += f"/{verse_number}"
    params = {"key": BIBLE_API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        return data
    return {"erro": "Verso não encontrado"}


def listar_biblias_idiomas(
    idiomas: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Lista todas as versões disponíveis nos idiomas desejados.
    """
    idiomas = idiomas or ["por", "spa", "eng", "ell", "heb"]
    params = {
        "key": BIBLE_API_KEY,
        "language_code": ",".join(idiomas)
    }
    url = f"{BIBLE_API_URL}/bibles"
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("data", [])
    return []


def buscar_recursos_extras(
    bible_id: str,
    book_id: str,
    chapter_id: str
) -> Dict[str, Any]:
    """
    Busca recursos extras (áudio, vídeo, etc) para um capítulo.
    """
    recursos = {}
    # Descobrir filesets disponíveis para a bíblia
    url_filesets = f"{BIBLE_API_URL}/bibles/{bible_id}"
    params = {"key": BIBLE_API_KEY}
    resp = requests.get(url_filesets, params=params)
    if resp.status_code == 200:
        data = resp.json()
        filesets = data.get("data", {}).get("filesets", [])
        for fs in filesets:
            fs_id = fs.get("id")
            fs_type = fs.get("set_type_code")
            # Buscar conteúdo do capítulo
            url_content = (
                f"{BIBLE_API_URL}/bibles/filesets/{fs_id}/"
                f"{book_id}/{chapter_id}"
            )
            resp2 = requests.get(url_content, params=params)
            if resp2.status_code == 200:
                recursos[fs_type] = resp2.json()
    return recursos


def listar_tipos_fileset():
    url = f"{BASE_URL}/bibles/filesets/media/types"
    params = {"v": 4, "key": API_KEY}
    response = requests.get(url, params=params)
    print("Status:", response.status_code)
    print("Response:", response.text)
    if response.status_code == 200:
        return response.json()
    return None


API_KEY = os.getenv("BIBLE_API_KEY")
BASE_URL = os.getenv("BIBLE_API_URL", "http://localhost:8080/api")


def buscar_versiculo(
    language_code,
    book_id,
    chapter_id,
    verse_number=None,
    fileset_id=None
):
    # Busca um versículo específico usando o endpoint correto da API DBT
    # O endpoint correto é:
    # /bibles/filesets/{fileset_id}/{book_id}/{chapter_id}/{verse_number}
    # Mas para uso genérico, vamos buscar o fileset de texto primeiro
    try:
        # Buscar bible_id
        bibles_url = (
            f"{BIBLE_API_URL}/bibles"
            f"?language_code={language_code}"
            f"&v=4&key={BIBLE_API_KEY}"
        )
        bibles_resp = requests.get(bibles_url)
        bibles_data = (
            bibles_resp.json().get("data", [])
            if bibles_resp.status_code == 200 else []
        )
        if not bibles_data:
            return {"error": "Nenhuma bíblia encontrada para o idioma."}
        bible_id = bibles_data[0]["abbr"]
        # Se não foi passado fileset_id, buscar o primeiro disponível
        if not fileset_id:
            filesets_url = (
                f"{BIBLE_API_URL}/bibles/{bible_id}"
                f"?v=4&key={BIBLE_API_KEY}"
            )
            filesets_resp = requests.get(filesets_url)
            filesets_obj = (
                filesets_resp.json().get("data", {}).get("filesets", {})
                if filesets_resp.status_code == 200 else {}
            )
            filesets = [
                fs
                for fs_list in filesets_obj.values()
                for fs in fs_list
                if fs.get("type", "").startswith("text")
                or fs.get("set_type_code", "").startswith("text")
            ]
            if not filesets:
                return {"error": "Nenhum fileset de texto encontrado."}
            fileset_id = filesets[0]["id"]
        # Montar endpoint correto para buscar o versículo
        if verse_number:
            url = (
                f"{BIBLE_API_URL}/bibles/filesets/{fileset_id}/"
                f"{book_id}/{chapter_id}/"
                f"{verse_number}?v=4&key={BIBLE_API_KEY}"
            )
        else:
            url = (
                f"{BIBLE_API_URL}/bibles/filesets/{fileset_id}/"
                f"{book_id}/{chapter_id}?v=4&key={BIBLE_API_KEY}"
            )
        print(f"[DEBUG buscar_versiculo] URL: {url}")
        response = requests.get(url)
        print(f"[DEBUG buscar_versiculo] Status: {response.status_code}")
        print(f"[DEBUG buscar_versiculo] Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            # Retorna o primeiro versículo encontrado
            if (
                "data" in data
                and isinstance(data["data"], list)
                and data["data"]
            ):
                return data["data"][0]
            return data
        # Fallback: se 404, buscar capítulo inteiro e filtrar o versículo
        if response.status_code == 404 and verse_number:
            cap_url = (
                f"{BIBLE_API_URL}/bibles/filesets/{fileset_id}/"
                f"{book_id}/{chapter_id}?v=4&key={BIBLE_API_KEY}"
            )
            print(f"[DEBUG buscar_versiculo] Fallback URL: {cap_url}")
            cap_resp = requests.get(cap_url)
            print(
                (
                    f"[DEBUG buscar_versiculo] Fallback Status: "
                    f"{cap_resp.status_code}"
                )
            )
            print(
                f"[DEBUG buscar_versiculo] Fallback Response: {cap_resp.text}"
            )
            if cap_resp.status_code == 200:
                cap_data = cap_resp.json().get("data", [])
                for verse in cap_data:
                    vnum = (
                        verse.get("verse_start")
                        or verse.get("verse_sequence")
                        or verse.get("verse")
                    )
                    if str(vnum) == str(verse_number):
                        return verse
            return {
                "error": (
                    (
                        "Versículo não encontrado nem no capítulo. Status: "
                        f"{response.status_code}"
                    )
                ),
                "response": response.text
            }
        return {
            "error": (
                f"Versículo não encontrado. Status: {response.status_code}"
            ),
            "response": response.text
        }
    except Exception as e:
        return {"error": str(e)}


def pesquisar_termo(termo, page=1, limit=5):
    try:
        # Buscar o primeiro bible_id disponível em português
        bibles_url = (
            f"{BIBLE_API_URL}/bibles?language_code=por"
            f"&v=4&key={BIBLE_API_KEY}"
        )
        bibles_resp = requests.get(bibles_url)
        bibles_data = (
            bibles_resp.json().get("data", [])
            if bibles_resp.status_code == 200 else []
        )
        if not bibles_data:
            return {"error": "Nenhuma bíblia encontrada para busca."}
        bible_id = bibles_data[0]["abbr"]
        # Buscar fileset_id de texto para o bible_id selecionado
        filesets_url = (
            f"{BIBLE_API_URL}/bibles/{bible_id}"
            f"?v=4&key={BIBLE_API_KEY}"
        )
        filesets_resp = requests.get(filesets_url)
        filesets_obj = (
            filesets_resp.json().get("data", {}).get("filesets", {})
            if filesets_resp.status_code == 200 else {}
        )
        filesets = [
            fs
            for fs_list in filesets_obj.values()
            for fs in fs_list
            if fs.get("type", "").startswith("text")
            or fs.get("set_type_code", "").startswith("text")
        ]
        if not filesets:
            return {
                "error": (
                    "Nenhum fileset de texto encontrado para a bíblia."
                )
            }
        fileset_id = filesets[0]["id"]
        url = f"{BIBLE_API_URL}/search"
        params = {
            "key": BIBLE_API_KEY,
            "query": termo,
            "bible_id": bible_id,
            "fileset_id": fileset_id,
            "page": page,
            "limit": limit,
            "v": 4
        }
        response = requests.get(url, params=params)
        print(f"[DEBUG pesquisar_termo] URL: {url}")
        print(f"[DEBUG pesquisar_termo] Params: {params}")
        print(f"[DEBUG pesquisar_termo] Status: {response.status_code}")
        print(f"[DEBUG pesquisar_termo] Response: {response.text}")
        if response.status_code == 200:
            result = response.json()
            # Se vier no formato verses > data, retorna direto os versos
            if "verses" in result and "data" in result["verses"]:
                return {"data": result["verses"]["data"]}
            return result
        return {
            "error": f"Busca falhou. Status: {response.status_code}",
            "response": response.text
        }
    except Exception as e:
        return {"error": str(e)}


def listar_biblias():
    url = f"{BIBLE_API_URL}/bibles"
    params = {"v": 4, "key": BIBLE_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", [])
    return []


def listar_livros(bible_id):
    url = f"{BASE_URL}/bibles/{bible_id}/book"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None


def buscar_conteudo_multimidia(fileset_id, book, chapter):
    url = f"{BASE_URL}/bibles/filesets/{fileset_id}/{book}/{chapter}"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None


def buscar_audio_timestamps(fileset_id, book, chapter):
    url = f"{BASE_URL}/timestamps/{fileset_id}/{book}/{chapter}"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None


def listar_idiomas():
    url = f"{BASE_URL}/languages"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None


def listar_paises():
    url = f"{BASE_URL}/countries"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None
    url = f"{BASE_URL}/countries"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None
