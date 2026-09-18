---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: MODULE
module-id: MOD-VOZ
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Módulo Mensajes de voz

# 1. Metainformación

Módulo extraído a partir de la parte de `app/bot.py` relativa a
transcripción de voz (`handle_voice`, `transcribe_voice`,
`_transcribe_sync`, `_get_whisper_model`) y `.env.example`
(`WHISPER_MODEL`).

# 2. Módulo

## MOD-VOZ — Mensajes de voz

- **Nombre:** Mensajes de voz
- **Objetivo:** Permitir que el usuario se comunique con el asistente
  mediante notas de voz o archivos de audio de Telegram, transcribiéndolos a
  texto antes de incorporarlos a la conversación.
- **Responsabilidad funcional:** Todo lo relativo a la transcripción de
  audio a texto pertenece a este módulo. Una vez obtenido el texto
  transcrito, el resto del ciclo de vida del mensaje (historial, llamada al
  modelo, respuesta) pertenece a `MOD-CONVERSACION` y `MOD-MOTOR-IA`.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Resumen funcional

Cuando el usuario envía una nota de voz o un archivo de audio, el bot lo
descarga desde Telegram y lo transcribe localmente con `faster-whisper` (en
CPU, con un modelo configurable). El texto resultante se antepone con un
prefijo fijo que indica que es una transcripción, y a partir de ahí sigue
exactamente el mismo camino que un mensaje de texto (`FLOW-GLOBAL-001`).

### Roles

- `ROL-USUARIO`

### Entidades principales

- NONE — la transcripción no crea una entidad propia; su resultado se
  incorpora como un `ENT-MENSAJE` ordinario de `MOD-CONVERSACION`.

### Interfaces principales

- `UI-CONVERSACION-CHAT` (definida en `mod-conversacion.md`; el envío de
  notas de voz usa el mismo chat de Telegram, sin una interfaz propia)

### Funcionalidades

- `FUN-VOZ-001`

### Flujos internos

- NONE — el único flujo relevante (`FLOW-GLOBAL-002`) es transversal y se
  define en `_relations.md`.

### Reglas de negocio

- `RULE-VOZ-001`

### Automatismos

- NONE — la transcripción es siempre resultado directo de una acción del
  usuario (enviar una nota de voz), no se dispara automáticamente sin esa
  acción.

### Módulos relacionados

- `MOD-CONVERSACION`

### Fuentes principales

- `SRC-VOZ-CODE-001`

# 3. Fuentes y cobertura del módulo

## Fuentes analizadas

### SRC-VOZ-CODE-001

- **Tipo:** CODE
- **Ubicación:** `app/bot.py`
- **Descripción:** `handle_voice()`, `transcribe_voice()`,
  `_transcribe_sync()`, `_get_whisper_model()`, constante
  `VOICE_TRANSCRIPTION_PREFIX`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-VOZ-DOC-001

- **Tipo:** DOCUMENT
- **Ubicación:** `.env.example`
- **Descripción:** Documentación de `WHISPER_MODEL` y sus valores posibles.
- **Fecha o versión:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-VOZ-CONFIG-001

- **Tipo:** CONFIGURATION
- **Ubicación:** `docker-compose.yml`
- **Descripción:** Volumen `whisper_data` que persiste los pesos del modelo
  Whisper descargado entre reinicios del contenedor.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-VOZ-TEST-001

- **Tipo:** TEST
- **Ubicación:** `tests/test_bot.py`
- **Descripción:** Confirma el manejo de fallos de transcripción y de
  transcripciones vacías.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

## Fuentes no disponibles o no analizadas

NONE

## Cobertura

- **Backend:** COMPLETE
- **Frontend:** NOT_APPLICABLE
- **Base de datos:** NOT_APPLICABLE
- **Documentación funcional:** COMPLETE
- **Planes / especificaciones:** NOT_APPLICABLE
- **Integraciones relevantes:** COMPLETE (Telegram para descarga de audio;
  `faster-whisper` para transcripción local)

### Limitaciones

- NONE

# 4. Navegación e interfaces de usuario

NONE — la funcionalidad de voz se accede desde la misma interfaz de chat
documentada como `UI-CONVERSACION-CHAT` en `mod-conversacion.md`; no existe
una superficie de interfaz propia de este módulo.

# 5. Entidades funcionales

NONE — la transcripción no persiste ni gestiona una entidad propia; su
único efecto funcional es producir el contenido de un `ENT-MENSAJE`
(propiedad de `MOD-CONVERSACION`).

# 6. Funcionalidades

## FUN-VOZ-001 — Enviar una nota de voz y recibir respuesta

- **Nombre:** Enviar una nota de voz y recibir respuesta
- **Módulo:** `MOD-VOZ`
- **Descripción:** El usuario envía una nota de voz o un archivo de audio;
  el bot lo transcribe a texto y, a partir de ahí, lo trata como un mensaje
  de texto normal para generar la respuesta del asistente.
- **User-facing:** YES
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Roles autorizados

- `ROL-USUARIO`

#### Interfaces de acceso

- `UI-CONVERSACION-CHAT`

#### Entidades implicadas

- `ENT-MENSAJE` (definida en `MOD-CONVERSACION`; el mensaje transcrito se
  incorpora al historial como un mensaje de usuario ordinario)

#### Precondiciones

- El usuario debe estar en la lista blanca de usuarios autorizados
  (`RULE-CONVERSACION-001`, definida en `MOD-CONVERSACION`).
- El mensaje debe ser una nota de voz o un archivo de audio reconocido por
  Telegram (filtro `filters.VOICE | filters.AUDIO`).

#### Trigger / inicio

El usuario envía una nota de voz o un archivo de audio en el chat con el
bot.

#### Acción funcional

El bot descarga el audio desde Telegram, lo transcribe con el modelo
Whisper configurado (`WHISPER_MODEL`) ejecutándolo en un hilo aparte para no
bloquear el proceso, antepone el prefijo de transcripción
(`RULE-VOZ-001`) y reutiliza el mismo procesamiento que un mensaje de texto
(`FUN-CONVERSACION-002`, vía `FLOW-GLOBAL-002`).

#### Datos requeridos

- Archivo de audio (nota de voz o audio) enviado por Telegram.

#### Datos opcionales

- NONE

#### Resultado esperado

El usuario recibe la respuesta del asistente basada en el contenido hablado
de su nota de voz.

#### Cambios de estado

- `NOT_APPLICABLE`

#### Datos creados o modificados

- Se añade un mensaje de usuario (el texto transcrito, con prefijo) al
  historial de la conversación (`ENT-CONVERSACION`, en `MOD-CONVERSACION`).

#### Efectos secundarios

- El modelo Whisper usado se carga en memoria la primera vez que se necesita
  y se mantiene en caché por nombre de modelo durante toda la vida del
  proceso (no se recarga en cada nota de voz).

#### Módulos afectados

- `MOD-CONVERSACION`

#### Reglas de negocio

- `RULE-VOZ-001`
- `RULE-CONVERSACION-001` (`otro-módulo::` no aplica; referenciada
  directamente por ID, definida en `MOD-CONVERSACION`)

#### Automatismos relacionados

- NONE

#### Restricciones

- La precisión y velocidad de la transcripción dependen del modelo Whisper
  configurado (`tiny`/`base`/`small`/`medium`/`large-v3`); se ejecuta
  siempre en CPU.

#### Excepciones y errores funcionales

- El usuario no tiene acceso: se responde «You don't have access to this
  bot.» y no se descarga ni transcribe el audio.
- Falla la transcripción (cualquier excepción durante la descarga o el
  proceso de Whisper): se responde «Couldn't transcribe that voice message.
  Please try again or send it as text.» y el mensaje no llega a incorporarse
  a la conversación ni a `MOD-MOTOR-IA`.
- La transcripción resulta vacía (ningún habla detectada tras recortar
  espacios): se responde «I couldn't make out any speech in that voice
  message.» y tampoco se incorpora a la conversación.

#### Resultado visible para el usuario

Respuesta de texto del asistente, generada a partir del contenido hablado;
o uno de los mensajes de error anteriores si la transcripción falla o está
vacía.

#### Funcionalidades relacionadas

- `FUN-CONVERSACION-002`

#### Fuentes

- `SRC-VOZ-CODE-001` — `app/bot.py` → `handle_voice()`, `transcribe_voice()`
- `SRC-VOZ-TEST-001` — `tests/test_bot.py`

# 7. Reglas de negocio

## RULE-VOZ-001

- **Nombre:** Prefijo de transcripción antepuesto siempre
- **Módulo propietario:** `MOD-VOZ`
- **Descripción:** Todo texto transcrito de una nota de voz se antepone
  siempre con el prefijo `[Voice message, transcribed by Whisper]:` antes de
  añadirse al historial de la conversación, para que el modelo pueda
  distinguir un mensaje hablado de uno escrito.
- **Condición:** Se ha transcrito con éxito una nota de voz o archivo de
  audio con contenido de habla detectado.
- **Consecuencia:** El prompt de sistema (definido en `MOD-CONVERSACION`)
  explica esta convención al modelo, de forma que pueda responder de forma
  coherente si el usuario se refiere a «el audio» o «lo que dije».
- **Roles afectados:** `ROL-USUARIO`
- **Entidades afectadas:** `ENT-MENSAJE` (definida en `MOD-CONVERSACION`)
- **Funcionalidades afectadas:** `FUN-VOZ-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-VOZ-CODE-001` — `app/bot.py` →
  `VOICE_TRANSCRIPTION_PREFIX`, `handle_voice()`

# 8. Automatismos

NONE — la transcripción siempre requiere una acción explícita del usuario
(enviar una nota de voz); no existe ningún automatismo sin esa acción
disparadora dentro de este módulo.

# 9. Flujos internos

NONE — el flujo relevante (`FLOW-GLOBAL-002`) es transversal entre
`MOD-VOZ`, `MOD-CONVERSACION` y `MOD-MOTOR-IA`, y se define en
`_relations.md`.

# 10. Incertidumbres del módulo

## Información inferida

NONE

## Información desconocida

NONE

## Conflictos

NONE

## Implementaciones parciales

NONE

# 11. Trazabilidad del módulo

| Elemento | Tipo | Estado | Evidencia | Fuentes principales |
|---|---|---|---|---|
| `MOD-VOZ` | Módulo | `IMPLEMENTED` | `CONFIRMED` | `SRC-VOZ-CODE-001` |
| `FUN-VOZ-001` | Funcionalidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-VOZ-CODE-001`, `SRC-VOZ-TEST-001` |
| `RULE-VOZ-001` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-VOZ-CODE-001` |

# 12. Validación del fichero

## Resultado

- Front matter completo y conforme a la sección 6 del schema.
- Todas las secciones obligatorias están presentes; las que no aplican a
  este módulo (entidades, UI, automatismos, flujos internos) están
  explícitamente marcadas como `NONE` con la justificación correspondiente.
- Todas las referencias a IDs externos a este módulo (`ENT-MENSAJE`,
  `RULE-CONVERSACION-001`, `UI-CONVERSACION-CHAT`, `FUN-CONVERSACION-002`,
  `FLOW-GLOBAL-002`) están definidas en `mod-conversacion.md` o
  `_relations.md`.

## Limitaciones

- NONE
