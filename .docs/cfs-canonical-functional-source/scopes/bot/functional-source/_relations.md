---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: RELATIONS
module-id: NOT_APPLICABLE
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Relaciones y flujos transversales

# 1. Metainformación

## Fuentes

### SRC-GLOBAL-CODE-003

- **Tipo:** CODE
- **Ubicación:** `app/bot.py`
- **Descripción:** `_reply_to()` — orquestación de la delegación de
  `MOD-CONVERSACION` en `MOD-MOTOR-IA`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-GLOBAL-CODE-004

- **Tipo:** CODE
- **Ubicación:** `app/bot.py`
- **Descripción:** `handle_voice()` — orquestación de la delegación de
  `MOD-CONVERSACION` en `MOD-VOZ`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-GLOBAL-CODE-005

- **Tipo:** CODE
- **Ubicación:** `app/llm.py`
- **Descripción:** `_call_tool()` — ejecución de una herramienta desde
  `MOD-MOTOR-IA`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-GLOBAL-CODE-006

- **Tipo:** CODE
- **Ubicación:** `app/llm.py`
- **Descripción:** `_run_with_tools()` — bucle compartido de generación con
  uso de herramientas.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

# 2. Relaciones entre módulos

## REL-CONVERSACION-MOTORIA

- **Origen:** `MOD-CONVERSACION`
- **Destino:** `MOD-MOTOR-IA`
- **Dirección:** `MOD-CONVERSACION` → `MOD-MOTOR-IA`
- **Tipo:** USES
- **Descripción:** Tras preparar el historial (recorte/compactación) y el
  prompt de sistema, `MOD-CONVERSACION` delega en `MOD-MOTOR-IA` la
  generación de la respuesta del asistente, pasándole el historial completo
  y, si hay herramientas habilitadas, la lista de herramientas.
- **Entidades compartidas:** `ENT-CONVERSACION`, `ENT-MENSAJE`
- **Funcionalidades relacionadas:** `FUN-CONVERSACION-002`, `FUN-VOZ-001`,
  `FUN-MOTORIA-001`
- **Flujos relacionados:** `FLOW-GLOBAL-001`, `FLOW-GLOBAL-002`
- **Datos intercambiados:** Historial de mensajes (lista de mensajes
  usuario/asistente/sistema), lista de herramientas habilitadas.
- **Efectos cruzados:** Un fallo al llamar al LLM se traduce en un mensaje
  de error hacia el usuario sin interrumpir el proceso del bot (ver
  `RULE-MOTORIA-003`).
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-GLOBAL-CODE-003` — `app/bot.py` → `_reply_to()`

## REL-CONVERSACION-VOZ

- **Origen:** `MOD-CONVERSACION`
- **Destino:** `MOD-VOZ`
- **Dirección:** `MOD-CONVERSACION` → `MOD-VOZ`
- **Tipo:** USES
- **Descripción:** Cuando el usuario envía una nota de voz o un archivo de
  audio, `MOD-CONVERSACION` (`handle_voice`) delega la transcripción en
  `MOD-VOZ` y, con el texto resultante, reutiliza el mismo flujo de
  conversación que un mensaje de texto (`_reply_to`).
- **Entidades compartidas:** `ENT-MENSAJE`
- **Funcionalidades relacionadas:** `FUN-VOZ-001`
- **Flujos relacionados:** `FLOW-GLOBAL-002`
- **Datos intercambiados:** Bytes de audio descargados de Telegram; texto
  transcrito resultante.
- **Efectos cruzados:** Un fallo de transcripción produce un mensaje de
  error específico y no llega a invocar `MOD-MOTOR-IA` para esa nota de voz.
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-GLOBAL-CODE-004` — `app/bot.py` → `handle_voice()`

## REL-MOTORIA-HERRAMIENTAS

- **Origen:** `MOD-MOTOR-IA`
- **Destino:** `MOD-HERRAMIENTAS`
- **Dirección:** `MOD-MOTOR-IA` → `MOD-HERRAMIENTAS`
- **Tipo:** USES
- **Descripción:** Cuando el modelo, dentro del bucle de generación de
  `MOD-MOTOR-IA`, decide invocar una herramienta, `MOD-MOTOR-IA` ejecuta la
  herramienta correspondiente del catálogo de `MOD-HERRAMIENTAS` y devuelve
  su resultado al modelo como parte de la conversación.
- **Entidades compartidas:** `ENT-HERRAMIENTA`
- **Funcionalidades relacionadas:** `FUN-MOTORIA-001`,
  `FUN-HERRAMIENTAS-001`
- **Flujos relacionados:** `FLOW-GLOBAL-001`
- **Datos intercambiados:** Nombre de herramienta y argumentos solicitados
  por el modelo; resultado textual de la herramienta.
- **Efectos cruzados:** Un fallo de la herramienta nunca se propaga como
  excepción hacia la conversación (`RULE-HERRAMIENTAS-003`); se convierte en
  un mensaje de error dirigido al propio modelo.
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-GLOBAL-CODE-005` — `app/llm.py` → `_call_tool()`

# 3. Relaciones entre entidades de módulos distintos

NONE — las relaciones entre entidades identificadas (`ENT-CONVERSACION` /
`ENT-MENSAJE`) son intra-módulo y se definen en `mod-conversacion.md`.

# 4. Flujos transversales

## FLOW-GLOBAL-001 — Enviar un mensaje de texto y recibir respuesta

- **Objetivo:** Que un usuario autorizado envíe un mensaje de texto al bot y
  reciba la respuesta generada por el backend LLM configurado, con el
  historial de conversación correctamente acotado y, si procede, apoyada en
  herramientas.
- **Módulos:** `MOD-CONVERSACION`, `MOD-MOTOR-IA`, `MOD-HERRAMIENTAS`
- **Roles:** `ROL-USUARIO`
- **Entidades:** `ENT-CONVERSACION`, `ENT-MENSAJE`, `ENT-HERRAMIENTA`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Secuencia

1. `MOD-CONVERSACION` / `FUN-CONVERSACION-002`: el usuario envía un mensaje
   de texto; se comprueba el acceso (`RULE-CONVERSACION-001`) y se añade el
   mensaje al historial del chat.
2. `MOD-CONVERSACION` / `AUTO-CONVERSACION-004`: se muestra el indicador de
   «escribiendo…» mientras dura el resto del proceso.
3. `MOD-CONVERSACION` / `AUTO-CONVERSACION-002`: si el historial supera el
   presupuesto de tokens, se compactan los mensajes más antiguos en un
   resumen (con aviso previo al usuario); si la compactación falla, se
   continúa sin ella.
4. `MOD-CONVERSACION` / `AUTO-CONVERSACION-003`: se reconstruye el mensaje
   de sistema con la fecha/hora actual y, si existe, el resumen.
5. `MOD-CONVERSACION` / `AUTO-CONVERSACION-001`: se recorta el historial
   resultante al presupuesto de tokens configurado, conservando siempre el
   mensaje de sistema y el mensaje más reciente.
6. `MOD-MOTOR-IA` / `FUN-MOTORIA-001`: se llama al backend LLM configurado
   con el historial preparado y, si hay herramientas habilitadas, su lista.
7. `MOD-HERRAMIENTAS` / `FUN-HERRAMIENTAS-001` (condicional): si el modelo
   solicita una herramienta, se ejecuta y su resultado se reincorpora a la
   conversación con el modelo, hasta un máximo de rondas
   (`RULE-MOTORIA-002`).
8. `MOD-CONVERSACION`: la respuesta final del modelo se añade al historial y
   se envía al usuario por Telegram.

### Decisiones y bifurcaciones

1. Si el usuario no está en la lista blanca (`RULE-CONVERSACION-001`):
   - se responde «You don't have access to this bot.» y el flujo termina en
     el paso 1.
2. Si el historial no supera el presupuesto de tokens:
   - se omiten los pasos de compactación (paso 3).
3. Si la llamada al LLM falla (paso 6):
   - se responde «Something went wrong talking to the model. Please try
     again.» y el flujo termina sin añadir una respuesta de asistente al
     historial.
4. Si el modelo no solicita ninguna herramienta, o `ENABLED_TOOLS` está
   vacío:
   - se omite el paso 7 y la respuesta se genera directamente.
5. Si se alcanza el máximo de rondas de herramientas sin que el modelo deje
   de solicitarlas (`RULE-MOTORIA-002`):
   - se fuerza una ronda final sin herramientas ofrecidas, forzando una
     respuesta en texto.

### Funcionalidades utilizadas

1. `FUN-CONVERSACION-002`
2. `FUN-MOTORIA-001`
3. `FUN-HERRAMIENTAS-001` (condicional)

### Entidades implicadas

- `ENT-CONVERSACION`
- `ENT-MENSAJE`
- `ENT-HERRAMIENTA`

### Estados iniciales

- `NOT_APPLICABLE` — las entidades implicadas no tienen máquina de estados
  (ver `mod-conversacion.md`, sección Entidades).

### Estados finales

- `NOT_APPLICABLE`

### Resultado

El usuario recibe una respuesta del asistente en el chat de Telegram, y el
historial de conversación queda actualizado (y, si procedía, compactado)
para el siguiente mensaje.

### Excepciones

- Acceso denegado (paso 1).
- Fallo de la llamada al LLM (paso 6).
- Fallo de una herramienta durante su ejecución: no interrumpe el flujo
  (`RULE-HERRAMIENTAS-003`), se informa al modelo como resultado de la
  herramienta.

### Flujos relacionados

- `FLOW-GLOBAL-002`
- `FLOW-CONVERSACION-001` (detalle interno de compactación, en
  `mod-conversacion.md`)

### Fuentes

- `SRC-GLOBAL-CODE-003` — `app/bot.py` → `_reply_to()`
- `SRC-GLOBAL-CODE-006` — `app/llm.py` → `_run_with_tools()`

## FLOW-GLOBAL-002 — Enviar una nota de voz y recibir respuesta

- **Objetivo:** Que un usuario autorizado envíe una nota de voz o un archivo
  de audio y reciba la respuesta del asistente, tratando el contenido
  transcrito como un mensaje más de la conversación.
- **Módulos:** `MOD-VOZ`, `MOD-CONVERSACION`, `MOD-MOTOR-IA`
- **Roles:** `ROL-USUARIO`
- **Entidades:** `ENT-MENSAJE`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Secuencia

1. `MOD-CONVERSACION`: se comprueba el acceso (`RULE-CONVERSACION-001`).
2. `MOD-VOZ` / `FUN-VOZ-001`: se descarga el audio desde Telegram y se
   transcribe con Whisper.
3. `MOD-VOZ` / `RULE-VOZ-001`: el texto transcrito se antepone con el
   prefijo `[Voice message, transcribed by Whisper]:`.
4. `MOD-CONVERSACION` / `FLOW-GLOBAL-001`: el texto resultante se trata
   exactamente igual que un mensaje de texto entrante, reutilizando los
   pasos 1-8 de dicho flujo desde «se añade el mensaje al historial».

### Decisiones y bifurcaciones

1. Si el usuario no está en la lista blanca:
   - se responde «You don't have access to this bot.» y el flujo termina.
2. Si la transcripción falla (excepción durante `FUN-VOZ-001`):
   - se responde «Couldn't transcribe that voice message. Please try again
     or send it as text.» y el flujo termina sin invocar
     `MOD-MOTOR-IA`.
3. Si la transcripción no detecta ningún habla (texto vacío tras `strip()`):
   - se responde «I couldn't make out any speech in that voice message.» y
     el flujo termina.

### Funcionalidades utilizadas

1. `FUN-VOZ-001`
2. `FUN-CONVERSACION-002` (reutilizada para el resto del intercambio, vía
   `FLOW-GLOBAL-001`)

### Entidades implicadas

- `ENT-MENSAJE`

### Estados iniciales

- `NOT_APPLICABLE`

### Estados finales

- `NOT_APPLICABLE`

### Resultado

El usuario recibe una respuesta del asistente basada en el contenido hablado
de su nota de voz, indistinguible en el resto del proceso de un mensaje de
texto salvo por el prefijo de transcripción visible en el historial que ve
el modelo.

### Excepciones

- Acceso denegado.
- Fallo de transcripción.
- Transcripción vacía (sin habla detectada).

### Flujos relacionados

- `FLOW-GLOBAL-001`

### Fuentes

- `SRC-GLOBAL-CODE-004` — `app/bot.py` → `handle_voice()`

# 5. Dependencias entre scopes

NONE — no existen otros scopes en este repositorio en este momento.

# 6. Resumen de relaciones intra-módulo

| ID | Fichero | Resumen |
|---|---|---|
| NONE | — | No existen relaciones intra-módulo con ID propio: `MOD-CONVERSACION` sólo tiene una relación entidad-entidad simple (composición de `ENT-CONVERSACION` con `ENT-MENSAJE`), documentada narrativamente en `mod-conversacion.md` sin requerir un `REL-` independiente. |

# 7. Incertidumbres

## Información desconocida

NONE

## Conflictos

NONE

# 8. Validación del fichero

## Resultado

- Front matter completo y conforme a la sección 6 del schema.
- Las tres relaciones inter-módulo cubren todas las dependencias observadas
  en el código entre los cuatro módulos del scope.
- Los dos flujos transversales cubren los dos puntos de entrada del usuario
  (texto y voz) documentados en `MOD-CONVERSACION` y `MOD-VOZ`.
- No se han encontrado dependencias con otros scopes ni relaciones
  inter-módulo adicionales.
