---
document-type: canonical-functional-source
schema-version: 2.1
scope-id: bot
scope-name: Bot de Telegram
part: ROLES
module-id: NOT_APPLICABLE
content-language: es
generated-at: 2026-09-18
source-commit: 25166ca4e6babcd070dea4e2d76030d024329fd8
source-branch: main
generation-status: COMPLETE
---

# CFS — Bot de Telegram — Roles y modelo de acceso

# 1. Metainformación

## Fuentes

### SRC-GLOBAL-CODE-001

- **Tipo:** CODE
- **Ubicación:** `app/bot.py`
- **Descripción:** `_is_allowed()`, `_has_access()` — control de acceso por
  lista blanca de usuarios.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-GLOBAL-CODE-002

- **Tipo:** CODE
- **Ubicación:** `app/config.py`
- **Descripción:** `Config.load()` — lectura de toda la configuración por
  variables de entorno.
- **Versión / commit:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-GLOBAL-DOC-001

- **Tipo:** DOCUMENT
- **Ubicación:** `.env.example`
- **Descripción:** Documentación de todas las variables de entorno que
  configura `ROL-OPERADOR`.
- **Fecha o versión:** 25166ca4e6babcd070dea4e2d76030d024329fd8
- **Analizada:** YES
- **Observaciones:** NONE

# 2. Roles

## ROL-USUARIO

- **Nombre:** Usuario de Telegram
- **Descripción:** Persona que conversa con el bot desde Telegram, con el
  chat 1:1 con el bot como único punto de acceso.
- **Responsabilidad funcional:** Iniciar la conversación, enviar mensajes de
  texto y notas de voz, y recibir las respuestas del asistente.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Acceso a módulos

- `MOD-CONVERSACION`
- `MOD-VOZ`

### Capacidades principales

- Enviar el comando `/start` (`FUN-CONVERSACION-001`).
- Enviar un mensaje de texto y recibir respuesta (`FUN-CONVERSACION-002`).
- Enviar una nota de voz o un archivo de audio y recibir respuesta
  (`FUN-VOZ-001`).

### Restricciones

- No puede configurar el bot (backend LLM, herramientas habilitadas, modelo
  de voz, zona horaria, etc.): esa configuración es responsabilidad de
  `ROL-OPERADOR` y se define fuera de la conversación de Telegram (variables
  de entorno).
- No tiene visibilidad de si el bot está usando una herramienta ni de qué
  backend LLM responde: ambos son transparentes para este rol.

### Condiciones adicionales de acceso

- **Propiedad del registro:** El historial de conversación de un chat sólo
  es accesible desde ese mismo chat de Telegram (identificado por
  `chat_id`); no existe una operación que permita a un usuario ver el
  historial de otro chat.
- **Empresa / tenant:** `NOT_APPLICABLE` — el bot no tiene concepto de
  organización o tenant.
- **Equipo / departamento:** `NOT_APPLICABLE`
- **Estado del elemento:** `NOT_APPLICABLE`
- **Permisos adicionales:** El acceso al bot en su conjunto depende de
  `RULE-CONVERSACION-001` (lista blanca `ALLOWED_USER_IDS`), configurada por
  `ROL-OPERADOR`.

### Fuentes

- `SRC-GLOBAL-CODE-001` — `app/bot.py` → `_is_allowed()`, `_has_access()`

## ROL-OPERADOR

- **Nombre:** Operador / titular del agente
- **Descripción:** Persona que despliega y configura una instancia
  («agente») del bot mediante variables de entorno (`.env`) y el fichero de
  prompt de sistema, antes o durante el funcionamiento del contenedor. No
  interactúa con el bot a través de Telegram en esta capacidad.
- **Responsabilidad funcional:** Determinar, para su instancia, qué usuarios
  de Telegram tienen acceso, qué backend LLM se usa, qué herramientas están
  habilitadas, el modelo de transcripción de voz, la zona horaria y los
  presupuestos de historial de conversación.
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Acceso a módulos

- `MOD-CONVERSACION`
- `MOD-VOZ`
- `MOD-HERRAMIENTAS`
- `MOD-MOTOR-IA`

### Capacidades principales

- Definir la lista blanca de usuarios autorizados (`ALLOWED_USER_IDS`,
  `RULE-CONVERSACION-001`).
- Elegir el backend LLM y sus parámetros (`RULE-MOTORIA-001`).
- Habilitar herramientas para el modelo (`RULE-HERRAMIENTAS-001`).
- Elegir el modelo de transcripción de voz (`WHISPER_MODEL`, ver
  `mod-voz.md`).
- Ajustar los presupuestos de historial de conversación
  (`MAX_HISTORY_TOKENS`, `RECENT_HISTORY_TOKENS`, ver `mod-conversacion.md`).
- Personalizar el nombre y la personalidad del agente (`AGENT_NAME`, prompt
  de sistema) — el mecanismo de aplicación se documenta en
  `mod-conversacion.md`; el contenido concreto queda fuera de este scope
  (ver `scopes/bot/README.md`).

### Restricciones

- No dispone de una interfaz dentro de Telegram para esta configuración: se
  realiza fuera del alcance de este scope (variables de entorno / ficheros
  de configuración del host), no mediante comandos del bot.

### Condiciones adicionales de acceso

- **Propiedad del registro:** `NOT_APPLICABLE`
- **Empresa / tenant:** `NOT_APPLICABLE`
- **Equipo / departamento:** `NOT_APPLICABLE`
- **Estado del elemento:** `NOT_APPLICABLE`
- **Permisos adicionales:** NONE — el acceso de este rol no está mediado por
  el propio bot (no hay autenticación en el bot para configurarlo); depende
  del acceso al host/instancia donde corre el contenedor, fuera del alcance
  funcional de este CFS.

### Fuentes

- `SRC-GLOBAL-CODE-002` — `app/config.py` → `Config.load()`
- `SRC-GLOBAL-DOC-001` — `.env.example`

# 3. Capabilities / permisos configurables

NONE — el producto no implementa un sistema de permisos granulares
configurable (`CAP-`) independiente de los dos roles anteriores. El único
control de acceso es la lista blanca binaria de `RULE-CONVERSACION-001`, que
determina si un usuario de Telegram pertenece o no a `ROL-USUARIO`.

# 4. Matriz rol → módulo

| Rol | MOD-CONVERSACION | MOD-VOZ | MOD-HERRAMIENTAS | MOD-MOTOR-IA |
|---|---|---|---|---|
| `ROL-USUARIO` | Acceso | Acceso | Sin acceso directo (transparente) | Sin acceso directo (transparente) |
| `ROL-OPERADOR` | Acceso (configuración) | Acceso (configuración) | Acceso (configuración) | Acceso (configuración) |

`ROL-USUARIO` nunca interactúa directamente con `MOD-HERRAMIENTAS` ni
`MOD-MOTOR-IA`: son invocados internamente al generar una respuesta (ver
`REL-CONVERSACION-MOTORIA` y `REL-MOTORIA-HERRAMIENTAS` en `_relations.md`).
`ROL-OPERADOR` accede a todos los módulos únicamente a través de su
configuración (variables de entorno), no mediante una interfaz de usuario
dentro de la aplicación.

# 5. Incertidumbres

## Información desconocida

### UNK-GLOBAL-002

- **Elemento:** `ROL-OPERADOR`
- **Información no determinada:** No existe evidencia de que exista más de
  un operador por instancia ni de ningún mecanismo de autenticación o
  auditoría sobre quién cambia la configuración; se asume que corresponde a
  quien tiene acceso al host/repositorio del agente.
- **Fuentes revisadas:** `app/config.py`, `.env.example`, `CLAUDE.md`
- **Qué sería necesario para resolverlo:** No aplica dentro de este scope;
  sería una cuestión de gestión de acceso al host, fuera del alcance del
  bot.
- **Impacto documental:** LOW

# 6. Validación del fichero

## Resultado

- Front matter completo y conforme a la sección 6 del schema.
- Los dos roles identificados (`ROL-USUARIO`, `ROL-OPERADOR`) cubren la
  totalidad de las interacciones observadas en el código.
- La matriz rol → módulo cubre los cuatro módulos del scope.
- No se han identificado capabilities configurables; la sección 3 se deja
  explícitamente como `NONE`.
