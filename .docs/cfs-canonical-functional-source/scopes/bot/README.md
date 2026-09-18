# Scope `bot` — Bot de Telegram

## Qué incluye

Este scope cubre el **comportamiento funcional en tiempo de ejecución** del
bot de Telegram contenido en el paquete `app/`, tal y como queda desplegado
por `docker compose up` una vez configurado:

- Conversación por Telegram: comando `/start`, mensajes de texto, control de
  acceso por lista blanca de usuarios, historial de conversación por chat,
  recorte del historial por presupuesto de tokens y compactación del
  historial antiguo en un resumen (`app/bot.py`).
- Transcripción de notas de voz / audio con `faster-whisper` y su
  incorporación a la conversación (`app/bot.py`).
- Motor de IA: selección de backend LLM (`ollama` local o `cloud` vía API
  compatible con OpenAI), llamada al modelo, precalentamiento del modelo
  Ollama al arrancar, y el bucle de uso de herramientas (`app/llm.py`).
- Sistema de herramientas opcionales que el modelo puede invocar durante la
  conversación, y la herramienta de búsqueda web incluida (`app/tools/`).
- Configuración funcional que determina el comportamiento anterior, tal y
  como se lee en tiempo de ejecución desde variables de entorno
  (`app/config.py`, `.env.example`).

## Qué excluye

- **`setup.py` y `update.py`** (raíz del repositorio): son herramientas de
  *tooling* de onboarding/actualización de un clon del template (asistente
  interactivo, fusión de Git, generación de `.env`/`system_prompt.txt`).
  No son funcionalidad del bot en ejecución ni algo con lo que interactúe un
  usuario de Telegram ni, en general, un operador *después* de tener el
  agente funcionando; se consideran infraestructura de desarrollo/despliegue
  del template, fuera de este scope.
- El **contenido concreto de la personalidad** de un agente (texto libre en
  `app/prompts/system_prompt.txt`, gitignored y propio de cada clon) no se
  documenta como dato — es configuración por instancia, no comportamiento
  del producto. Sí se documenta el *mecanismo* (existencia del prompt de
  sistema, placeholder `{{AGENT_NAME}}`, y qué añade el bot al vuelo:
  fecha/hora y resumen de historial).
- Los ficheros Docker (`Dockerfile`, `docker-compose.yml`,
  `docker-compose.override.yml.example`) se usan sólo como fuente para
  confirmar comportamiento (p. ej. qué servicios existen, persistencia de
  modelos), no se documentan como funcionalidad propia de infraestructura
  Docker.
- No se documenta el detalle interno de librerías de terceros
  (`python-telegram-bot`, `faster-whisper`, `httpx`) más allá de cómo el bot
  las usa funcionalmente.

## Qué proyectos o componentes técnicos deben analizarse

- `app/config.py`, `app/llm.py`, `app/bot.py`, `app/main.py`
- `app/tools/base.py`, `app/tools/__init__.py`, `app/tools/web_search.py`
- `app/prompts/system_prompt.txt.example`
- `.env.example`, `docker-compose.yml`
- `tests/` como confirmación de comportamiento (no como fuente de intención)

## Dependencias funcionales con otros scopes

Ninguna. Este repositorio es un proyecto único (un template de bot por
clon) y no existen actualmente otros scopes CFS definidos en este
repositorio.

## Límites funcionales para evitar duplicación

No aplica: es el único scope del repositorio, por lo que no hay
responsabilidad funcional que pertenezca a otro scope.
