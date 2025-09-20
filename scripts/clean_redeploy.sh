#!/usr/bin/env bash
set -euo pipefail

# clean_redeploy.sh
# Uso: pode ser executado de QUALQUER lugar. Ele sempre vai operar em /www/wwwroot/api-ia.eklesia.app.br
# Objetivo: remover completamente containers, volumes e código anteriores e clonar novamente do GitHub.
# ATENÇÃO: Isso APAGA todos os dados anteriores do Postgres e vetores Chroma.

REPO_URL="https://github.com/AldairSbarros/eklesia.ia.python.git"
BASE_DIR="/www/wwwroot"
PROJECT_DIR="/www/wwwroot/api-ia.eklesia.app.br"
COMPOSE_FILE="docker-compose.yml"

echo "==> Garantindo diretório base $BASE_DIR existe"
mkdir -p "$BASE_DIR"

echo "==> Parando containers relacionados (se existirem)"
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
  (cd "$PROJECT_DIR" && docker compose down || true)
fi

echo "==> Removendo containers órfãos usando imagem postgres ou ollama ou backend"
for c in $(docker ps -aq --filter "ancestor=postgres" --filter "name=postgres" || true); do docker rm -f "$c" || true; done
for c in $(docker ps -aq --filter "ancestor=ollama/ollama" --filter "name=ollama" || true); do docker rm -f "$c" || true; done

echo "==> Removendo containers que contenham nome antigo do projeto"
for c in $(docker ps -aq --filter "name=apieklesiaappbr" --filter "name=api-iaeklesiaappbr" || true); do docker rm -f "$c" || true; done

echo "==> Removendo volumes relacionados"
for v in $(docker volume ls -q | grep -E 'eklesia|api-iaeklesiaappbr|apieklesiaappbr' || true); do docker volume rm "$v" || true; done

echo "==> (Opcional) Limpando imagens não usadas"
docker image prune -f || true

if [ -d "$PROJECT_DIR" ]; then
  echo "==> Removendo diretório existente $PROJECT_DIR"
  rm -rf "$PROJECT_DIR"
fi

echo "==> Clonando repositório"
git clone "$REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "==> Criando arquivo .env se não existir"
if [ ! -f .env ]; then
cat > .env <<'EOF'
# Preencha os segredos reais após o deploy
BIBLE_API_KEY=COLOQUE_SUA_CHAVE
BIBLE_API_URL=https://sua-api-biblia
DATABASE_URL=postgresql+psycopg2://aldai:senha@postgres:5432/eklesia_ia_db
JWT_SECRET=altereme
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=gemma:2b
EOF
fi

echo "==> Subindo stack Docker (pull + up)"
docker compose pull
docker compose up -d --remove-orphans

echo "==> Aguardando Postgres ficar pronto"
RETRIES=30
until docker compose exec postgres pg_isready -U aldai >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "Aguardando Postgres... ($RETRIES)"; sleep 2; RETRIES=$((RETRIES-1));
done

echo "==> Verificando versão do Postgres"
if docker compose exec postgres psql -U aldai -d eklesia_ia_db -c "SELECT version();" >/dev/null 2>&1; then
  docker compose exec postgres psql -U aldai -d eklesia_ia_db -c "SELECT version();"
else
  echo "[AVISO] Não foi possível consultar versão do Postgres ainda. Verifique logs: docker compose logs postgres"
fi

echo "==> Testando backend (docs endpoint)"
if curl -I http://localhost:8000/docs 2>/dev/null | head -n 1 | grep -q "200\|307\|308"; then
  curl -I http://localhost:8000/docs 2>/dev/null | head -n 1
else
  echo "[AVISO] /docs não retornou 200/redirect ainda. Verifique logs: docker compose logs backend"
fi

echo "==> Concluído. Ajuste valores reais no .env se necessário e reinicie backend se alterar segredos:"
echo "    docker compose restart backend"
