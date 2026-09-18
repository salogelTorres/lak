---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: INDEX
module-id: NOT_APPLICABLE
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram

# 1. Metainformación

## Resumen de generación

Primera generación completa del CFS del scope `bot`. Se ha analizado el
código en ejecución bajo `app/` (Telegram, motor de IA, herramientas, voz),
su configuración (`.env.example`, `app/config.py`), la plantilla de prompt
de sistema y `docker-compose.yml`, cruzando esta información con la suite de
tests (`tests/`) para confirmar comportamiento. No existía CFS previo para
este scope.

## Inventario de ficheros

| Fichero | Part | Módulo | generated-at | source-commit | generation-status |
|---|---|---|---|---|---|
| `_index.md` | INDEX | NOT_APPLICABLE | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `_roles.md` | ROLES | NOT_APPLICABLE | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `_glossary.md` | GLOSSARY | NOT_APPLICABLE | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `_relations.md` | RELATIONS | NOT_APPLICABLE | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `mod-conversacion.md` | MODULE | `MOD-CONVERSACION` | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `mod-voz.md` | MODULE | `MOD-VOZ` | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `mod-herramientas.md` | MODULE | `MOD-HERRAMIENTAS` | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |
| `mod-motor-ia.md` | MODULE | `MOD-MOTOR-IA` | 2026-09-18 | 25166ca4e6babcd070dea4e2d76030d024329fd8 | COMPLETE |

# 2. Scope y límites

## Scope

- **ID:** `bot`
- **Nombre:** Bot de Telegram
- **Descripción:** Comportamiento funcional en tiempo de ejecución de un bot
  de Telegram respaldado por un LLM (local vía Ollama o remoto vía una API
  compatible con OpenAI), incluyendo conversación, historial, voz y
  herramientas opcionales.
- **Evidence status:** `CONFIRMED`

## Incluye

- Conversación por Telegram (`/start`, mensajes de texto, control de acceso,
  historial de conversación, recorte por presupuesto de tokens,
  compactación del historial antiguo).
- Transcripción de notas de voz/audio y su incorporación a la conversación.
- Motor de IA: selección de backend LLM, llamada al modelo, precalentamiento
  de Ollama, bucle de uso de herramientas.
- Sistema de herramientas opcionales invocables por el modelo durante la
  conversación (catálogo y herramienta de búsqueda web incluida).
- Configuración funcional que determina el comportamiento anterior
  (variables de entorno leídas por `app/config.py`).

## Excluye

- `setup.py` y `update.py` (asistente de onboarding y actualización del
  clon del template) — herramientas de desarrollo/despliegue, no
  comportamiento del bot en ejecución.
- El contenido concreto de la personalidad de un agente (texto libre en
  `system_prompt.txt`, propio de cada instancia desplegada).
- Detalle interno de las librerías de terceros usadas (`python-telegram-bot`,
  `faster-whisper`, `httpx`) más allá de su uso funcional por el bot.

Ver `scopes/bot/README.md` para el detalle completo de la delimitación.

## Dependencias con otros scopes

NONE — no existen actualmente otros scopes CFS en este repositorio.

## Límites ambiguos

- NONE

# 3. Cobertura global

## Resumen

- **Backend (lógica del bot en `app/`):** COMPLETE
- **Frontend / UI:** NOT_APPLICABLE — la interfaz es el propio cliente de
  Telegram; no existe frontend propio del repositorio.
- **Base de datos:** NOT_APPLICABLE — no existe persistencia; el historial
  de conversación es en memoria de proceso (ver `RULE-CONVERSACION-004` en
  `mod-conversacion.md`).
- **Documentación funcional:** COMPLETE (`README.md`, `CLAUDE.md`,
  `.env.example`, `app/prompts/system_prompt.txt.example`).
- **Planes / especificaciones:** NOT_APPLICABLE — no se han localizado
  planes de desarrollo independientes; `CLAUDE.md` documenta racionales de
  diseño ya implementados.
- **Integraciones relevantes:** COMPLETE (API de Telegram vía
  `python-telegram-bot`, Ollama, API compatible con OpenAI, DuckDuckGo HTML).

### Limitaciones

- No se ha ejecutado el bot real contra Telegram/Ollama/una API cloud; el
  comportamiento se ha confirmado mediante lectura de código y la suite de
  tests (que mockea toda E/S), no mediante observación en vivo.

## Fuentes no disponibles o no analizadas

NONE

# 4. Visión funcional global

## Propósito

Ofrecer, por cada clon del template, un asistente conversacional accesible
por Telegram y respaldado por un LLM (local o remoto), con historial de
conversación por chat, soporte de notas de voz y capacidad opcional de usar
herramientas (como búsqueda web) durante la conversación.

## Usuarios principales

- `ROL-USUARIO`
- `ROL-OPERADOR`

## Módulos

| ID | Nombre | Objetivo | Roles principales | Entidades principales | Estado |
|---|---|---|---|---|---|
| `MOD-CONVERSACION` | Conversación | Gestionar el intercambio de mensajes de texto por Telegram, el acceso y el historial de la conversación | `ROL-USUARIO`, `ROL-OPERADOR` | `ENT-CONVERSACION`, `ENT-MENSAJE` | `IMPLEMENTED` |
| `MOD-VOZ` | Mensajes de voz | Transcribir notas de voz/audio de Telegram e incorporarlas a la conversación | `ROL-USUARIO` | NONE | `IMPLEMENTED` |
| `MOD-HERRAMIENTAS` | Herramientas | Catalogar y ejecutar capacidades adicionales que el modelo puede invocar durante la conversación | `ROL-OPERADOR` | `ENT-HERRAMIENTA` | `IMPLEMENTED` |
| `MOD-MOTOR-IA` | Motor de IA | Seleccionar y llamar al backend LLM configurado, y coordinar el uso de herramientas | `ROL-OPERADOR` | NONE | `IMPLEMENTED` |

## Relaciones principales

- `MOD-CONVERSACION` → `MOD-MOTOR-IA`: la conversación delega en el motor de
  IA la generación de cada respuesta (`REL-CONVERSACION-MOTORIA`).
- `MOD-CONVERSACION` → `MOD-VOZ`: los mensajes de voz se transcriben antes de
  incorporarse a la conversación (`REL-CONVERSACION-VOZ`).
- `MOD-MOTOR-IA` → `MOD-HERRAMIENTAS`: el motor de IA ejecuta las
  herramientas que el modelo decide invocar (`REL-MOTORIA-HERRAMIENTAS`).

## Flujos principales

- `FLOW-GLOBAL-001`: envío de un mensaje de texto y generación de la
  respuesta (con recorte/compactación de historial y uso opcional de
  herramientas).
- `FLOW-GLOBAL-002`: envío de una nota de voz y generación de la respuesta.

# 5. Módulos pendientes de extracción

NONE — los cuatro módulos identificados están extraídos.

# 6. Entidades sin módulo propietario claro

NONE

# 7. Incertidumbres globales

## Información inferida

NONE — las incertidumbres identificadas son específicas de cada módulo (ver
sección 10 de cada `mod-*.md`) o se documentan a continuación.

## Información desconocida

### UNK-GLOBAL-001

- **Elemento:** Scope global — comportamiento en ejecución real
- **Información no determinada:** No se ha verificado el comportamiento
  contra una instancia real de Telegram, Ollama o una API cloud; toda la
  evidencia proviene de lectura de código y de la suite de tests (que
  mockea `httpx`, `input()` y `subprocess`).
- **Fuentes revisadas:** `app/*.py`, `tests/*.py`
- **Qué sería necesario para resolverlo:** Ejecutar `docker compose up` con
  credenciales reales y observar el comportamiento end-to-end.
- **Impacto documental:** LOW — el comportamiento está confirmado a nivel de
  código y test unitario/de integración mockeada, que es coherente y
  suficientemente explícito.

## Conflictos

NONE

# 8. Validación de scope

## Resultado

- Existen los cuatro ficheros obligatorios (`_index.md`, `_roles.md`,
  `_glossary.md`, `_relations.md`) y un fichero por cada módulo del
  inventario, con nombre conforme a la sección 7.1 del schema.
- No se han detectado IDs duplicados dentro del scope.
- Toda referencia cruzada (`FUN-`, `RULE-`, `AUTO-`, `ENT-`, `STA-`, `REL-`,
  `FLOW-`, `ROL-`, `UI-`) resuelve a un ID definido en algún fichero del
  scope.
- No existen módulos con stub: los cuatro módulos identificados en la
  pasada de inventario quedaron extraídos en la misma generación.
- No se han utilizado planes o documentación de intención como evidencia de
  implementación actual: toda funcionalidad `IMPLEMENTED` tiene evidencia en
  código y, cuando ha sido posible, en tests.
- No existe `tools/lint-cfs.mjs` en este repositorio (no se distribuye bajo
  `.docs/cfs-canonical-functional-source/`), por lo que la validación
  estructural se ha realizado manualmente contra la sección 27 del schema,
  sin verificación mecánica.

## Limitaciones finales

- Validación estructural manual (sin lint mecánico disponible en este
  repositorio) — ver `UNK-GLOBAL-001` para la limitación sobre verificación
  en ejecución real.
