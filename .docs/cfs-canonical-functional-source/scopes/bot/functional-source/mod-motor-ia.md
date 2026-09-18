---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: MODULE
module-id: MOD-MOTOR-IA
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Módulo Motor de IA

# 1. Metainformación

Módulo extraído a partir de `app/llm.py`, la parte de `app/config.py`
relativa a la selección de backend, `app/bot.py` (`_warm_up_ollama`,
`post_init`), `.env.example` (`LLM_BACKEND` y variables asociadas) y
`docker-compose.yml` (servicio `ollama`).

# 2. Módulo

## MOD-MOTOR-IA — Motor de IA

- **Nombre:** Motor de IA
- **Objetivo:** Generar la respuesta del asistente llamando al backend LLM
  configurado (modelo local vía Ollama, o una API remota compatible con
  OpenAI), coordinando el uso de herramientas cuando el modelo las solicita.
- **Responsabilidad funcional:** La elección de backend, la forma concreta
  de la petición a cada uno, el bucle que decide cuántas rondas de
  herramientas permitir, y el precalentamiento del modelo Ollama al
  arrancar, pertenecen a este módulo. Qué herramientas existen y cómo se
  ejecuta cada una pertenece a `MOD-HERRAMIENTAS`; cuándo se llama a este
  módulo (con qué historial) pertenece a `MOD-CONVERSACION`.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Resumen funcional

Cada agente se configura con un único backend LLM: `ollama` (el servicio
`ollama` del propio `docker-compose.yml`, sin necesidad de API key) o
`cloud` (cualquier API que exponga un endpoint `/chat/completions`
compatible con OpenAI, con clave de API). Ambos backends comparten un mismo
bucle de generación con soporte de herramientas: si se ofrecen herramientas
y el modelo las solicita, se ejecutan (delegando en `MOD-HERRAMIENTAS`) y su
resultado se reincorpora a la conversación, hasta un máximo de rondas, tras
el cual se fuerza una ronda final sin herramientas ofrecidas para obligar a
una respuesta en texto. Cuando el backend es `ollama`, el modelo se
precarga en memoria al arrancar el bot para que la primera respuesta real no
pague ese coste.

### Roles

- `ROL-OPERADOR`

### Entidades principales

- NONE — este módulo no gestiona entidades funcionales persistentes propias;
  opera sobre el historial de mensajes propiedad de `MOD-CONVERSACION`.

### Interfaces principales

- NONE — no tiene interfaz propia; es invisible para `ROL-USUARIO`.

### Funcionalidades

- `FUN-MOTORIA-001`

### Flujos internos

- NONE — su participación se documenta dentro de los flujos transversales
  `FLOW-GLOBAL-001` y `FLOW-GLOBAL-002`, en `_relations.md`.

### Reglas de negocio

- `RULE-MOTORIA-001`
- `RULE-MOTORIA-002`
- `RULE-MOTORIA-003`

### Automatismos

- `AUTO-MOTORIA-001`

### Módulos relacionados

- `MOD-CONVERSACION`
- `MOD-HERRAMIENTAS`

### Fuentes principales

- `SRC-MOTORIA-CODE-001`

# 3. Fuentes y cobertura del módulo

## Fuentes analizadas

### SRC-MOTORIA-CODE-001

- **Tipo:** CODE
- **Ubicación:** `app/llm.py`
- **Descripción:** `LLMClient` (protocolo), `OllamaClient`, `CloudClient`,
  `build_llm_client()`, `_run_with_tools()`, `_call_tool()`, `_post_json()`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-MOTORIA-CODE-002

- **Tipo:** CODE
- **Ubicación:** `app/bot.py`
- **Descripción:** `_warm_up_ollama()`, registro de la tarea de
  precalentamiento en `post_init()`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-MOTORIA-CODE-003

- **Tipo:** CODE
- **Ubicación:** `app/config.py`
- **Descripción:** Validación y valores por defecto de `LLM_BACKEND` y de
  las variables específicas de cada backend.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-MOTORIA-DOC-001

- **Tipo:** DOCUMENT
- **Ubicación:** `.env.example`
- **Descripción:** Documentación de `LLM_BACKEND`, `OLLAMA_BASE_URL`,
  `OLLAMA_MODEL`, `CLOUD_API_BASE_URL`, `CLOUD_API_KEY`, `CLOUD_MODEL`.
- **Fecha o versión:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-MOTORIA-CONFIG-001

- **Tipo:** CONFIGURATION
- **Ubicación:** `docker-compose.yml`
- **Descripción:** Servicio `ollama` (red interna, `OLLAMA_KEEP_ALIVE=-1`,
  volumen `ollama_data`), usado únicamente cuando `LLM_BACKEND=ollama`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-MOTORIA-TEST-001

- **Tipo:** TEST
- **Ubicación:** `tests/test_llm.py`
- **Descripción:** Confirma el bucle de herramientas, el límite de rondas,
  la construcción de payloads por backend y el manejo de errores de
  herramienta.
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
- **Integraciones relevantes:** COMPLETE (servicio Ollama vía HTTP interno
  de Compose; cualquier API compatible con OpenAI vía HTTPS)

### Limitaciones

- No se ha verificado contra un backend `cloud` real (OpenAI, OpenRouter,
  etc.) ni contra una instancia real de Ollama; el comportamiento se basa en
  la lectura de `app/llm.py` y en `tests/test_llm.py` (E/S mockeada).

# 4. Navegación e interfaces de usuario

NONE — este módulo no tiene interfaz propia; opera exclusivamente detrás de
`UI-CONVERSACION-CHAT` (definida en `mod-conversacion.md`), invocado por
`MOD-CONVERSACION`.

# 5. Entidades funcionales

NONE — este módulo no posee entidades funcionales propias con ciclo de vida
(creación/modificación/eliminación); trabaja sobre el historial de mensajes
propiedad de `ENT-CONVERSACION`/`ENT-MENSAJE` (`MOD-CONVERSACION`) y sobre
el catálogo de `ENT-HERRAMIENTA` (`MOD-HERRAMIENTAS`).

# 6. Funcionalidades

## FUN-MOTORIA-001 — Generar la respuesta del asistente

- **Nombre:** Generar la respuesta del asistente
- **Módulo:** `MOD-MOTOR-IA`
- **Descripción:** Dado un historial de mensajes (y, opcionalmente, una
  lista de herramientas habilitadas), llamar al backend LLM configurado
  para obtener la respuesta del asistente, gestionando internamente
  cualquier ronda de uso de herramientas que el modelo solicite.
- **User-facing:** NO — no es una acción que el usuario inicie
  directamente; es invocada internamente por `FUN-CONVERSACION-002`,
  `FUN-VOZ-001` y por la compactación de historial
  (`AUTO-CONVERSACION-002`).
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Roles autorizados

- `NOT_APPLICABLE` — no se invoca directamente por ningún rol; es interna.

#### Interfaces de acceso

- NONE

#### Entidades implicadas

- NONE propias de este módulo (opera sobre `ENT-MENSAJE`, propiedad de
  `MOD-CONVERSACION`, y `ENT-HERRAMIENTA`, propiedad de
  `MOD-HERRAMIENTAS`).

#### Precondiciones

- Debe existir configuración válida para el backend seleccionado
  (`LLM_BACKEND`): URL base de Ollama, o URL base + clave de API + modelo
  para `cloud`.

#### Trigger / inicio

Es invocada internamente por `MOD-CONVERSACION` (para responder a un
mensaje de texto o de voz transcrito, o para compactar el historial) — no
tiene un trigger propio iniciado por el usuario.

#### Acción funcional

Si no se ofrecen herramientas, se realiza una única llamada al backend
configurado y se devuelve su respuesta de texto. Si se ofrecen herramientas,
se ejecuta un bucle (`RULE-MOTORIA-002`): en cada ronda se llama al backend
ofreciéndole las herramientas; si el modelo solicita una o varias, se
ejecutan (delegando en `MOD-HERRAMIENTAS`) y su resultado se añade a la
conversación antes de la siguiente ronda; si el modelo no solicita ninguna,
su respuesta de texto se devuelve directamente.

#### Datos requeridos

- Historial de mensajes (lista con roles `system`/`user`/`assistant`, y
  eventualmente `tool`).

#### Datos opcionales

- Lista de herramientas habilitadas para esa llamada.

#### Resultado esperado

Un texto de respuesta del asistente, listo para enviarse al usuario (o para
usarse como resumen, en el caso de la compactación de historial).

#### Cambios de estado

- `NOT_APPLICABLE`

#### Datos creados o modificados

- NONE persistente — los mensajes intermedios de la ronda de herramientas
  existen sólo durante la llamada; el historial persistente lo gestiona
  `MOD-CONVERSACION` a partir del resultado devuelto.

#### Efectos secundarios

- Una petición HTTP saliente al backend configurado (Ollama o la API cloud)
  por cada ronda del bucle.

#### Módulos afectados

- `MOD-HERRAMIENTAS` (cuando el modelo solicita herramientas)

#### Reglas de negocio

- `RULE-MOTORIA-001`
- `RULE-MOTORIA-002`
- `RULE-MOTORIA-003`

#### Automatismos relacionados

- `AUTO-MOTORIA-001`

#### Restricciones

- El timeout de lectura para el backend `ollama` es de 300 segundos (frente
  a 10 segundos de conexión), para tolerar la carga inicial de un modelo
  «frío»; el backend `cloud` usa un timeout fijo de 120 segundos.
- El uso efectivo de herramientas depende de que el modelo configurado
  soporte tool/function calling; si no lo soporta, simplemente no las
  solicita y el resultado es indistinguible de no tener herramientas
  habilitadas.

#### Excepciones y errores funcionales

- Cualquier error de red o de respuesta HTTP no exitosa del backend (vía
  `httpx`) se propaga como excepción hacia quien llama a
  `FUN-MOTORIA-001`; `MOD-CONVERSACION` la convierte en el mensaje «Something
  went wrong talking to the model. Please try again.» para el usuario (ver
  `FUN-CONVERSACION-002`). Este módulo no la gestiona internamente ni la
  convierte en un mensaje de error propio.
- Si el modelo sigue solicitando herramientas indefinidamente, se alcanza el
  límite de rondas (`RULE-MOTORIA-002`) y se devuelve el texto «I tried
  using some tools but couldn't get to an answer. Could you rephrase?» en
  lugar de continuar sin límite.

#### Resultado visible para el usuario

Indirecto: el texto de respuesta se envía al usuario a través de
`MOD-CONVERSACION`.

#### Funcionalidades relacionadas

- `FUN-CONVERSACION-002`
- `FUN-VOZ-001`
- `FUN-HERRAMIENTAS-001`

#### Fuentes

- `SRC-MOTORIA-CODE-001` — `app/llm.py` → `OllamaClient.chat()`,
  `CloudClient.chat()`, `_run_with_tools()`
- `SRC-MOTORIA-TEST-001` — `tests/test_llm.py`

# 7. Reglas de negocio

## RULE-MOTORIA-001

- **Nombre:** Selección de backend LLM por configuración
- **Módulo propietario:** `MOD-MOTOR-IA`
- **Descripción:** El backend usado para generar respuestas (`ollama` o
  `cloud`) se determina íntegramente por la variable de entorno
  `LLM_BACKEND` al arrancar el proceso; no puede cambiarse en tiempo de
  ejecución ni por conversación.
- **Condición:** Arranque del proceso (`Config.load()`).
- **Consecuencia:** Un valor distinto de `ollama`/`cloud` impide arrancar el
  bot (error explícito); un valor válido determina qué cliente
  (`OllamaClient`/`CloudClient`) se construye para toda la vida del proceso.
- **Roles afectados:** `ROL-OPERADOR`
- **Entidades afectadas:** NONE
- **Funcionalidades afectadas:** `FUN-MOTORIA-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-MOTORIA-CODE-003` — `app/config.py` → `Config.load()`;
  `SRC-MOTORIA-CODE-001` — `app/llm.py` → `build_llm_client()`

## RULE-MOTORIA-002

- **Nombre:** Límite de rondas de uso de herramientas
- **Módulo propietario:** `MOD-MOTOR-IA`
- **Descripción:** El bucle de uso de herramientas permite como máximo 3
  rondas en las que se ofrecen herramientas al modelo; en una ronda
  adicional final, las herramientas no se ofrecen, forzando al modelo a
  responder en texto.
- **Condición:** Se están usando herramientas (`tools` no vacío) al generar
  una respuesta.
- **Consecuencia:** Un modelo que solicitara herramientas indefinidamente no
  puede bloquear la respuesta para siempre; en el peor caso, tras la ronda
  final sin herramientas, si el modelo aun así no da una respuesta de texto,
  se devuelve un mensaje fijo pidiendo reformular la pregunta.
- **Roles afectados:** `ROL-USUARIO` (beneficiario)
- **Entidades afectadas:** `ENT-HERRAMIENTA`
- **Funcionalidades afectadas:** `FUN-MOTORIA-001`, `FUN-HERRAMIENTAS-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-MOTORIA-CODE-001` — `app/llm.py` →
  `MAX_TOOL_ROUNDS`, `_run_with_tools()`

## RULE-MOTORIA-003

- **Nombre:** Un fallo de herramienta se resuelve dentro del bucle de
  generación, nunca fuera de él
- **Módulo propietario:** `MOD-MOTOR-IA`
- **Descripción:** Cuando el modelo solicita una herramienta, su ejecución
  (delegada en `MOD-HERRAMIENTAS`) se envuelve de forma que cualquier
  excepción se convierte en un mensaje de resultado de herramienta en lugar
  de interrumpir el bucle de generación; esto es lo que hace posible
  `RULE-HERRAMIENTAS-003`.
- **Condición:** El modelo solicita una herramienta durante una ronda del
  bucle de generación.
- **Consecuencia:** El bucle de generación siempre completa su ronda actual,
  independientemente de si la herramienta tuvo éxito.
- **Roles afectados:** `ROL-USUARIO` (beneficiario)
- **Entidades afectadas:** `ENT-HERRAMIENTA`
- **Funcionalidades afectadas:** `FUN-MOTORIA-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-MOTORIA-CODE-001` — `app/llm.py` → `_call_tool()`

# 8. Automatismos

## AUTO-MOTORIA-001

- **Nombre:** Precalentamiento del modelo Ollama al arrancar
- **Módulo propietario:** `MOD-MOTOR-IA`
- **Descripción:** Si el backend configurado es `ollama`, al arrancar el bot
  se lanza en segundo plano una llamada de prueba al modelo para forzar su
  carga en memoria/VRAM antes de que llegue el primer mensaje real de un
  usuario.
- **Trigger:** Arranque de la aplicación (`post_init`, tras construir el
  cliente Telegram).
- **Condiciones:** `LLM_BACKEND` es `ollama`.
- **Acciones ejecutadas:** Se envía un mensaje de prueba («Hi») al backend
  Ollama; si falla, se reintenta hasta 10 veces con una pausa entre
  intentos (para tolerar que el servicio `ollama` de Compose tarde unos
  segundos en aceptar conexiones); si todos los intentos fallan, se registra
  un aviso y el bot sigue funcionando con normalidad (el primer mensaje real
  simplemente pagará el coste de carga).
- **Entidades afectadas:** NONE
- **Cambios de estado:** `NOT_APPLICABLE`
- **Módulos afectados:** `NONE`
- **Resultado visible para el usuario:** Ninguno directo; efecto indirecto
  en que la primera respuesta real tras un arranque no sufre el retraso de
  carga del modelo (salvo que el precalentamiento agote sus reintentos).
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-MOTORIA-CODE-002` — `app/bot.py` →
  `_warm_up_ollama()`, `post_init()`

# 9. Flujos internos

NONE — la participación de este módulo se documenta dentro de los flujos
transversales `FLOW-GLOBAL-001` y `FLOW-GLOBAL-002`, en `_relations.md`.

# 10. Incertidumbres del módulo

## Información inferida

NONE

## Información desconocida

### UNK-MOTORIA-001

- **Elemento:** `FUN-MOTORIA-001` (backend `cloud`)
- **Información no determinada:** No se ha verificado el comportamiento
  real contra un proveedor `cloud` concreto (OpenAI, OpenRouter u otro);
  sólo se ha confirmado la forma de la petición HTTP construida
  (`CloudClient.chat()`) y su cobertura por tests con E/S mockeada.
- **Fuentes revisadas:** `app/llm.py`, `tests/test_llm.py`
- **Qué sería necesario para resolverlo:** Ejecutar el bot con
  `LLM_BACKEND=cloud` y una clave de API real contra al menos un proveedor.
- **Impacto documental:** LOW — la forma de la petición sigue exactamente el
  estándar `/chat/completions`, ampliamente estable entre proveedores
  compatibles.

## Conflictos

NONE

## Implementaciones parciales

NONE

# 11. Trazabilidad del módulo

| Elemento | Tipo | Estado | Evidencia | Fuentes principales |
|---|---|---|---|---|
| `MOD-MOTOR-IA` | Módulo | `IMPLEMENTED` | `CONFIRMED` | `SRC-MOTORIA-CODE-001`, `SRC-MOTORIA-CODE-002`, `SRC-MOTORIA-CODE-003` |
| `FUN-MOTORIA-001` | Funcionalidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-MOTORIA-CODE-001`, `SRC-MOTORIA-TEST-001` |
| `RULE-MOTORIA-001` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-MOTORIA-CODE-003`, `SRC-MOTORIA-CODE-001` |
| `RULE-MOTORIA-002` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-MOTORIA-CODE-001` |
| `RULE-MOTORIA-003` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-MOTORIA-CODE-001` |
| `AUTO-MOTORIA-001` | Automatismo | `IMPLEMENTED` | `CONFIRMED` | `SRC-MOTORIA-CODE-002` |

# 12. Validación del fichero

## Resultado

- Front matter completo y conforme a la sección 6 del schema.
- Todas las secciones obligatorias están presentes; las que no aplican a
  este módulo (entidades propias, UI, flujos internos) están explícitamente
  marcadas `NONE` con su justificación.
- Todas las referencias externas (`ENT-MENSAJE`, `ENT-HERRAMIENTA`,
  `FUN-CONVERSACION-002`, `FUN-VOZ-001`, `FUN-HERRAMIENTAS-001`,
  `RULE-HERRAMIENTAS-003`, `AUTO-CONVERSACION-002`, `UI-CONVERSACION-CHAT`)
  están definidas en `mod-conversacion.md`, `mod-voz.md` o
  `mod-herramientas.md`.

## Limitaciones

- Ver `UNK-MOTORIA-001` sobre la falta de verificación contra un backend
  `cloud` real.
