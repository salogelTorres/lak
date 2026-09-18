---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: MODULE
module-id: MOD-HERRAMIENTAS
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Módulo Herramientas

# 1. Metainformación

Módulo extraído a partir de `app/tools/base.py`, `app/tools/__init__.py`,
`app/tools/web_search.py` y `.env.example` (`ENABLED_TOOLS`).

# 2. Módulo

## MOD-HERRAMIENTAS — Herramientas

- **Nombre:** Herramientas
- **Objetivo:** Catalogar capacidades adicionales que el modelo puede
  invocar durante la generación de una respuesta (p. ej. búsqueda web), de
  forma independiente de qué agente concreto las tiene habilitadas.
- **Responsabilidad funcional:** La existencia y definición del catálogo de
  herramientas, así como el comportamiento propio de cada herramienta
  (p. ej. cómo busca y filtra resultados `search_web`), pertenece a este
  módulo. Qué herramientas están habilitadas para un agente concreto es
  configuración (`ENABLED_TOOLS`), interpretada aquí mismo
  (`resolve_tools`). La ejecución del bucle de llamada a herramientas
  durante una conversación (cuándo y cuántas veces se invoca una
  herramienta) pertenece a `MOD-MOTOR-IA`.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Resumen funcional

El repositorio incluye un catálogo de herramientas (`AVAILABLE_TOOLS`),
actualmente compuesto por una única herramienta, `search_web` (búsqueda en
DuckDuckGo sin necesidad de clave de API). Ninguna herramienta está
habilitada por defecto para un agente: cada instancia debe listar
explícitamente, en su configuración, los nombres de las herramientas que
quiere permitir al modelo usar. Cuando el modelo invoca una herramienta
habilitada, ésta se ejecuta de forma síncrona en un hilo aparte y su
resultado (texto) se reincorpora a la conversación con el modelo.

### Roles

- `ROL-OPERADOR`

### Entidades principales

- `ENT-HERRAMIENTA`

### Interfaces principales

- NONE — las herramientas no tienen interfaz propia; son invisibles para
  `ROL-USUARIO`, que sólo percibe el resultado incorporado a la respuesta
  del asistente.

### Funcionalidades

- `FUN-HERRAMIENTAS-001`

### Flujos internos

- NONE — el uso de una herramienta forma parte del flujo transversal
  `FLOW-GLOBAL-001`, definido en `_relations.md`.

### Reglas de negocio

- `RULE-HERRAMIENTAS-001`
- `RULE-HERRAMIENTAS-002`
- `RULE-HERRAMIENTAS-003`
- `RULE-HERRAMIENTAS-004`

### Automatismos

- NONE

### Módulos relacionados

- `MOD-MOTOR-IA`

### Fuentes principales

- `SRC-HERRAMIENTAS-CODE-001`
- `SRC-HERRAMIENTAS-CODE-002`

# 3. Fuentes y cobertura del módulo

## Fuentes analizadas

### SRC-HERRAMIENTAS-CODE-001

- **Tipo:** CODE
- **Ubicación:** `app/tools/base.py`, `app/tools/__init__.py`
- **Descripción:** Definición de `Tool` (dataclass), catálogo
  `AVAILABLE_TOOLS` y `resolve_tools()`.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-HERRAMIENTAS-CODE-002

- **Tipo:** CODE
- **Ubicación:** `app/tools/web_search.py`
- **Descripción:** Implementación de la herramienta `search_web`:
  construcción de la petición a DuckDuckGo, extracción de resultados,
  filtrado de anuncios y redacción de contenido que parezca un intento de
  inyección de instrucciones.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-HERRAMIENTAS-DOC-001

- **Tipo:** DOCUMENT
- **Ubicación:** `.env.example`
- **Descripción:** Documentación de `ENABLED_TOOLS` y de la herramienta
  disponible.
- **Fecha o versión:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-HERRAMIENTAS-TEST-001

- **Tipo:** TEST
- **Ubicación:** `tests/test_tools.py`
- **Descripción:** Confirma el comportamiento de `resolve_tools()` y de
  `search_web()` (extracción, filtrado de anuncios, redacción de
  inyecciones, manejo de fallos de red).
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
- **Integraciones relevantes:** COMPLETE (endpoint HTML de DuckDuckGo para
  `search_web`)

### Limitaciones

- NONE

# 4. Navegación e interfaces de usuario

NONE — las herramientas no exponen ninguna interfaz propia; se invocan
internamente por el modelo durante la generación de una respuesta en
`UI-CONVERSACION-CHAT` (definida en `mod-conversacion.md`).

# 5. Entidades funcionales

## ENT-HERRAMIENTA

- **Nombre:** Herramienta
- **Descripción:** Una capacidad del catálogo que el modelo puede invocar
  durante la conversación: nombre, descripción, esquema de parámetros (JSON
  Schema) y la función que la ejecuta.
- **Módulo propietario:** `MOD-HERRAMIENTAS`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Significado funcional

Cada herramienta representa una acción concreta que el modelo puede pedir
que se ejecute (por ejemplo, buscar en la web) en lugar de responder
únicamente con su conocimiento interno. El catálogo existe de forma
independiente de cualquier agente: estar en el catálogo no implica que un
agente concreto pueda usarla.

### Campos funcionalmente relevantes

| Campo | Nombre visible | Significado | Obligatorio | Editable | Restricciones |
|---|---|---|---|---|---|
| `name` | (no visible al usuario; sí al modelo) | Nombre único de la herramienta (p. ej. `search_web`) | YES | NO (fijado en el catálogo) | Debe ser único en `AVAILABLE_TOOLS` |
| `description` | (no visible al usuario; sí al modelo) | Explica al modelo cuándo y cómo usar la herramienta | YES | NO | NONE |
| `parameters` | (no visible) | Esquema JSON de los argumentos que la herramienta acepta | YES | NO | Debe ser un JSON Schema válido para `tool_choice`/`tools` del backend LLM |
| `execute` | (no visible) | Función síncrona que realiza la acción y devuelve un texto | YES | NO | Se ejecuta en un hilo aparte (`asyncio.to_thread`) para no bloquear el proceso |

### Roles relacionados

- `ROL-OPERADOR`: decide, vía `ENABLED_TOOLS`, qué herramientas del catálogo
  están disponibles para su agente.

### Creación

- **Quién puede crear:** Una herramienta nueva se añade al catálogo
  únicamente modificando el código del repositorio (nuevo módulo bajo
  `app/tools/`, registrado en `AVAILABLE_TOOLS`); no existe ninguna
  funcionalidad en tiempo de ejecución para crear herramientas.
- **Condiciones:** `NOT_APPLICABLE`
- **Funcionalidad:** NONE

### Modificación

- **Quién puede modificar:** NOT_APPLICABLE — el catálogo es fijo en tiempo
  de ejecución; sólo cambia entre versiones del código.

### Eliminación

- **Permitida:** NO — no existe una operación en tiempo de ejecución para
  eliminar una herramienta del catálogo. Retirar una herramienta del
  catálogo (en el código) hace que cualquier nombre que la referenciara en
  `ENABLED_TOOLS` quede simplemente ignorado (`RULE-HERRAMIENTAS-002`).
- **Condiciones:** `NOT_APPLICABLE`
- **Funcionalidad:** NONE

### Estados

NONE

### Relaciones

- NONE — `ENT-HERRAMIENTA` no tiene relaciones con otras entidades del
  scope más allá de su uso por `MOD-MOTOR-IA` (documentado como relación
  entre módulos, `REL-MOTORIA-HERRAMIENTAS`, en `_relations.md`).

### Reglas relacionadas

- `RULE-HERRAMIENTAS-001`
- `RULE-HERRAMIENTAS-002`

### Fuentes

- `SRC-HERRAMIENTAS-CODE-001` — `app/tools/base.py` → `Tool`,
  `app/tools/__init__.py` → `AVAILABLE_TOOLS`

# 6. Funcionalidades

## FUN-HERRAMIENTAS-001 — Uso de una herramienta durante la conversación

- **Nombre:** Uso de una herramienta durante la conversación
- **Módulo:** `MOD-HERRAMIENTAS`
- **Descripción:** Cuando el modelo, respondiendo a un mensaje del usuario,
  decide que necesita una herramienta habilitada (por ejemplo, buscar en la
  web información que no conoce con certeza), ésta se ejecuta y su
  resultado se incorpora a la respuesta final.
- **User-facing:** PARTIAL — la decisión de usar la herramienta la toma el
  modelo, no el usuario directamente; el usuario sólo percibe el resultado
  incorporado en la respuesta (y, en el caso de `search_web`, se le pide al
  modelo que cite la fuente).
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Roles autorizados

- `ROL-USUARIO` (de forma indirecta; no invoca la herramienta él mismo)

#### Interfaces de acceso

- `UI-CONVERSACION-CHAT` (definida en `mod-conversacion.md`)

#### Entidades implicadas

- `ENT-HERRAMIENTA`

#### Precondiciones

- La herramienta solicitada por el modelo debe estar en la lista de
  herramientas habilitadas para ese agente (`ENABLED_TOOLS`,
  `RULE-HERRAMIENTAS-001`).
- El backend LLM configurado debe soportar llamada a funciones/herramientas
  («tool/function calling»); si el modelo simplemente ignora las
  herramientas ofrecidas, no se activa ningún error explícito — el modelo
  responde sin usarlas.

#### Trigger / inicio

Durante la generación de una respuesta (`FUN-MOTORIA-001`), el modelo
solicita explícitamente el uso de una herramienta por su nombre y unos
argumentos.

#### Acción funcional

`MOD-MOTOR-IA` localiza la herramienta por nombre en el catálogo de
herramientas habilitadas, interpreta los argumentos que el modelo envió
(JSON) y ejecuta su función `execute` en un hilo aparte. El resultado
(siempre texto) se añade a la conversación como un mensaje de rol `tool`,
que el modelo puede leer en la siguiente ronda de generación.

#### Datos requeridos

- Nombre de la herramienta solicitada por el modelo.
- Argumentos de la herramienta, en formato JSON, según el esquema
  `parameters` de la herramienta (para `search_web`: `query`, texto de
  búsqueda).

#### Datos opcionales

- NONE

#### Resultado esperado

El modelo recibe el resultado textual de la herramienta y lo utiliza para
completar o corregir su respuesta al usuario.

#### Cambios de estado

- `NOT_APPLICABLE`

#### Datos creados o modificados

- Se añaden mensajes de rol `assistant` (con la solicitud de herramienta) y
  `tool` (con su resultado) al historial de la conversación en curso —
  estos mensajes intermedios no se persisten como parte del historial final
  guardado por `MOD-CONVERSACION` una vez terminada la ronda de generación.

#### Efectos secundarios

- `search_web` realiza una petición HTTP saliente a DuckDuckGo por cada
  invocación.

#### Módulos afectados

- `MOD-MOTOR-IA`

#### Reglas de negocio

- `RULE-HERRAMIENTAS-001`
- `RULE-HERRAMIENTAS-002`
- `RULE-HERRAMIENTAS-003`
- `RULE-HERRAMIENTAS-004`
- `RULE-MOTORIA-002` (límite de rondas, definida en `mod-motor-ia.md`)

#### Automatismos relacionados

- NONE

#### Restricciones

- Sólo existe una herramienta en el catálogo actual (`search_web`); el
  número de herramientas ofrecidas al modelo en una misma ronda no está
  limitado explícitamente más allá de las que estén habilitadas.

#### Excepciones y errores funcionales

- El modelo solicita un nombre de herramienta que no existe en el catálogo
  habilitado: se responde a la herramienta con «Unknown tool: {name}» y la
  conversación continúa (no se interrumpe).
- Los argumentos enviados por el modelo no son JSON válido: se tratan como
  un diccionario vacío en lugar de fallar.
- La ejecución de la herramienta lanza una excepción (p. ej. fallo de red en
  `search_web`): se captura y se devuelve al modelo el texto «The {name}
  tool failed to run.» en lugar de propagar el error
  (`RULE-HERRAMIENTAS-003`).
- `search_web` en particular nunca lanza una excepción por sí misma ante
  fallos de red o ausencia de resultados: devuelve un texto explicativo
  («The search returned no results...») para que el modelo no afirme con
  seguridad que algo no existe sólo porque la búsqueda falló.

#### Resultado visible para el usuario

Ninguno directamente visible como «uso de herramienta»; sólo se percibe el
efecto en el contenido de la respuesta final del asistente.

#### Funcionalidades relacionadas

- `FUN-MOTORIA-001`

#### Fuentes

- `SRC-HERRAMIENTAS-CODE-001` — `app/tools/base.py` → `Tool.schema()`
- `SRC-HERRAMIENTAS-CODE-002` — `app/tools/web_search.py` → `search_web()`
- `SRC-HERRAMIENTAS-TEST-001` — `tests/test_tools.py`

# 7. Reglas de negocio

## RULE-HERRAMIENTAS-001

- **Nombre:** Sólo las herramientas habilitadas por agente están disponibles
- **Módulo propietario:** `MOD-HERRAMIENTAS`
- **Descripción:** Ninguna herramienta del catálogo está disponible para un
  agente por el mero hecho de existir; sólo las que su configuración
  (`ENABLED_TOOLS`) lista explícitamente se ofrecen al modelo.
- **Condición:** Se va a generar una respuesta (`FUN-MOTORIA-001`).
- **Consecuencia:** Si `ENABLED_TOOLS` está vacío, el modelo nunca recibe
  ninguna herramienta y responde exactamente igual que antes de que el
  sistema de herramientas existiera.
- **Roles afectados:** `ROL-OPERADOR`
- **Entidades afectadas:** `ENT-HERRAMIENTA`
- **Funcionalidades afectadas:** `FUN-HERRAMIENTAS-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-HERRAMIENTAS-CODE-001` — `app/tools/__init__.py` →
  `resolve_tools()`; `SRC-CONVERSACION-CODE-001` — `app/bot.py` →
  `_reply_to()`

## RULE-HERRAMIENTAS-002

- **Nombre:** Nombres de herramienta desconocidos se ignoran silenciosamente
- **Módulo propietario:** `MOD-HERRAMIENTAS`
- **Descripción:** Si `ENABLED_TOOLS` contiene un nombre que no existe en el
  catálogo (por ejemplo, una herramienta que el template retiró
  posteriormente), ese nombre se ignora en lugar de producir un error.
- **Condición:** `ENABLED_TOOLS` contiene un nombre ausente de
  `AVAILABLE_TOOLS`.
- **Consecuencia:** El agente sigue arrancando con normalidad, simplemente
  sin esa herramienta.
- **Roles afectados:** `ROL-OPERADOR`
- **Entidades afectadas:** `ENT-HERRAMIENTA`
- **Funcionalidades afectadas:** `FUN-HERRAMIENTAS-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-HERRAMIENTAS-CODE-001` — `app/tools/__init__.py` →
  `resolve_tools()`

## RULE-HERRAMIENTAS-003

- **Nombre:** Un fallo de herramienta nunca interrumpe la conversación
- **Módulo propietario:** `MOD-HERRAMIENTAS`
- **Descripción:** Cualquier excepción producida al ejecutar una herramienta
  se captura y se convierte en un mensaje de resultado de herramienta
  indicando el fallo, en lugar de propagarse y romper la respuesta al
  usuario.
- **Condición:** La función `execute` de una herramienta lanza una
  excepción.
- **Consecuencia:** El modelo recibe «The {name} tool failed to run.» como
  resultado de la herramienta y puede continuar generando una respuesta con
  esa información.
- **Roles afectados:** `ROL-USUARIO` (beneficiario: no ve caer la
  conversación)
- **Entidades afectadas:** `ENT-HERRAMIENTA`
- **Funcionalidades afectadas:** `FUN-HERRAMIENTAS-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-HERRAMIENTAS-CODE-001`(uso genérico) — realmente
  implementada en `app/llm.py` → `_call_tool()` (ver `mod-motor-ia.md`,
  `RULE-MOTORIA-002` para el contexto del bucle); documentada aquí porque
  afecta directamente al contrato funcional de toda herramienta del
  catálogo.

## RULE-HERRAMIENTAS-004

- **Nombre:** Los resultados de búsqueda se tratan como contenido no
  confiable
- **Módulo propietario:** `MOD-HERRAMIENTAS`
- **Descripción:** El texto de título y fragmento de cada resultado de
  `search_web` se comprueba contra patrones típicos de intento de inyección
  de instrucciones (p. ej. «ignore previous instructions», «reveal the
  system prompt»); si coincide, el contenido de ese resultado se sustituye
  por un aviso de redacción en lugar de pasarlo tal cual al modelo.
- **Condición:** El título o el fragmento de un resultado de búsqueda
  coincide con alguno de los patrones de inyección conocidos.
- **Consecuencia:** Ese resultado se muestra al modelo como «[external
  content omitted: looked like a prompt-injection attempt]» en lugar de su
  contenido original.
- **Roles afectados:** `ROL-USUARIO` (beneficiario indirecto)
- **Entidades afectadas:** `ENT-HERRAMIENTA`
- **Funcionalidades afectadas:** `FUN-HERRAMIENTAS-001`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** `SRC-HERRAMIENTAS-CODE-002` — `app/tools/web_search.py` →
  `_looks_like_injection()`, `_INJECTION_PATTERNS`

# 8. Automatismos

NONE — la invocación de una herramienta siempre es resultado de una
decisión del modelo dentro de una ronda de generación ya iniciada por un
mensaje del usuario; no existe ningún trigger independiente de esa cadena.

# 9. Flujos internos

NONE — el flujo relevante (`FLOW-GLOBAL-001`) es transversal entre
`MOD-CONVERSACION`, `MOD-MOTOR-IA` y `MOD-HERRAMIENTAS`, y se define en
`_relations.md`.

# 10. Incertidumbres del módulo

## Información inferida

### INF-HERRAMIENTAS-001

- **Elemento:** `FUN-HERRAMIENTAS-001` (`User-facing: PARTIAL`)
- **Inferencia:** Se ha clasificado como `PARTIAL` en lugar de `NO` porque,
  aunque el usuario no invoca la herramienta directamente, su mensaje es lo
  que desencadena que el modelo decida usarla, y el resultado influye
  directamente en lo que el usuario recibe.
- **Motivo:** No hay ninguna acción de UI explícita para «buscar en la
  web»; la decisión es enteramente del modelo.
- **Fuentes:** `SRC-CONVERSACION-CODE-001` — `app/bot.py` → `_reply_to()`;
  `SRC-HERRAMIENTAS-CODE-001` — `app/llm.py` → `_run_with_tools()`
- **Impacto documental:** LOW

## Información desconocida

NONE

## Conflictos

NONE

## Implementaciones parciales

NONE

# 11. Trazabilidad del módulo

| Elemento | Tipo | Estado | Evidencia | Fuentes principales |
|---|---|---|---|---|
| `MOD-HERRAMIENTAS` | Módulo | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-001`, `SRC-HERRAMIENTAS-CODE-002` |
| `ENT-HERRAMIENTA` | Entidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-001` |
| `FUN-HERRAMIENTAS-001` | Funcionalidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-001`, `SRC-HERRAMIENTAS-CODE-002`, `SRC-HERRAMIENTAS-TEST-001` |
| `RULE-HERRAMIENTAS-001` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-001` |
| `RULE-HERRAMIENTAS-002` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-001` |
| `RULE-HERRAMIENTAS-003` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-001` |
| `RULE-HERRAMIENTAS-004` | Regla | `IMPLEMENTED` | `CONFIRMED` | `SRC-HERRAMIENTAS-CODE-002` |

# 12. Validación del fichero

## Resultado

- Front matter completo y conforme a la sección 6 del schema.
- Todas las secciones obligatorias están presentes; las vacías están
  explícitamente marcadas `NONE` con su justificación.
- Todas las referencias externas a este módulo (`FUN-MOTORIA-001`,
  `RULE-MOTORIA-002`, `UI-CONVERSACION-CHAT`) están definidas en
  `mod-motor-ia.md` o `mod-conversacion.md`.

## Limitaciones

- NONE
