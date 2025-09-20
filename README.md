# Eklesia IA Python

Sistema para integração e automação de processos utilizando inteligência artificial.

## Postgres externo via rede Docker compartilhada

Para compartilhar o mesmo Postgres entre múltiplas stacks no mesmo host (mesmo IP) sem expor porta pública, use uma rede Docker externa e um alias DNS interno estável.

### 1) Criar rede externa (uma vez no host)

```sh
docker network create eklesia-net
```

### 2) Subir o Postgres em outra stack

Use o exemplo `docker-compose.postgres.example.yml` (idealmente em OUTRO diretório) para subir o Postgres conectado à `eklesia-net` e com alias `eklesia-postgres`:

```sh
# Em OUTRO diretório (recomendado)
docker compose -f docker-compose.postgres.example.yml up -d
```

- Banco padrão: `eklesia_ia_db`
- Usuário: `postgres` (ajuste senha no compose exemplo)
- Alias DNS interno: `eklesia-postgres`

### 3) Configurar a API para usar o Postgres externo

No `.env` da API, aponte a `DATABASE_URL` para o host `eklesia-postgres`:

```env
DATABASE_URL=postgresql+psycopg2://USUARIO:SENHA@eklesia-postgres:5432/NOME_BANCO
```

Garanta que o `docker-compose.yml` da API usa a rede externa `eklesia-net` e que o serviço `backend` está conectado a ela.

### 4) Subir a API

```sh
docker compose up -d
```

Pronto: a API acessa o Postgres via DNS interno apenas dentro da rede Docker, mantendo o banco não exposto na internet.

## Instalação

```bash
git clone https://github.com/seu-usuario/eklesia.ia.python.git
cd eklesia.ia.python
pip install -r requirements.txt
```

## Uso

### Exemplo de Requisição

```json
POST /api/v1/processar
Content-Type: application/json

{
    "texto": "Qual a previsão do tempo para amanhã?",
    "usuario_id": 123
}
```

### Exemplo de Resposta

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
    "resposta": "A previsão do tempo para amanhã é de sol com poucas nuvens.",
    "status": "sucesso"
}
```

## Funcionalidades

- Processamento de linguagem natural
- Integração com APIs externas
- Respostas automatizadas

## Contribuição

Pull requests são bem-vindos. Para grandes mudanças, abra uma issue primeiro para discutir o que você gostaria de modificar.

## Licença

[MIT](LICENSE)