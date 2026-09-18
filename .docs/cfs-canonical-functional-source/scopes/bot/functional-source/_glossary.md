---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: GLOSSARY
module-id: NOT_APPLICABLE
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Glosario funcional

# 1. Metainformación

Terminología consolidada a partir de `app/*.py`, `.env.example`, `README.md`
y `CLAUDE.md`. El código y la documentación de este repositorio están en
inglés; el contenido funcional de este CFS se redacta en español conforme a
`content-language: es`, manteniendo entre paréntesis el término técnico
original cuando ayuda a la trazabilidad.

# 2. Glosario

## Agente

- **Término canónico:** Agente
- **Significado:** Una instancia desplegada del bot (un clon del
  repositorio con su propio token de Telegram, configuración y
  personalidad).
- **Término mostrado al usuario:** El nombre configurado en `AGENT_NAME`
  (por defecto «Assistant»), usado por el propio bot al saludar
  (`FUN-CONVERSACION-001`).
- **Sinónimos encontrados:** «bot», «asistente».
- **Términos técnicos relacionados:** `AGENT_NAME`, `{{AGENT_NAME}}`.
- **Uso recomendado en documentación:** «el agente» para la instancia
  desplegada; «el asistente» para el papel conversacional que desempeña.
- **Notas:** NONE

## Conversación

- **Término canónico:** Conversación
- **Significado:** El intercambio de mensajes entre un usuario de Telegram y
  el agente dentro de un mismo chat, junto con su historial y resumen
  asociados (`ENT-CONVERSACION`).
- **Término mostrado al usuario:** No tiene una etiqueta visible propia; es
  implícita al propio chat de Telegram.
- **Sinónimos encontrados:** «chat», «historial».
- **Términos técnicos relacionados:** `chat_id`, `histories`, `summaries`.
- **Uso recomendado en documentación:** «conversación» para el concepto
  funcional; «chat de Telegram» cuando se quiera enfatizar el canal.
- **Notas:** NONE

## Historial de conversación

- **Término canónico:** Historial de conversación
- **Significado:** Lista ordenada de mensajes (usuario/asistente) de un chat,
  mantenida en memoria del proceso y acotada por un presupuesto de tokens.
- **Término mostrado al usuario:** No visible directamente.
- **Sinónimos encontrados:** «history» (código).
- **Términos técnicos relacionados:** `MAX_HISTORY_TOKENS`,
  `_trim_to_token_budget`.
- **Uso recomendado en documentación:** «historial de conversación».
- **Notas:** Se pierde al reiniciar el proceso (no hay persistencia); ver
  `RULE-CONVERSACION-004`.

## Compactación del historial

- **Término canónico:** Compactación del historial
- **Significado:** Sustitución de los mensajes más antiguos de una
  conversación por un resumen generado por el propio LLM, en lugar de
  descartarlos directamente, cuando el historial supera el presupuesto de
  tokens.
- **Término mostrado al usuario:** Aviso de Telegram: «One moment —
  compacting older conversation history to keep things running smoothly...»
- **Sinónimos encontrados:** «compaction» (código), «resumen».
- **Términos técnicos relacionados:** `_compact_history`, `_split_recent`,
  `RECENT_HISTORY_TOKENS`.
- **Uso recomendado en documentación:** «compactación del historial».
- **Notas:** Ver `AUTO-CONVERSACION-002`.

## Presupuesto de tokens

- **Término canónico:** Presupuesto de tokens
- **Significado:** Límite aproximado (estimado a ~4 caracteres por token,
  no un conteo exacto) de cuánta conversación se envía al modelo en cada
  mensaje, para no exceder la ventana de contexto del modelo.
- **Término mostrado al usuario:** No visible directamente.
- **Sinónimos encontrados:** «token budget».
- **Términos técnicos relacionados:** `MAX_HISTORY_TOKENS`,
  `RECENT_HISTORY_TOKENS`, `CHARS_PER_TOKEN_ESTIMATE`.
- **Uso recomendado en documentación:** «presupuesto de tokens».
- **Notas:** NONE

## Nota de voz

- **Término canónico:** Nota de voz
- **Significado:** Mensaje de audio enviado por Telegram (nota de voz o
  archivo de audio) que el bot transcribe a texto antes de tratarlo como un
  mensaje más de la conversación.
- **Término mostrado al usuario:** «voice message» (dentro del prefijo de
  transcripción, en inglés en el código actual).
- **Sinónimos encontrados:** «voice note», «audio».
- **Términos técnicos relacionados:** `VOICE_TRANSCRIPTION_PREFIX`,
  `handle_voice`.
- **Uso recomendado en documentación:** «nota de voz».
- **Notas:** El prefijo `[Voice message, transcribed by Whisper]:` se
  antepone siempre al texto transcrito antes de añadirlo al historial; ver
  `RULE-VOZ-001`.

## Backend LLM

- **Término canónico:** Backend LLM
- **Significado:** El proveedor de generación de texto usado por el agente:
  `ollama` (modelo local, contenedor propio) o `cloud` (cualquier API
  compatible con `/chat/completions` de OpenAI).
- **Término mostrado al usuario:** No visible directamente.
- **Sinónimos encontrados:** «LLM_BACKEND», «motor de IA».
- **Términos técnicos relacionados:** `OllamaClient`, `CloudClient`,
  `build_llm_client`.
- **Uso recomendado en documentación:** «backend LLM».
- **Notas:** NONE

## Herramienta

- **Término canónico:** Herramienta
- **Significado:** Capacidad adicional, catalogada de forma independiente de
  cualquier agente concreto, que el modelo puede invocar durante la
  generación de una respuesta (p. ej. búsqueda web). Ningún agente la tiene
  habilitada por defecto.
- **Término mostrado al usuario:** No visible directamente; el usuario sólo
  percibe el resultado incorporado a la respuesta del asistente.
- **Sinónimos encontrados:** «tool».
- **Términos técnicos relacionados:** `Tool`, `AVAILABLE_TOOLS`,
  `ENABLED_TOOLS`, `resolve_tools`.
- **Uso recomendado en documentación:** «herramienta».
- **Notas:** Ver `ENT-HERRAMIENTA` en `mod-herramientas.md`.

## Precalentamiento del modelo

- **Término canónico:** Precalentamiento del modelo
- **Significado:** Llamada de arranque, sin intervención del usuario, que
  carga el modelo Ollama en memoria/VRAM al iniciar el bot, para que la
  primera respuesta real no pague ese coste.
- **Término mostrado al usuario:** No visible directamente.
- **Sinónimos encontrados:** «warm-up».
- **Términos técnicos relacionados:** `_warm_up_ollama`, `OLLAMA_KEEP_ALIVE`.
- **Uso recomendado en documentación:** «precalentamiento del modelo».
- **Notas:** Sólo se ejecuta cuando `LLM_BACKEND=ollama`; ver
  `AUTO-MOTORIA-001`.

## Prompt de sistema

- **Término canónico:** Prompt de sistema
- **Significado:** Instrucciones base que definen la personalidad y el
  comportamiento del agente, a las que se añade dinámicamente en cada
  mensaje la fecha/hora actual y, si existe, el resumen de historial
  compactado.
- **Término mostrado al usuario:** No visible directamente.
- **Sinónimos encontrados:** «system prompt», «system_prompt.txt».
- **Términos técnicos relacionados:** `SYSTEM_PROMPT_FILE`,
  `_build_system_message`, `{{AGENT_NAME}}`.
- **Uso recomendado en documentación:** «prompt de sistema».
- **Notas:** El contenido personalizado del fichero queda fuera de este
  scope (ver `scopes/bot/README.md`); se documenta el mecanismo, no el
  contenido.

## Lista blanca de usuarios

- **Término canónico:** Lista blanca de usuarios
- **Significado:** Conjunto configurable de identificadores numéricos de
  Telegram autorizados a usar el bot; si está vacía, cualquiera que
  encuentre el bot puede usarlo.
- **Término mostrado al usuario:** «You don't have access to this bot.»
  (cuando se deniega el acceso).
- **Sinónimos encontrados:** «whitelist», `ALLOWED_USER_IDS`.
- **Términos técnicos relacionados:** `_is_allowed`, `_has_access`.
- **Uso recomendado en documentación:** «lista blanca de usuarios».
- **Notas:** Ver `RULE-CONVERSACION-001`.

# 3. Validación del fichero

- Front matter completo y conforme a la sección 6 del schema.
- Todos los términos incluidos son referenciados desde al menos un fichero
  de módulo o desde `_roles.md`.
- Se ha priorizado, cuando existe, el texto realmente mostrado al usuario
  (mensajes de Telegram del propio bot) frente a nombres internos del
  código.
