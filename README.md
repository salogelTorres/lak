# Plantilla de agente Telegram + LLM

Plantilla para levantar, con un solo comando, un bot de Telegram conectado a un
modelo (local vía Ollama, o remoto vía cualquier API compatible con OpenAI:
OpenAI, OpenRouter, proxies, etc.), corriendo en Docker.

## Crear un nuevo agente

1. Clona este repo con el nombre del nuevo agente:

   ```bash
   git clone https://github.com/salogelTorres/lak.git mi-agente
   cd mi-agente
   ```

2. Ejecuta el asistente de configuración (solo necesita Python, sin dependencias):

   ```bash
   python setup.py
   ```

   Te pedirá el token de Telegram (@BotFather), el backend de LLM (`ollama` o
   `cloud`), el modelo, y opcionalmente la API key. Genera el archivo `.env` y,
   si quieres, arranca el contenedor con `docker compose up -d --build`.

3. Si prefieres hacerlo a mano:

   ```bash
   cp .env.example .env   # edítalo con tus valores
   docker compose up -d --build
   ```

## Personalizar el agente

- **Nombre y personalidad**: edita `app/prompts/system_prompt.txt` (soporta el
  placeholder `{{AGENT_NAME}}`, que se rellena con `AGENT_NAME` del `.env`).
  No hace falta reconstruir la imagen: `docker compose restart` recarga el
  prompt (está montado como volumen).
- **Backend del LLM**: variable `LLM_BACKEND` en `.env`, `ollama` o `cloud`.
  - `ollama`: usa un modelo local. Si Ollama corre en el host (no en Docker),
    `OLLAMA_BASE_URL=http://host.docker.internal:11434` ya funciona en
    Docker Desktop (Windows/Mac) sin configuración extra.
  - `cloud`: cualquier API con endpoint `/chat/completions` compatible con
    OpenAI (OpenAI, OpenRouter, etc.). Configura `CLOUD_API_BASE_URL`,
    `CLOUD_API_KEY` y `CLOUD_MODEL`.
- **Acceso**: `ALLOWED_USER_IDS` en `.env` limita quién puede hablar con el
  bot (lista de IDs numéricos de Telegram separados por comas). Vacío =
  cualquiera.

## Varios agentes en paralelo

Cada agente es una carpeta/clon independiente con su propio `.env` y su
propio `docker-compose`. Para crear otro, repite el paso 1 en otra carpeta
con otro token de Telegram.

## Comandos útiles

```bash
docker compose logs -f      # ver logs
docker compose restart      # reiniciar (p. ej. tras editar el prompt)
docker compose down         # parar y eliminar el contenedor
```
