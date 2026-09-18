---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: MODULE
module-id: MOD-CONVERSACION
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Módulo Conversación

# 1. Metainformación

Módulo extraído a partir de `app/bot.py` (excepto la parte de transcripción
de voz, ver `MOD-VOZ`), `app/config.py` y `.env.example`.

# 2. Módulo

## MOD-CONVERSACION — Conversación

- **Nombre:** Conversación
- **Objetivo:** Gestionar el intercambio de mensajes de texto entre un
  usuario de Telegram y el asistente: control de acceso, historial por
  chat, y preparación del contexto (recorte y compactación) antes de cada
  llamada al motor de IA.
- **Responsabilidad funcional:** Todo lo relativo al ciclo de vida de una
  conversación de Telegram (inicio, mensajes, historial, acceso) pertenece
  a este módulo. La generación de la respuesta en sí (qué backend LLM
  responde y cómo) pertenece a `MOD-MOTOR-IA`; la transcripción de audio
  pertenece a `MOD-VOZ`.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Resumen funcional

El usuario inicia la conversación con `/start` y a partir de ahí envía
mensajes de texto (o notas de voz, ver `MOD-VOZ`). Cada mensaje entrante se
valida contra la lista blanca de usuarios, se añade al historial en memoria
del chat, y — si el historial supera el presupuesto de tokens configurado —
se compacta la parte más antigua en un resumen antes de recortar el
historial al presupuesto y delegar la generación de la respuesta en
`MOD-MOTOR-IA`. La respuesta final se añade también al historial y se envía
al usuario.

### Roles

- `ROL-USUARIO`
- `ROL-OPERADOR`

### Entidades principales

- `ENT-CONVERSACION`
- `ENT-MENSAJE`

### Interfaces principales

- `UI-CONVERSACION-CHAT`

### Funcionalidades

- `FUN-CONVERSACION-001`
- `FUN-CONVERSACION-002`

### Flujos internos

- `FLOW-CONVERSACION-001`

### Reglas de negocio

- `RULE-CONVERSACION-001`
- `RULE-CONVERSACION-002`
- `RULE-CONVERSACION-003`
- `RULE-CONVERSACION-004`

### Automatismos

- `AUTO-CONVERSACION-001`
- `AUTO-CONVERSACION-002`
- `AUTO-CONVERSACION-003`
- `AUTO-CONVERSACION-004`

### Módulos relacionados

- `MOD-MOTOR-IA`
- `MOD-VOZ`

### Fuentes principales

- `SRC-CONVERSACION-CODE-001`
- `SRC-CONVERSACION-CODE-002`

# 3. Fuentes y cobertura del módulo

## Fuentes analizadas

### SRC-CONVERSACION-CODE-001

- **Tipo:** CODE
- **Ubicación:** `app/bot.py`
- **Descripción:** Handlers de Telegram (`start`, `handle_message`), control
  de acceso, historial, recorte/compactación, construcción del mensaje de
  sistema.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-CONVERSACION-CODE-002

- **Tipo:** CODE
- **Ubicación:** `app/config.py`
- **Descripción:** Carga de configuración (`Config.load`): token, lista
  blanca, nombre del agente, prompt de sistema, zona horaria, presupuestos
  de historial.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-CONVERSACION-DOC-001

- **Tipo:** DOCUMENT
- **Ubicación:** `.env.example`
- **Descripción:** Documentación de las variables de entorno relevantes
  (`ALLOWED_USER_IDS`, `AGENT_NAME`, `TZ`, `MAX_HISTORY_TOKENS`,
  `RECENT_HISTORY_TOKENS`).
- **Fecha o versión:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-CONVERSACION-TEST-001

- **Tipo:** TEST
- **Ubicación:** `tests/test_bot.py`
- **Descripción:** Confirma el comportamiento de acceso, recorte,
  compactación y manejo de errores de la llamada al LLM.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

## Fuentes no disponibles o no analizadas

NONE

## Cobertura

- **Backend:** COMPLETE
- **Frontend:** NOT_APPLICABLE — la interfaz es el cliente de Telegram.
- **Base de datos:** NOT_APPLICABLE — historial en memoria de proceso.
- **Documentación funcional:** COMPLETE
- **Planes / especificaciones:** NOT_APPLICABLE
- **Integraciones relevantes:** COMPLETE (API de Telegram vía
  `python-telegram-bot`)

### Limitaciones

- NONE

# 4. Navegación e interfaces de usuario

## UI-CONVERSACION-CHAT

- **Nombre visible:** Chat con el bot (nombre de usuario de Telegram del
  agente, definido en Telegram, fuera de este repositorio)
- **Tipo:** `OTHER` — chat 1:1 de Telegram; no es una interfaz gráfica propia
  del repositorio.
- **Módulo:** `MOD-CONVERSACION`
- **Ruta funcional:** Chat directo con el bot en Telegram.
- **Ruta técnica:** `UNKNOWN` — depende del nombre de usuario de Telegram
  asignado al bot mediante BotFather, fuera del código de este repositorio.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Cómo se accede

1. El usuario busca el bot en Telegram por su nombre de usuario (asignado al
   crear el bot en BotFather, fuera de este scope) y abre el chat.
2. Envía `/start` o directamente un mensaje de texto o una nota de voz.

### Roles con acceso

- `ROL-USUARIO`

### Propósito

Único punto de entrada del usuario a toda la funcionalidad conversacional
del bot: envío de mensajes, recepción de respuestas, y (indirectamente)
notas de voz.

### Información mostrada

- Respuestas de texto del asistente.
- Mensaje de bienvenida al usar `/start`.
- Mensajes de error o aviso del propio bot (acceso denegado, fallo del LLM,
  aviso de compactación, fallo de transcripción).
- Indicador nativo de Telegram «escribiendo…» mientras se genera la
  respuesta.

### Acciones disponibles

- `FUN-CONVERSACION-001`
- `FUN-CONVERSACION-002`
- `FUN-VOZ-001` (ver `mod-voz.md`)

### Filtros / búsquedas relevantes

- NONE

### Estados o condiciones que alteran la interfaz

- Si el usuario no está en la lista blanca (`RULE-CONVERSACION-001`), toda
  interacción responde únicamente «You don't have access to this bot.»

### Superficies relacionadas

- NONE

### Fuentes

- `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `build_application()`

# 5. Entidades funcionales

## ENT-CONVERSACION

- **Nombre:** Conversación
- **Descripción:** Estado conversacional de un chat de Telegram: su
  historial de mensajes y, si existe, su resumen compactado.
- **Módulo propietario:** `MOD-CONVERSACION`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Significado funcional

Representa, para cada `chat_id` de Telegram, todo lo que el bot recuerda de
esa conversación: los mensajes recientes (verbatim, dentro del presupuesto
de tokens) y un resumen de lo anterior a eso, si el historial ha llegado a
compactarse alguna vez.

### Campos funcionalmente relevantes

| Campo | Nombre visible | Significado | Obligatorio | Editable | Restricciones |
|---|---|---|---|---|---|
| `chat_id` | (implícito, no visible) | Identificador del chat de Telegram | YES | NO | Clave de acceso al historial y al resumen de esa conversación |
| historial de mensajes | (no visible) | Secuencia de mensajes usuario/asistente/sistema | YES | NO (se gestiona automáticamente) | Acotado por `MAX_HISTORY_TOKENS` |
| resumen compactado | (no visible) | Texto que condensa los mensajes más antiguos ya retirados del historial verbatim | NO | NO (se gestiona automáticamente) | Se genera vía `MOD-MOTOR-IA`; puede no existir todavía |

### Roles relacionados

- `ROL-USUARIO`: genera y consume el contenido de su propia conversación al
  enviar y recibir mensajes.

### Creación

- **Quién puede crear:** Se crea implícitamente en el primer mensaje de un
  `chat_id` nuevo (no existe una acción explícita de «crear conversación»).
- **Condiciones:** El usuario debe estar autorizado
  (`RULE-CONVERSACION-001`).
- **Funcionalidad:** `FUN-CONVERSACION-001`, `FUN-CONVERSACION-002`

### Modificación

- **Quién puede modificar:** Se modifica automáticamente con cada mensaje
  entrante o saliente de ese chat, y con cada compactación.
- **Condiciones:** NOT_APPLICABLE — no existe una operación manual de
  edición del historial.

### Eliminación

- **Permitida:** NO — no existe ninguna funcionalidad para que un usuario
  borre su historial; sólo desaparece al reiniciarse el proceso del bot
  (`RULE-CONVERSACION-004`).
- **Condiciones:** NOT_APPLICABLE
- **Funcionalidad:** NONE

### Estados

NONE — `ENT-CONVERSACION` no tiene una máquina de estados funcional propia;
su contenido varía de forma continua (crece, se recorta, se compacta) sin
estados discretos con significado de negocio.

### Relaciones

- Composición 1:N con `ENT-MENSAJE` (una conversación contiene sus
  mensajes). No se ha definido con un ID `REL-` independiente: se trata de
  la propia estructura del historial, sin comportamiento adicional que
  documentar más allá de lo ya cubierto en `AUTO-CONVERSACION-001` y
  `AUTO-CONVERSACION-002`.

### Reglas relacionadas

- `RULE-CONVERSACION-002`
- `RULE-CONVERSACION-003`
- `RULE-CONVERSACION-004`

### Fuentes

- `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `build_application()`
  (`histories`, `summaries`)

## ENT-MENSAJE

- **Nombre:** Mensaje
- **Descripción:** Un elemento individual del historial de una conversación:
  el mensaje de sistema, un mensaje del usuario, un mensaje del asistente, o
  (internamente, sólo cuando hay herramientas) un mensaje de herramienta.
- **Módulo propietario:** `MOD-CONVERSACION`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Significado funcional

Cada turno de la conversación (lo que escribe el usuario, lo que responde el
asistente, y el propio prompt de sistema recalculado en cada turno) se
representa como un mensaje con un rol y un contenido de texto.

### Campos funcionalmente relevantes

| Campo | Nombre visible | Significado | Obligatorio | Editable | Restricciones |
|---|---|---|---|---|---|
| rol | (no visible) | `system` / `user` / `assistant` (y `tool`, ver `mod-herramientas.md`) | YES | NO | Determina cómo lo interpreta el modelo |
| contenido | El propio texto enviado o recibido | El texto del mensaje | YES | NO | Los mensajes de voz llevan el prefijo `VOICE_TRANSCRIPTION_PREFIX` (ver `mod-voz.md`) |

### Roles relacionados

- `ROL-USUARIO`: autor de los mensajes de rol `user`.

### Creación

- **Quién puede crear:** Se crea automáticamente por cada mensaje entrante
  del usuario y por cada respuesta generada por `MOD-MOTOR-IA`; el mensaje
  de sistema se recalcula en cada turno (`AUTO-CONVERSACION-003`).
- **Condiciones:** El usuario debe estar autorizado.
- **Funcionalidad:** `FUN-CONVERSACION-002`

### Modificación

- **Quién puede modificar:** NOT_APPLICABLE — un mensaje ya creado no se
  edita; sólo puede dejar de enviarse al modelo si es recortado
  (`AUTO-CONVERSACION-001`) o queda absorbido por una compactación
  (`AUTO-CONVERSACION-002`).

### Eliminación

- **Permitida:** CONDITIONAL — un mensaje puede quedar fuera del historial
  enviado al modelo (recorte) o ser sustituido por un resumen
  (compactación), pero no existe una eliminación directa iniciada por el
  usuario.
- **Condiciones:** El historial total supera `MAX_HISTORY_TOKENS`.
- **Funcionalidad:** `AUTO-CONVERSACION-001`, `AUTO-CONVERSACION-002`

### Estados

NONE

### Relaciones

- Pertenece a `ENT-CONVERSACION` (ver relación descrita en dicha entidad).

### Reglas relacionadas

- `RULE-CONVERSACION-002`

### Fuentes

- `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `_reply_to()`

# 6. Funcionalidades

## FUN-CONVERSACION-001 — Iniciar conversación con el bot

- **Nombre:** Iniciar conversación con el bot
- **Módulo:** `MOD-CONVERSACION`
- **Descripción:** El usuario envía el comando `/start` y el bot responde
  con un saludo que incluye el nombre configurado del agente.
- **User-facing:** YES
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Roles autorizados

- `ROL-USUARIO`

#### Interfaces de acceso

- `UI-CONVERSACION-CHAT`

#### Entidades implicadas

- NONE — `/start` no crea entradas en `ENT-CONVERSACION`; es una respuesta
  fija que no pasa por el historial ni por `MOD-MOTOR-IA`.

#### Precondiciones

- NONE — a diferencia del resto de funcionalidades, `/start` no comprueba la
  lista blanca de usuarios (`RULE-CONVERSACION-001` no se aplica a este
  handler).

#### Trigger / inicio

El usuario envía el comando `/start` en el chat de Telegram con el bot.

#### Acción funcional

El bot responde directamente con un mensaje de saludo fijo, sin llamar al
backend LLM.

#### Datos requeridos

- NONE

#### Datos opcionales

- NONE

#### Resultado esperado

El usuario recibe el mensaje «Hi, I'm {AGENT_NAME}. How can I help?» (con
`{AGENT_NAME}` sustituido por el nombre configurado del agente).

#### Cambios de estado

- `NOT_APPLICABLE`

#### Datos creados o modificados

- NONE

#### Efectos secundarios

- `NONE`

#### Módulos afectados

- `NONE`

#### Reglas de negocio

- NONE

#### Automatismos relacionados

- NONE

#### Restricciones

- NONE

#### Excepciones y errores funcionales

- NONE — no se ha identificado ningún camino de error para este comando.

#### Resultado visible para el usuario

Mensaje de saludo del bot en el chat.

#### Funcionalidades relacionadas

- `FUN-CONVERSACION-002`

#### Fuentes

- `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `start()`

## FUN-CONVERSACION-002 — Enviar un mensaje de texto y recibir respuesta

- **Nombre:** Enviar un mensaje de texto y recibir respuesta
- **Módulo:** `MOD-CONVERSACION`
- **Descripción:** El usuario envía un mensaje de texto (que no sea un
  comando) y recibe la respuesta generada por el asistente, teniendo en
  cuenta el historial de la conversación.
- **User-facing:** YES
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Roles autorizados

- `ROL-USUARIO`

#### Interfaces de acceso

- `UI-CONVERSACION-CHAT`

#### Entidades implicadas

- `ENT-CONVERSACION`
- `ENT-MENSAJE`

#### Precondiciones

- El usuario debe estar en la lista blanca de usuarios autorizados, o la
  lista debe estar vacía (`RULE-CONVERSACION-001`).
- El mensaje debe ser texto y no un comando (los comandos se gestionan por
  handlers separados, p. ej. `/start`).

#### Trigger / inicio

El usuario envía un mensaje de texto en el chat con el bot.

#### Acción funcional

El bot añade el mensaje al historial del chat, muestra el indicador de
«escribiendo…», compacta el historial antiguo si corresponde
(`AUTO-CONVERSACION-002`), reconstruye el mensaje de sistema con la
fecha/hora actual (`AUTO-CONVERSACION-003`), recorta el historial al
presupuesto configurado (`AUTO-CONVERSACION-001`), y delega en
`MOD-MOTOR-IA` (`FUN-MOTORIA-001`) la generación de la respuesta —
pasándole también las herramientas habilitadas, si las hay.

#### Datos requeridos

- Texto del mensaje.

#### Datos opcionales

- NONE

#### Resultado esperado

El usuario recibe, en el mismo chat, la respuesta de texto generada por el
modelo.

#### Cambios de estado

- `NOT_APPLICABLE`

#### Datos creados o modificados

- Se añade un mensaje de usuario y, si la llamada al LLM tiene éxito, un
  mensaje de asistente al historial de `ENT-CONVERSACION` del chat.
- El resumen de la conversación puede actualizarse si se dispara una
  compactación (`AUTO-CONVERSACION-002`).

#### Efectos secundarios

- Si el historial supera el presupuesto de tokens, se envía primero un
  aviso de Telegram indicando que se está compactando el historial.

#### Módulos afectados

- `MOD-MOTOR-IA`

#### Reglas de negocio

- `RULE-CONVERSACION-001`
- `RULE-CONVERSACION-002`
- `RULE-CONVERSACION-003`

#### Automatismos relacionados

- `AUTO-CONVERSACION-001`
- `AUTO-CONVERSACION-002`
- `AUTO-CONVERSACION-003`
- `AUTO-CONVERSACION-004`

#### Restricciones

- La respuesta depende de la disponibilidad del backend LLM configurado
  (`MOD-MOTOR-IA`); si no está disponible, ver excepciones.

#### Excepciones y errores funcionales

- El usuario no tiene acceso: se responde «You don't have access to this
  bot.» y no se procesa el mensaje.
- Falla la llamada al LLM (excepción de cualquier tipo): se responde
  «Something went wrong talking to the model. Please try again.» y no se
  añade una respuesta de asistente al historial (el mensaje del usuario sí
  queda registrado).
- Falla la compactación del historial: se continúa sin ella y se aplica
  únicamente el recorte por presupuesto como red de seguridad (no se
  informa de este fallo concreto al usuario, sólo se registra internamente).

#### Resultado visible para el usuario

Respuesta de texto del asistente en el chat; opcionalmente, antes de esa
respuesta, el aviso de compactación del historial.

#### Funcionalidades relacionadas

- `FUN-CONVERSACION-001`
- `FUN-VOZ-001`
- `FUN-MOTORIA-001`

#### Fuentes

- `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `handle_message()`,
  `_reply_to()`
- `SRC-CONVERSACION-TEST-001` — `tests/test_bot.py`

# 7. Reglas de negocio

## RULE-CONVERSACION-001

- **Nombre:** Control de acceso por lista blanca de usuarios
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** Sólo los usuarios de Telegram cuyo ID numérico esté en
  `ALLOWED_USER_IDS` pueden usar el bot; si la lista está vacía, cualquier
  usuario que encuentre el bot puede usarlo.
- **Condición:** `ALLOWED_USER_IDS` no está vacía y el ID del usuario no está
  en ella.
- **Consecuencia:** Se responde «You don't have access to this bot.» y no se
  procesa el mensaje (ni de texto ni de voz).
- **Roles afectados:** `ROL-USUARIO` (restringido), `ROL-OPERADOR` (define la
  lista)
- **Entidades afectadas:** `ENT-CONVERSACION`
- **Funcionalidades afectadas:** `FUN-CONVERSACION-002`, `FUN-VOZ-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `_is_allowed()`,
  `_has_access()`

## RULE-CONVERSACION-002

- **Nombre:** El mensaje más reciente siempre se conserva
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** Al recortar el historial por presupuesto de tokens
  (`AUTO-CONVERSACION-001`), el mensaje de sistema y el mensaje más reciente
  se conservan siempre, incluso si el mensaje más reciente por sí solo
  supera el presupuesto configurado.
- **Condición:** El recorte del historial se activa.
- **Consecuencia:** Es preferible exceder ligeramente el presupuesto de
  tokens antes que descartar silenciosamente la pregunta que el usuario
  acaba de hacer.
- **Roles afectados:** `ROL-USUARIO`
- **Entidades afectadas:** `ENT-CONVERSACION`, `ENT-MENSAJE`
- **Funcionalidades afectadas:** `FUN-CONVERSACION-002`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` →
  `_trim_to_token_budget()`

## RULE-CONVERSACION-003

- **Nombre:** `RECENT_HISTORY_TOKENS` debe ser menor que `MAX_HISTORY_TOKENS`
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** El presupuesto de mensajes recientes que se conservan
  siempre en texto (sin compactar) debe ser menor que el presupuesto total
  de historial.
- **Condición:** Configuración de `RECENT_HISTORY_TOKENS` y
  `MAX_HISTORY_TOKENS` en `.env`.
- **Consecuencia documentada:** Si no se respeta, el comportamiento no está
  definido (no se ha localizado validación cruzada entre ambos valores en
  `app/config.py`: sólo se valida que cada uno sea un número entero).
- **Roles afectados:** `ROL-OPERADOR`
- **Entidades afectadas:** `ENT-CONVERSACION`
- **Funcionalidades afectadas:** `FUN-CONVERSACION-002`
- **Implementation status:** `PARTIAL`
- **Evidence status:** `CONFIRMED` — la exigencia está documentada
  explícitamente en `.env.example`; ver `PARTIAL-CONVERSACION-001` sobre su
  falta de validación en código.
- **Fuentes:** `SRC-CONVERSACION-DOC-001` — `.env.example`
  (`RECENT_HISTORY_TOKENS`)

## RULE-CONVERSACION-004

- **Nombre:** El historial de conversación no persiste
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** El historial y el resumen de cada chat se mantienen
  únicamente en memoria del proceso (diccionarios `histories`/`summaries`
  cerrados sobre `build_application`); no existe base de datos ni fichero de
  persistencia.
- **Condición:** El proceso del bot se reinicia (despliegue, caída,
  `docker compose restart`, etc.).
- **Consecuencia:** Todo el historial y los resúmenes de todas las
  conversaciones se pierden; la siguiente conversación de cada chat empieza
  desde cero.
- **Roles afectados:** `ROL-USUARIO`
- **Entidades afectadas:** `ENT-CONVERSACION`
- **Funcionalidades afectadas:** `FUN-CONVERSACION-002`, `FUN-VOZ-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` →
  `build_application()`

# 8. Automatismos

## AUTO-CONVERSACION-001

- **Nombre:** Recorte del historial por presupuesto de tokens
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** Antes de cada llamada al LLM, se recorta el historial
  para que quepa dentro de `MAX_HISTORY_TOKENS`, descartando primero los
  mensajes más antiguos (después de cualquier compactación), conservando
  siempre el mensaje de sistema y el más reciente.
- **Trigger:** Cada mensaje entrante (texto o voz), justo antes de llamar al
  motor de IA.
- **Condiciones:** El historial total (estimado a ~4 caracteres por token)
  excede `MAX_HISTORY_TOKENS`.
- **Acciones ejecutadas:** Se eliminan mensajes antiguos del historial que
  se va a enviar al modelo, de más antiguo a más reciente, hasta encajar en
  el presupuesto.
- **Entidades afectadas:** `ENT-CONVERSACION`, `ENT-MENSAJE`
- **Cambios de estado:** `NOT_APPLICABLE`
- **Módulos afectados:** `NONE`
- **Resultado visible para el usuario:** Ninguno directamente; efecto
  indirecto en que el modelo puede «no recordar» mensajes muy antiguos que
  no llegaron a compactarse.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` →
  `_trim_to_token_budget()`

## AUTO-CONVERSACION-002

- **Nombre:** Compactación del historial antiguo en un resumen
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** Cuando el historial total supera `MAX_HISTORY_TOKENS`, en
  lugar de descartar directamente los mensajes más antiguos, se separan en
  un bloque «antiguo» (todo lo anterior a los últimos
  `RECENT_HISTORY_TOKENS`) y se piden al backend LLM configurado que los
  condense (junto con el resumen ya existente, si lo hay) en un nuevo
  resumen breve.
- **Trigger:** El historial total supera `MAX_HISTORY_TOKENS` al procesar un
  mensaje entrante.
- **Condiciones:** El bloque de mensajes «antiguos» resultante de separar
  los últimos `RECENT_HISTORY_TOKENS` no está vacío.
- **Acciones ejecutadas:** Se envía primero un aviso de Telegram
  (`COMPACTING_NOTICE`); se llama al LLM con un prompt de sistema específico
  de compactación; el resumen devuelto sustituye al resumen anterior del
  chat y los mensajes «antiguos» se retiran del historial verbatim.
- **Entidades afectadas:** `ENT-CONVERSACION`, `ENT-MENSAJE`
- **Cambios de estado:** `NOT_APPLICABLE`
- **Módulos afectados:** `MOD-MOTOR-IA` (la compactación es en sí misma una
  llamada adicional al backend LLM)
- **Resultado visible para el usuario:** Mensaje «One moment — compacting
  older conversation history to keep things running smoothly...» antes de
  la respuesta normal.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` →
  `_compact_history()`, `_split_recent()`

## AUTO-CONVERSACION-003

- **Nombre:** Inserción de fecha/hora actual en el prompt de sistema
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** El mensaje de sistema se reconstruye en cada turno de
  conversación añadiendo la fecha y hora actuales (según la zona horaria
  `TZ` configurada) al prompt de sistema base, en lugar de fijarse una única
  vez al arrancar el proceso.
- **Trigger:** Cada mensaje entrante (texto o voz).
- **Condiciones:** NONE — ocurre siempre.
- **Acciones ejecutadas:** Se calcula la fecha/hora actual en la zona
  horaria configurada (con `UTC` como salvaguarda si `TZ` no es una zona
  IANA válida) y se añade como línea adicional al prompt de sistema, junto
  con el resumen compactado si existe.
- **Entidades afectadas:** `ENT-MENSAJE` (el mensaje de sistema)
- **Cambios de estado:** `NOT_APPLICABLE`
- **Módulos afectados:** `NONE`
- **Resultado visible para el usuario:** Indirecto — el modelo puede
  responder correctamente a preguntas sobre la fecha/hora actual.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` →
  `_build_system_message()`

## AUTO-CONVERSACION-004

- **Nombre:** Indicador de «escribiendo…» durante la generación de la
  respuesta
- **Módulo propietario:** `MOD-CONVERSACION`
- **Descripción:** Mientras dura la preparación del historial y la llamada
  al motor de IA, el bot reenvía periódicamente el indicador nativo de
  Telegram de «escribiendo…», ya que Telegram sólo lo muestra unos segundos
  por cada envío y una respuesta de un modelo local puede tardar mucho más.
- **Trigger:** Inicio del procesamiento de cualquier mensaje entrante (texto
  o voz, tras pasar el control de acceso).
- **Condiciones:** NONE
- **Acciones ejecutadas:** Se reenvía la acción `typing` cada pocos segundos
  en una tarea en segundo plano, cancelada en cuanto la respuesta está lista
  (o ha fallado).
- **Entidades afectadas:** NONE
- **Cambios de estado:** `NOT_APPLICABLE`
- **Módulos afectados:** `NONE`
- **Resultado visible para el usuario:** El indicador «escribiendo…» se
  mantiene visible en Telegram durante toda la espera.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `_keep_typing()`

# 9. Flujos internos

## FLOW-CONVERSACION-001 — Compactación del historial antiguo

- **Nombre:** Compactación del historial antiguo
- **Objetivo:** Condensar los mensajes más antiguos de una conversación en
  un resumen, para no perder contexto relevante al recortar el historial
  por presupuesto de tokens.
- **Módulo principal:** `MOD-CONVERSACION`
- **Módulos participantes:**
  - `MOD-CONVERSACION`
  - `MOD-MOTOR-IA`
- **Roles participantes:**
  - `ROL-USUARIO` (receptor del aviso; no interviene activamente)
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Punto de inicio

El historial total del chat (sin contar el mensaje de sistema) supera
`MAX_HISTORY_TOKENS` al procesar un mensaje entrante.

#### Precondiciones

- El historial dividido en «recientes» (últimos `RECENT_HISTORY_TOKENS`) y
  «antiguos» (el resto) tiene al menos un mensaje «antiguo».

#### Secuencia principal

1. Se separan los mensajes en `older` (antiguos) y `recent` (recientes).
2. Se envía al usuario el aviso de compactación en curso.
3. Se llama al LLM con un prompt de sistema de compactación, el resumen
   existente (si lo hay) y los mensajes `older`, pidiendo un resumen breve.
4. El resumen devuelto sustituye al resumen anterior del chat.
5. El historial en memoria del chat se sustituye por sólo los mensajes
   `recent`.

#### Decisiones y bifurcaciones

1. Si la llamada al LLM de compactación falla (cualquier excepción):
   - se registra el fallo internamente y no se modifica el historial ni el
     resumen; el flujo principal (`FLOW-GLOBAL-001`) continúa aplicando
     únicamente `AUTO-CONVERSACION-001` como red de seguridad.

#### Funcionalidades utilizadas

1. `FUN-MOTORIA-001` (llamada al LLM para generar el resumen)

#### Entidades implicadas

- `ENT-CONVERSACION`
- `ENT-MENSAJE`

#### Estados iniciales

- `NOT_APPLICABLE`

#### Estados finales

- `NOT_APPLICABLE`

#### Resultado

El chat conserva un resumen actualizado de su historial más antiguo y su
historial verbatim queda reducido a los mensajes recientes, listo para el
recorte final por presupuesto (`AUTO-CONVERSACION-001`).

#### Excepciones

- Fallo de la llamada al LLM de compactación (ver decisión 1).

#### Flujos relacionados

- `FLOW-GLOBAL-001`

#### Fuentes

- `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `_compact_history()`,
  `_split_recent()`, `_reply_to()`

# 10. Incertidumbres del módulo

## Información inferida

NONE

## Información desconocida

NONE

## Conflictos

NONE

## Implementaciones parciales

### PARTIAL-CONVERSACION-001

- **Elemento:** `RULE-CONVERSACION-003`
- **Parte implementada:** La documentación (`.env.example`) exige
  explícitamente que `RECENT_HISTORY_TOKENS` sea menor que
  `MAX_HISTORY_TOKENS`.
- **Parte no implementada:** No se ha localizado validación en
  `app/config.py` (`Config.load`) que compruebe esta relación entre ambos
  valores al arrancar el bot; sólo se valida que cada uno, por separado, sea
  un número entero (`_parse_int_env`).
- **Fuentes:** `SRC-CONVERSACION-CODE-002` — `app/config.py` →
  `Config.load()`; `SRC-CONVERSACION-DOC-001` — `.env.example`

# 11. Trazabilidad del módulo

| Elemento | Tipo | Estado | Evidencia | Fuentes principales |
|---|---|---|---|---|
| `MOD-CONVERSACION` | Módulo | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001`, `SRC-CONVERSACION-CODE-002` |
| `UI-CONVERSACION-CHAT` | Interfaz | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `ENT-CONVERSACION` | Entidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `ENT-MENSAJE` | Entidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `FUN-CONVERSACION-001` | Funcionalidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `FUN-CONVERSACION-002` | Funcionalidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001`, `SRC-CONVERSACION-TEST-001` |
| `RULE-CONVERSACION-001` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `RULE-CONVERSACION-002` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `RULE-CONVERSACION-003` | Regla | `PARTIAL` | `CONFIRMED` | `SRC-CONVERSACION-DOC-001` |
| `RULE-CONVERSACION-004` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `AUTO-CONVERSACION-001` | Automatismo | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `AUTO-CONVERSACION-002` | Automatismo | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `AUTO-CONVERSACION-003` | Automatismo | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `AUTO-CONVERSACION-004` | Automatismo | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |
| `FLOW-CONVERSACION-001` | Flujo | `IMPLEMENTED` | `CONFIRMED` | `SRC-CONVERSACION-CODE-001` |

# 12. Validación del fichero

## Resultado

- Front matter completo y conforme a la sección 6 del schema.
- Todas las secciones obligatorias están presentes, incluidas aquellas sin
  contenido (marcadas `NONE`).
- Las dos entidades no tienen máquina de estados funcional; se ha declarado
  explícitamente en cada una en lugar de omitir la sección.
- Todas las referencias a `ROL-`, `MOD-`, `UI-`, `FUN-`, `RULE-`, `AUTO-`,
  `FLOW-` usadas en este fichero están definidas en este mismo fichero o en
  `_roles.md` / `_relations.md`.

## Limitaciones

- NONE
