# CFS — Functional Schema

**Schema:** Canonical Functional Source  
**Versión del schema:** `2.1`  
**Idioma de esta especificación:** Español (`es`)

---

## ÍNDICE

- [[#1-objetivo-del-schema]]
- [[#2-principios-normativos]]
- [[#3-valores-normalizados]]
- [[#4-sistema-de-identificadores]]
- [[#5-referencias-entre-scopes]]
- [[#6-metadatos-del-documento]]
- [[#7-estructura-del-cfs-multi-fichero]]
- [[#8-scope-y-límites-funcionales]]
- [[#9-fuentes-y-cobertura-del-análisis]]
- [[#10-visión-funcional-global]]
- [[#11-roles-y-modelo-de-acceso]]
- [[#12-navegación-e-interfaces-de-usuario]]
- [[#13-entidades-funcionales]]
- [[#14-módulos]]
- [[#15-funcionalidades]]
- [[#16-reglas-de-negocio]]
- [[#17-automatismos]]
- [[#18-flujos-de-trabajo]]
- [[#19-relaciones-entre-módulos]]
- [[#20-flujos-transversales]]
- [[#21-glosario-funcional]]
- [[#22-incertidumbres-conflictos-y-carencias]]
- [[#23-trazabilidad]]
- [[#24-reglas-para-evitar-duplicación]]
- [[#25-información-que-no-debe-incluirse]]
- [[#26-reglas-de-redacción]]
- [[#27-validación-final]]
- [[#28-esqueleto-del-documento-generado]]
- [[#29-evolución-del-schema]]

---

# 1. OBJETIVO DEL SCHEMA

Este documento define el contrato estructural que debe cumplir cualquier **CFS — Canonical Functional Source** generado mediante la metodología del proyecto.

El CFS es una representación funcional, estructurada, canónica e intermedia del comportamiento real de un sistema o de uno de sus scopes.

Este schema establece:

- Qué información debe contener un CFS.
- Cómo debe organizarse.
- Cómo deben identificarse sus elementos.
- Cómo deben representarse módulos, funcionalidades, roles, entidades, estados, flujos y relaciones.
- Cómo debe indicarse la evidencia que respalda una afirmación.
- Cómo deben representarse incertidumbres, conflictos y carencias.
- Cómo deben establecerse referencias entre elementos.
- Cómo deben establecerse referencias entre scopes distintos.
- Qué información debe evitarse.
- Qué condiciones debe cumplir un CFS antes de considerarse válido.

El objetivo es que agentes posteriores puedan utilizar el CFS como fuente funcional de referencia para generar:

- Manuales de usuario.
- Documentación funcional.
- Infografías.
- Diagramas.
- Flujos visuales.
- Diagramas de estados.
- Matrices de permisos.
- Material de onboarding.
- Ayuda contextual.
- Otros artefactos funcionales derivados.

Los agentes consumidores del CFS no deberían necesitar consultar nuevamente el código fuente o la documentación de desarrollo para reconstruir el comportamiento funcional descrito.

---

# 2. PRINCIPIOS NORMATIVOS

En este documento se utilizan los siguientes términos:

- **DEBE**: requisito obligatorio.
- **NO DEBE**: comportamiento prohibido.
- **DEBERÍA**: comportamiento recomendado salvo motivo justificado.
- **PUEDE**: comportamiento opcional.

Un CFS conforme a este schema **DEBE** respetar todos los requisitos marcados como obligatorios.

## 2.1 El CFS describe el sistema, no cómo debería ser el sistema

El CFS DEBE representar el comportamiento funcional que pueda determinarse a partir de las fuentes disponibles.

NO DEBE completar huecos basándose únicamente en:

- buenas prácticas generales;
- comportamientos habituales de otros ERP;
- expectativas del agente;
- funcionalidades que "tendrían sentido";
- interpretaciones no respaldadas por las fuentes.

---

## 2.2 Separación entre certeza e implementación

Deben distinguirse dos conceptos diferentes:

1. **Estado de evidencia**: cuánto sabemos sobre una afirmación.
2. **Estado de implementación**: en qué situación se encuentra la funcionalidad en el producto.

Por ejemplo, una funcionalidad puede estar:

```text
implementation-status: PLANNED
evidence-status: CONFIRMED
```

si existe documentación inequívoca indicando que está planificada pero todavía no implementada.

Del mismo modo:

```text
implementation-status: IMPLEMENTED
evidence-status: INFERRED
```

si el código parece implementarla pero no se ha podido confirmar completamente su comportamiento funcional.

---

## 2.3 Una única definición canónica

Cada concepto funcional DEBE tener una ubicación canónica dentro del CFS.

Cuando aparezca en otras secciones, deberá referenciarse mediante su identificador en lugar de redefinirse completamente.

---

## 2.4 Trazabilidad

Toda afirmación funcional relevante DEBE poder relacionarse, siempre que sea posible, con una o más fuentes.

Los elementos marcados como `CONFIRMED` DEBEN incluir evidencia suficiente para justificar dicha clasificación.

---

## 2.5 Orientación funcional

El CFS debe describir principalmente:

- Qué puede hacer el usuario.
- Quién puede hacerlo.
- Sobre qué elemento actúa.
- Desde dónde puede hacerlo.
- Bajo qué condiciones.
- Qué información necesita.
- Qué resultado obtiene.
- Qué cambia en el sistema.
- Qué efectos secundarios se producen.
- Cómo afecta a otros módulos.
- Qué excepciones pueden producirse.

Los detalles técnicos sólo se incluirán cuando ayuden a:

- verificar una afirmación;
- comprender el comportamiento funcional;
- localizar su implementación;
- explicar una integración funcional relevante.

---

# 3. VALORES NORMALIZADOS

Para evitar ambigüedades se utilizarán los siguientes valores estándar.

## 3.1 Estado de evidencia

Valores permitidos:

### `CONFIRMED`

La información puede verificarse suficientemente mediante una o varias fuentes.

### `INFERRED`

La información se deduce razonablemente de las fuentes, pero no puede confirmarse completamente.

Debe explicarse brevemente la inferencia.

### `UNKNOWN`

No existe información suficiente para determinar el comportamiento.

### `CONFLICT`

Dos o más fuentes proporcionan información incompatible y no es posible resolver la contradicción con suficiente seguridad.

Deben identificarse las fuentes en conflicto.

---

## 3.2 Estado de implementación

Valores permitidos:

### `IMPLEMENTED`

Existe evidencia suficiente de que la funcionalidad está implementada actualmente.

### `PARTIAL`

Existe implementación, pero sólo cubre parte del comportamiento previsto o documentado.

### `PLANNED`

La funcionalidad aparece en planes o especificaciones, pero no existe evidencia suficiente de implementación actual.

### `DEPRECATED`

La funcionalidad sigue existiendo o aparece en las fuentes, pero está marcada como obsoleta o en proceso de retirada.

### `REMOVED`

Existe evidencia de que la funcionalidad existió anteriormente pero ya no forma parte del comportamiento actual.

### `UNKNOWN`

No puede determinarse su estado de implementación.

---

## 3.3 Valores para ausencia de información

No deben confundirse los siguientes valores:

### `NONE`

Se ha determinado que no existe ningún elemento de ese tipo.

Ejemplo:

```text
Efectos secundarios: NONE
```

significa que se ha comprobado que la operación no produce efectos secundarios relevantes.

### `NOT_APPLICABLE`

El campo no tiene sentido para este elemento.

Ejemplo:

```text
Cambio de estado: NOT_APPLICABLE
```

para una consulta que no modifica datos.

### `UNKNOWN`

El dato podría existir o ser relevante, pero no ha podido determinarse.

NO DEBE utilizarse `NONE` para ocultar desconocimiento.

---

# 4. SISTEMA DE IDENTIFICADORES

Los elementos funcionales principales DEBEN utilizar identificadores estables.

Los identificadores permiten:

- referencias cruzadas;
- generación automatizada;
- trazabilidad;
- comparación entre versiones;
- generación de diagramas;
- análisis por agentes;
- evitar duplicaciones.

## 4.1 Reglas generales

Los IDs:

- DEBEN estar en ASCII.
- DEBEN estar en mayúsculas.
- DEBEN utilizar guiones como separador.
- NO DEBEN contener espacios.
- NO DEBEN contener tildes.
- NO DEBEN contener `ñ`.
- DEBEN ser únicos dentro del scope.
- DEBEN mantenerse estables entre regeneraciones siempre que el concepto siga siendo el mismo.
- NO DEBEN reutilizarse para otro concepto después de eliminarse uno anterior.

---

## 4.2 Prefijos estándar

Se utilizarán los siguientes prefijos:

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Módulo | `MOD-` | `MOD-TAREAS` |
| Funcionalidad | `FUN-` | `FUN-TAREAS-001` |
| Rol | `ROL-` | `ROL-ADMINISTRADOR` |
| Entidad | `ENT-` | `ENT-TAREA` |
| Estado | `STA-` | `STA-TAREA-CERRADA` |
| Flujo | `FLOW-` | `FLOW-TAREAS-001` |
| Regla de negocio | `RULE-` | `RULE-TAREAS-001` |
| Automatismo | `AUTO-` | `AUTO-TAREAS-001` |
| Superficie UI | `UI-` | `UI-TAREAS-LISTADO` |
| Relación | `REL-` | `REL-PROYECTO-TAREA` |
| Capability / permiso | `CAP-` | `CAP-TAREAS-CERRAR` |
| Fuente | `SRC-` | `SRC-TAREAS-CODE-001` |

---

## 4.3 IDs de funcionalidades

Las funcionalidades pertenecientes principalmente a un módulo DEBERÍAN seguir:

```text
FUN-<MODULO>-<NNN>
```

Ejemplo:

```text
FUN-TAREAS-001
FUN-TAREAS-002
FUN-TAREAS-003
```

Los números NO implican prioridad ni orden de ejecución.

Cuando se añada una funcionalidad nueva, NO DEBEN renumerarse las anteriores.

---

## 4.4 IDs semánticos frente a IDs numéricos

Para elementos conceptualmente estables se prefieren IDs semánticos:

```text
MOD-TAREAS
ENT-TAREA
ROL-ADMINISTRADOR
STA-TAREA-CERRADA
```

Para elementos numerosos o cuya denominación pueda evolucionar se prefieren IDs numerados:

```text
FUN-TAREAS-001
FLOW-TAREAS-002
RULE-TAREAS-004
```

---

## 4.5 IDs y ficheros

El CFS de un scope se compone de varios ficheros (ver sección 7).

- Cada ID DEBE definirse canónicamente en exactamente un fichero del scope, determinado por las reglas de ubicación de la sección 7.3.
- Las referencias a un ID desde cualquier fichero del mismo scope utilizan el ID directamente, sin rutas de fichero.
- Los IDs son independientes de la organización física en ficheros: reorganizar ficheros NO DEBE alterar ningún ID ni ninguna referencia.
- La unicidad de IDs se evalúa a nivel de scope completo, no por fichero.

---

# 5. REFERENCIAS ENTRE SCOPES

Cada CFS pertenece a un scope.

Una referencia a un elemento del mismo scope utilizará directamente su ID:

```text
MOD-TAREAS
FUN-TAREAS-001
ENT-TAREA
```

con independencia del fichero físico en el que dicho elemento esté definido (ver sección 4.5).

Una referencia a un elemento perteneciente a otro scope utilizará:

```text
<scope-id>::<element-id>
```

Ejemplos:

```text
legna-core::MOD-FILES
nexus-core::ENT-AI-AGENT
fontenebro-nexus::FUN-AGENTS-003
```

Las referencias externas:

- NO deben provocar la duplicación completa de la definición externa.
- DEBEN explicar únicamente la relación relevante para el scope actual.
- DEBEN marcarse como `UNKNOWN` si el scope externo todavía no dispone de CFS y la relación no puede verificarse completamente.
- DEBEN estar declaradas en la sección «Dependencias entre scopes» de `_relations.md` del scope que las utiliza.
- DEBEN marcarse como provisionales (`Provisional: YES`) en dicha declaración mientras el scope externo no disponga de CFS; el ID externo es entonces un identificador propuesto que deberá revisarse cuando dicho CFS exista.

---

# 6. METADATOS DEL DOCUMENTO

Todos los ficheros que componen el CFS de un scope (ver sección 7) DEBEN comenzar con front matter YAML.

Formato obligatorio:

```yaml
---
document-type: canonical-functional-source
schema-version: 2.0
scope-id: erp
scope-name: ERP
part: INDEX | ROLES | GLOSSARY | RELATIONS | MODULE
module-id: <MOD-... | NOT_APPLICABLE>
content-language: es
generated-at: YYYY-MM-DD
source-commit: <commit | UNKNOWN>
source-branch: <branch | UNKNOWN>
generation-status: COMPLETE | PARTIAL
---
```

Los campos `generated-at`, `source-commit`, `source-branch` y `generation-status` son **por fichero**: cada fichero refleja cuándo y contra qué commit se generó o actualizó por última vez. Esto permite conocer la frescura de cada módulo de forma independiente.

## 6.1 `document-type`

Valor obligatorio:

```text
canonical-functional-source
```

---

## 6.2 `schema-version`

Versión de `functional-schema.md` utilizada para generar el documento.

---

## 6.3 `scope-id`

Identificador técnico estable del scope.

Ejemplo:

```text
erp
```

---

## 6.4 `scope-name`

Nombre legible del ámbito funcional.

Ejemplo:

```text
ERP
```

---

## 6.5 `content-language`

Código de idioma utilizado en el contenido funcional.

Ejemplos:

```text
es
en
fr
pt
```

---

## 6.6 `generated-at`

Fecha en la que se realizó la última extracción o actualización del contenido del fichero (la fecha del análisis, no la de ediciones posteriores menores).

Formato:

```text
YYYY-MM-DD
```

---

## 6.7 `source-commit`

Commit del repositorio contra el que se realizó la extracción cuando pueda determinarse.

Si no puede determinarse:

```text
UNKNOWN
```

---

## 6.8 `source-branch`

Branch analizada cuando pueda determinarse.

---

## 6.9 `generation-status`

Valores:

### `COMPLETE`

El agente ha podido revisar el ámbito previsto y considera que el documento satisface las comprobaciones de este schema.

No implica que toda la información sea conocida.

Puede haber elementos `UNKNOWN`, siempre que estén correctamente identificados.

### `PARTIAL`

No ha podido analizarse parte relevante del scope o de sus fuentes.

La causa DEBE explicarse en la sección de cobertura.

---

## 6.10 `part`

Tipo de fichero dentro del CFS:

- `INDEX` — `_index.md`
- `ROLES` — `_roles.md`
- `GLOSSARY` — `_glossary.md`
- `RELATIONS` — `_relations.md`
- `MODULE` — `mod-<modulo>.md`

---

## 6.11 `module-id`

ID del módulo documentado (`MOD-...`) cuando `part: MODULE`.

En los ficheros globales:

```text
NOT_APPLICABLE
```

El nombre del fichero DEBE derivarse de `module-id` conforme a la sección 7.1.

---

# 7. ESTRUCTURA DEL CFS (MULTI-FICHERO)

Desde la versión 2.0 del schema, el CFS de un scope NO es un único fichero sino un conjunto de ficheros bajo:

```text
scopes/<scope>/functional-source/
```

## 7.1 Conjunto de ficheros

```text
scopes/<scope>/functional-source/
├── _index.md          (obligatorio)
├── _roles.md          (obligatorio)
├── _glossary.md       (obligatorio)
├── _relations.md      (obligatorio)
└── mod-<modulo>.md    (uno por módulo)
```

Reglas de nomenclatura:

- Los ficheros globales llevan prefijo `_` (ordenan primero y no pueden colisionar con nombres de módulo).
- Cada módulo tiene exactamente un fichero, cuyo nombre DEBE derivarse de su ID: minúsculas del ID sin el prefijo `MOD-`, conservando los guiones.

```text
MOD-TAREAS   → mod-tareas.md
MOD-COMPRAS  → mod-compras.md
```

- NO DEBE subdividirse un módulo en varios ficheros. Si un fichero de módulo resulta desproporcionado, debe evaluarse si funcionalmente se trata de dos módulos.

## 7.2 Contenido obligatorio de cada fichero

### `_index.md`

1. Metainformación (resumen de generación e inventario de ficheros)
2. Scope y límites
3. Cobertura global (resumen)
4. Visión funcional global
5. Módulos pendientes de extracción (stubs, ver sección 7.7)
6. Entidades sin módulo propietario claro (si existen)
7. Incertidumbres globales o transversales
8. Validación de scope

El inventario de ficheros DEBE ser una tabla con una fila por fichero del CFS:

```text
| Fichero | Part | Módulo | generated-at | source-commit | generation-status |
```

Este inventario permite conocer la frescura de cada parte del CFS sin abrir cada fichero.

El inventario sólo lista ficheros existentes; los módulos identificados pero aún sin fichero aparecen como stubs en la sección «Módulos pendientes de extracción» (sección 7.7).

### `_roles.md`

1. Metainformación
2. Roles y modelo de acceso (definiciones canónicas `ROL-`)
3. Capabilities / permisos configurables (`CAP-`), cuando el producto los utilice
4. Matriz rol → módulo
5. Incertidumbres propias
6. Validación del fichero

### `_glossary.md`

1. Metainformación
2. Glosario funcional completo del scope
3. Validación del fichero

### `_relations.md`

1. Metainformación
2. Relaciones entre módulos (definiciones canónicas de `REL-` inter-módulo)
3. Relaciones entre entidades pertenecientes a módulos distintos
4. Flujos transversales (`FLOW-GLOBAL-...`)
5. Dependencias entre scopes
6. Resumen de relaciones intra-módulo (solo ID y una línea; la definición canónica permanece en el fichero del módulo)
7. Incertidumbres propias
8. Validación del fichero

### `mod-<modulo>.md`

1. Metainformación del módulo
2. Definición del módulo (`MOD-...`)
3. Fuentes y cobertura del módulo
4. Navegación e interfaces de usuario (`UI-...`)
5. Entidades funcionales en propiedad (`ENT-...`, con sus `STA-...`, transiciones y `REL-...` intra-módulo)
6. Funcionalidades (`FUN-...`)
7. Reglas de negocio (`RULE-...`)
8. Automatismos (`AUTO-...`)
9. Flujos internos (`FLOW-...`)
10. Incertidumbres del módulo
11. Trazabilidad del módulo
12. Validación del fichero

## 7.3 Reglas de ubicación

Cada elemento se define canónicamente en un único fichero, determinado por estas reglas:

| Elemento | Fichero donde se define |
|---|---|
| `MOD-X` | `mod-x.md`; mientras esté pendiente de extracción, stub en `_index.md` (sección 7.7) |
| `FUN-`, `RULE-`, `AUTO-`, `UI-` de un módulo | fichero de su módulo |
| `ENT-` | fichero de su módulo propietario |
| `STA-` y transiciones | junto a su entidad |
| `REL-` con origen y destino en el mismo módulo | fichero del módulo |
| `REL-` entre módulos distintos | `_relations.md` |
| `FLOW-` interno de un módulo | fichero del módulo |
| `FLOW-GLOBAL-` transversal | `_relations.md` |
| `ROL-`, `CAP-` | `_roles.md` |
| Términos del glosario | `_glossary.md` |
| `SRC-`, `INF-`, `UNK-`, `CONFLICT-`, `PARTIAL-` | fichero que los utiliza (secciones 9 y 22) |

Módulo propietario de una entidad: aquel que gestiona su ciclo de vida principal (alta, modificación, eliminación). Si no puede determinarse un propietario claro, la entidad se define en `_index.md`.

Estas reglas DEBEN aplicarse de forma determinista: dos regeneraciones del mismo contenido DEBEN ubicar cada elemento en el mismo fichero.

## 7.4 Autocontención para consumo

La unidad de consumo prevista para generar un artefacto de un módulo es:

```text
_index.md + _roles.md + _glossary.md + mod-<modulo>.md
```

añadiendo `_relations.md` cuando el artefacto sea transversal.

Cada fichero de módulo DEBE ser comprensible utilizando únicamente ese conjunto, sin necesidad de abrir los ficheros de otros módulos.

## 7.5 Secciones obligatorias

Las secciones obligatorias de cada fichero NO DEBEN omitirse aunque no existan elementos.

Cuando una sección no tenga contenido debe indicarse explícitamente:

```text
NONE
```

o:

```text
UNKNOWN
```

según corresponda.

## 7.6 Aplicación de los formatos de este schema

Los formatos de elemento definidos en los capítulos 8 a 23 siguen siendo aplicables. Los encabezados y la numeración de secciones mostrados dentro de dichos formatos deben adaptarse a la numeración del fichero correspondiente, según los esqueletos de la sección 28.

## 7.7 Módulos pendientes de extracción

Los IDs de módulo se asignan para todo el scope en la pasada de inventario, aunque la mayoría de los módulos todavía no se hayan extraído.

Un módulo identificado pero aún sin fichero propio se define como **stub** en `_index.md`:

```md
### MOD-VENTAS

- **Nombre:** Ventas
- **Descripción provisional:** ...
- **Extraction:** PENDING
- **Evidence status:** `UNKNOWN`
```

Reglas:

- El stub es la definición canónica temporal del módulo: las referencias desde cualquier fichero del scope utilizan su ID con normalidad (también en `REL-` y flujos).
- Un módulo con stub NO aparece en el inventario de ficheros (no tiene fichero) y no requiere columna propia en la matriz rol → módulo.
- Al extraer el módulo, el stub se elimina de `_index.md` y la definición canónica pasa a `mod-<modulo>.md`, conservando el ID.
- Si la extracción revela que un stub agrupaba en realidad varios módulos (o lo contrario), se aplica el criterio de actualización conservadora: los IDs sólo cambian si cambia la identidad funcional, y el cambio se registra como incidencia.

---

# 8. SCOPE Y LÍMITES FUNCIONALES

Esta sección DEBE explicar claramente qué forma parte del CFS y qué queda fuera.

Formato:

```md
# 2. Scope y límites

## Scope

- **ID:** `erp`
- **Nombre:** ERP
- **Descripción:** ...
- **Evidence status:** `CONFIRMED`

## Incluye

- ...
- ...

## Excluye

- ...
- ...

## Dependencias con otros scopes

- `scope-id`
  - Tipo de dependencia:
  - Descripción:
  - Elementos conocidos:
  - Evidence status:

## Límites ambiguos

- NONE | descripción
```

Debe quedar suficientemente claro dónde termina la responsabilidad funcional del scope.

---

# 9. FUENTES Y COBERTURA DEL ANÁLISIS

## 9.1 Inventario de fuentes

Cada fichero del CFS registra sus propias fuentes.

Los IDs de fuente llevan el ámbito del fichero como primer segmento:

```text
SRC-<AMBITO>-<TIPO>-<NNN>
```

donde `<AMBITO>` es el ID del módulo sin el prefijo `MOD-` (por ejemplo `TAREAS`), o `GLOBAL` para los ficheros `_*.md`.

Ejemplos:

```text
SRC-TAREAS-CODE-001
SRC-TAREAS-UI-002
SRC-GLOBAL-DOC-001
```

Una fuente utilizada por varios módulos se registra en cada fichero que la utilice, con su propio ID. Esta duplicación está permitida deliberadamente: mantiene cada fichero autocontenido y refleja qué analizó cada extracción.

En una actualización conservadora, el campo «Versión / commit» de cada fuente refleja el commit del último análisis de **esa fuente**: las fuentes no re-analizadas conservan su commit anterior (frescura por fuente). El `source-commit` del front matter refleja la última pasada de actualización del fichero.

Las fuentes relevantes DEBEN registrarse utilizando IDs.

Formato:

```md
# 3. Fuentes y cobertura

## Fuentes analizadas

### SRC-TAREAS-CODE-001

- **Tipo:** CODE
- **Ubicación:** `path/to/source`
- **Descripción:** ...
- **Versión / commit:** ...
- **Analizada:** YES
- **Observaciones:** NONE

### SRC-TAREAS-DOC-001

- **Tipo:** DOCUMENT
- **Ubicación:** `.docs/...`
- **Descripción:** ...
- **Fecha o versión:** ...
- **Analizada:** YES
- **Observaciones:** ...
```

Tipos recomendados:

```text
CODE
UI
DOCUMENT
SPECIFICATION
PLAN
DATABASE
API
CONFIGURATION
TEST
OTHER
```

Los tipos se escriben completos: no se admiten abreviaturas (`DOCUMENT`, no `DOC`).

---

## 9.2 Fuentes no disponibles

Debe indicarse cualquier fuente que razonablemente sería necesaria pero no haya podido analizarse.

Formato:

```md
## Fuentes no disponibles o no analizadas

- **Fuente esperada:** ...
- **Motivo:** ...
- **Impacto:** ...
```

Si no existen:

```text
NONE
```

---

## 9.3 Cobertura

Debe describirse la cobertura global:

```md
## Cobertura

- **Backend:** COMPLETE | PARTIAL | NOT_APPLICABLE | UNKNOWN
- **Frontend:** COMPLETE | PARTIAL | NOT_APPLICABLE | UNKNOWN
- **Base de datos:** COMPLETE | PARTIAL | NOT_APPLICABLE | UNKNOWN
- **Documentación funcional:** COMPLETE | PARTIAL | NOT_APPLICABLE | UNKNOWN
- **Planes / especificaciones:** COMPLETE | PARTIAL | NOT_APPLICABLE | UNKNOWN
- **Integraciones relevantes:** COMPLETE | PARTIAL | NOT_APPLICABLE | UNKNOWN

### Limitaciones

- ...
```

`COMPLETE` significa que se ha revisado suficientemente el área dentro del scope, no que se conozca absolutamente todo.

---

# 10. VISIÓN FUNCIONAL GLOBAL

Debe proporcionar suficiente información para generar posteriormente una infografía general del scope.

Formato:

```md
# 4. Visión funcional global

## Propósito

...

## Usuarios principales

- `ROL-...`
- `ROL-...`

## Módulos

| ID | Nombre | Objetivo | Roles principales | Entidades principales | Estado |
|---|---|---|---|---|---|
| `MOD-...` | ... | ... | ... | ... | `IMPLEMENTED` |

## Relaciones principales

- `MOD-X` → `MOD-Y`: ...
- ...

## Flujos principales

- `FLOW-...`: ...
- ...
```

Esta sección es un resumen.

NO DEBE sustituir la definición detallada posterior.

---

# 11. ROLES Y MODELO DE ACCESO

Los roles funcionales se definen globalmente en `_roles.md` y sólo se referencian posteriormente desde el resto de ficheros.

Formato obligatorio:

```md
# 5. Roles y modelo de acceso

## ROL-ADMINISTRADOR

- **Nombre:** Administrador
- **Descripción:** ...
- **Responsabilidad funcional:** ...
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Acceso a módulos

- `MOD-X`
- `MOD-Y`

### Capacidades principales

- ...
- ...

### Restricciones

- ...
- ...

### Condiciones adicionales de acceso

- Propiedad del registro: ...
- Empresa / tenant: ...
- Equipo / departamento: ...
- Estado del elemento: ...
- Permisos adicionales: ...

### Fuentes

- `SRC-...` — localización concreta
```

## 11.1 Permisos que no dependen únicamente del rol

Si el comportamiento depende de condiciones adicionales, estas DEBEN documentarse.

Ejemplos:

- propietario del registro;
- organización;
- tenant;
- equipo;
- departamento;
- estado del elemento;
- relación con otra entidad;
- permiso individual;
- configuración;
- feature flag.

NO debe simplificarse como "el rol X puede editar" si en realidad sólo puede editar determinados registros.

---

## 11.2 Matriz de acceso

El CFS DEBE incluir una matriz resumen:

```md
## Matriz rol → módulo

| Rol | MOD-X | MOD-Y | MOD-Z |
|---|---|---|---|
| `ROL-A` | Acceso | Sin acceso | Limitado |
| `ROL-B` | Acceso | Acceso | Acceso |
```

Cuando `Limitado` no sea suficientemente descriptivo debe existir una referencia hacia las reglas correspondientes.

---

## 11.3 Capabilities / permisos configurables

Cuando el producto utilice permisos granulares configurables (capabilities) además de roles, cada capability funcionalmente relevante DEBERÍA definirse con ID propio en `_roles.md`:

```md
### CAP-TAREAS-CERRAR

- **Nombre:** ...
- **Descripción:** ...
- **Funcionalidades que habilita:** `FUN-...`
- **Asignación:** configurable por rol | fija
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** ...
```

Las funcionalidades condicionadas por una capability DEBEN referenciarla en sus precondiciones o restricciones en lugar de describir el permiso de forma narrativa.

Cuando la asignación de capabilities a roles sea configurable, la matriz rol → capability refleja la configuración por defecto y DEBE indicarse expresamente que es configurable.

---

# 12. NAVEGACIÓN E INTERFACES DE USUARIO

Esta sección representa la estructura visible desde la perspectiva del usuario.

Su finalidad es permitir posteriormente generar:

- manuales paso a paso;
- mapas de navegación;
- infografías de interfaz;
- documentación contextual.

No debe convertirse en un inventario técnico de componentes Angular.

Sólo deben documentarse superficies funcionalmente relevantes.

## 12.1 Tipos recomendados

```text
PAGE
LIST
DETAIL
FORM
DIALOG
TAB
PANEL
MENU
WIZARD
DASHBOARD
REPORT
COMPONENT
OTHER
```

---

## 12.2 Formato

```md
# 6. Navegación e interfaces de usuario

## UI-TAREAS-LISTADO

- **Nombre visible:** Tareas
- **Tipo:** `LIST`
- **Módulo:** `MOD-TAREAS`
- **Ruta funcional:** ...
- **Ruta técnica:** `/tasks` | UNKNOWN
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Cómo se accede

1. ...
2. ...

### Roles con acceso

- `ROL-...`

### Propósito

...

### Información mostrada

- ...
- ...

### Acciones disponibles

- `FUN-TAREAS-001`
- `FUN-TAREAS-004`

### Filtros / búsquedas relevantes

- ...
- ...

### Estados o condiciones que alteran la interfaz

- ...

### Superficies relacionadas

- `UI-...`

### Fuentes

- `SRC-...`
```

## 12.3 Terminología visible

Cuando pueda verificarse, los nombres visibles en botones, menús, pestañas y acciones DEBEN reproducir la terminología real de la interfaz.

NO deben inventarse etiquetas "más bonitas" para documentación.

Las recomendaciones terminológicas, si son necesarias, pertenecen al glosario.

---

# 13. ENTIDADES FUNCIONALES

Una entidad representa un objeto de negocio significativo para el usuario o para los flujos funcionales.

No es obligatorio documentar cada tabla de base de datos.

Una tabla puramente técnica NO debe convertirse automáticamente en una entidad funcional.

Cada entidad se define canónicamente en el fichero de su módulo propietario, conforme a la sección 7.3.

Formato:

```md
# 7. Entidades funcionales

## ENT-TAREA

- **Nombre:** Tarea
- **Descripción:** ...
- **Módulo propietario:** `MOD-TAREAS`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Significado funcional

...

### Campos funcionalmente relevantes

| Campo | Nombre visible | Significado | Obligatorio | Editable | Restricciones |
|---|---|---|---|---|---|
| ... | ... | ... | YES | ... | ... |

### Roles relacionados

- `ROL-...`: ...
- ...

### Creación

- **Quién puede crear:** ...
- **Condiciones:** ...
- **Funcionalidad:** `FUN-...`

### Modificación

- **Quién puede modificar:** ...
- **Condiciones:** ...

### Eliminación

- **Permitida:** YES | NO | CONDITIONAL | UNKNOWN
- **Condiciones:** ...
- **Funcionalidad:** ...

### Estados

- `STA-TAREA-PENDIENTE`
- `STA-TAREA-CERRADA`

### Relaciones

- `REL-...`

### Reglas relacionadas

- `RULE-...`

### Fuentes

- `SRC-...`
```

---

## 13.1 Campos funcionalmente relevantes

Sólo deben incluirse campos que:

- el usuario pueda ver;
- el usuario pueda editar;
- condicionen un flujo;
- condicionen permisos;
- condicionen estados;
- tengan significado de negocio;
- aparezcan en documentación;
- sean necesarios para comprender relaciones.

NO debe copiarse automáticamente el esquema completo de base de datos.

---

## 13.2 Estados

Cada estado funcionalmente relevante DEBE definirse.

Formato:

```md
### STA-TAREA-PENDIENTE

- **Nombre:** Pendiente
- **Entidad:** `ENT-TAREA`
- **Descripción:** ...
- **Estado inicial:** YES | NO
- **Estado final:** YES | NO
- **Evidence status:** `CONFIRMED`

#### Acciones permitidas

- `FUN-...`

#### Acciones bloqueadas

- `FUN-...`

#### Fuentes

- `SRC-...`
```

---

## 13.3 Transiciones de estado

Las transiciones DEBEN documentarse mediante una tabla:

```md
### Transiciones

| Desde | Hacia | Acción / trigger | Rol | Condiciones | Referencia |
|---|---|---|---|---|---|
| `STA-X` | `STA-Y` | ... | `ROL-X` | ... | `FUN-X-001` |
```

Si una transición es automática:

```text
Referencia: AUTO-X-001
```

---

## 13.4 Relaciones entre entidades

Las relaciones importantes DEBEN utilizar ID.

Formato:

```md
### REL-PROYECTO-TAREA

- **Origen:** `ENT-PROYECTO`
- **Destino:** `ENT-TAREA`
- **Tipo:** CONTAINS
- **Cardinalidad:** `1:N`
- **Dirección:** `ENT-PROYECTO` → `ENT-TAREA`
- **Descripción:** ...
- **Obligatoria:** YES | NO | CONDITIONAL | UNKNOWN
- **Evidence status:** `CONFIRMED`
- **Fuentes:** ...
```

Tipos recomendados:

```text
CONTAINS
BELONGS_TO
REFERENCES
DEPENDS_ON
ASSIGNED_TO
CREATED_BY
USES
GENERATES
DERIVED_FROM
LINKED_TO
OTHER
```

Puede utilizarse otro valor cuando los anteriores no representen correctamente la relación.

---

## 13.5 Baja lógica (activo / inactivo)

La baja lógica (desactivar / reactivar) NO es una máquina de estados y NO debe modelarse con `STA-`, salvo que interactúe con el ciclo de vida funcional de la entidad de forma que lo justifique.

Cuando una entidad soporte baja lógica, DEBE documentarse dentro de su definición con un bloque estándar:

```md
### Baja lógica

- **Soportada:** YES
- **Quién puede desactivar / reactivar:** ...
- **Efectos de la desactivación:** ...
- **Funcionalidades:** `FUN-...`
```

Los bloqueos que la desactivación imponga sobre otras operaciones se documentan como reglas de negocio (`RULE-`) referenciadas desde las funcionalidades afectadas.

---

# 14. MÓDULOS

Cada módulo debe tener una única sección canónica.

Formato:

```md
# 8. Módulos

## MOD-TAREAS — Tareas

- **Nombre:** Tareas
- **Objetivo:** ...
- **Responsabilidad funcional:** ...
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

### Resumen funcional

...

### Roles

- `ROL-...`

### Entidades principales

- `ENT-...`

### Interfaces principales

- `UI-...`

### Funcionalidades

- `FUN-...`
- `FUN-...`

### Flujos internos

- `FLOW-...`

### Reglas de negocio

- `RULE-...`

### Automatismos

- `AUTO-...`

### Módulos relacionados

- `MOD-...`
- `otro-scope::MOD-...`

### Fuentes principales

- `SRC-...`
```

## 14.1 Responsabilidad funcional

Debe poder responderse claramente:

> ¿Qué responsabilidad pertenece a este módulo y no a los demás?

Esto ayuda a evitar módulos solapados y duplicaciones.

---

# 15. FUNCIONALIDADES

Una funcionalidad representa una capacidad funcional concreta ofrecida por el sistema.

Debe tener granularidad suficiente para responder:

> ¿Qué puede hacer un usuario concreto y qué ocurre cuando lo hace?

No debe dividirse artificialmente cada clic en una funcionalidad independiente.

Tampoco deben agruparse acciones significativamente distintas bajo una única funcionalidad genérica.

---

## 15.1 Formato obligatorio

```md
### FUN-TAREAS-001 — Crear tarea

- **Nombre:** Crear tarea
- **Módulo:** `MOD-TAREAS`
- **Descripción:** ...
- **User-facing:** YES
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Roles autorizados

- `ROL-...`

#### Interfaces de acceso

- `UI-...`

#### Entidades implicadas

- `ENT-...`

#### Precondiciones

- ...

#### Trigger / inicio

...

#### Acción funcional

...

#### Datos requeridos

- ...

#### Datos opcionales

- ...

#### Resultado esperado

...

#### Cambios de estado

- `STA-X` → `STA-Y`
- `NOT_APPLICABLE`

#### Datos creados o modificados

- ...

#### Efectos secundarios

- ...
- `NONE`

#### Módulos afectados

- `MOD-...`
- `NONE`

#### Reglas de negocio

- `RULE-...`

#### Automatismos relacionados

- `AUTO-...`

#### Restricciones

- ...

#### Excepciones y errores funcionales

- ...

#### Resultado visible para el usuario

...

#### Funcionalidades relacionadas

- `FUN-...`

#### Fuentes

- `SRC-...` — localización concreta
```

---

## 15.2 `User-facing`

Valores:

```text
YES
NO
PARTIAL
```

### `YES`

La funcionalidad es directamente iniciada o percibida por un usuario.

### `NO`

Es funcionalmente relevante, pero únicamente interna o automática.

### `PARTIAL`

Combina una acción del usuario con comportamiento automático significativo.

---

## 15.3 Precondiciones

Las precondiciones deben ser explícitas.

Ejemplos:

- La entidad debe estar en determinado estado.
- Debe existir una relación previa.
- El usuario debe pertenecer a la misma organización.
- Debe existir determinada configuración.
- Debe estar activa determinada característica.
- El usuario debe ser propietario del registro.

NO utilizar:

```text
Precondiciones: las habituales
```

---

## 15.4 Errores funcionales

Sólo deben incluirse errores con significado para el usuario o para el flujo.

No es necesario documentar excepciones técnicas internas sin consecuencia funcional.

Ejemplos relevantes:

- No puede eliminarse porque existen registros dependientes.
- La operación no está disponible en ese estado.
- El usuario no tiene permiso.
- La información introducida no es válida.
- Una integración externa no ha podido completar la operación.

---

# 16. REGLAS DE NEGOCIO

Toda regla que condicione de forma relevante el comportamiento funcional DEBERÍA disponer de ID propio.

Formato:

```md
### RULE-TAREAS-001

- **Nombre:** ...
- **Módulo propietario:** `MOD-TAREAS`
- **Descripción:** ...
- **Condición:** ...
- **Consecuencia:** ...
- **Roles afectados:** ...
- **Entidades afectadas:** ...
- **Funcionalidades afectadas:** ...
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** ...
```

Ejemplos de reglas:

- Una tarea cerrada no puede modificarse.
- Sólo el propietario puede eliminar un borrador.
- Un pedido no puede facturarse dos veces.
- Un elemento sólo puede cambiar a determinado estado si cumple una condición previa.

Las reglas NO deben esconderse únicamente dentro de descripciones narrativas cuando sean reutilizadas por varias funcionalidades.

---

# 17. AUTOMATISMOS

Un automatismo representa un comportamiento que el sistema ejecuta sin una acción manual equivalente del usuario.

Formato:

```md
### AUTO-TAREAS-001

- **Nombre:** ...
- **Módulo propietario:** `MOD-TAREAS`
- **Descripción:** ...
- **Trigger:** ...
- **Condiciones:** ...
- **Acciones ejecutadas:** ...
- **Entidades afectadas:** ...
- **Cambios de estado:** ...
- **Módulos afectados:** ...
- **Resultado visible para el usuario:** ...
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`
- **Fuentes:** ...
```

Ejemplos:

- Cambio automático de estado.
- Generación automática de registros.
- Envío de notificaciones.
- Cálculo de valores.
- Sincronización.
- Propagación de cambios.
- Ejecución programada.
- Reacción ante eventos externos.

---

# 18. FLUJOS DE TRABAJO

Un flujo representa una secuencia funcional con un objetivo identificable.

Los flujos pueden ser:

- internos de un módulo;
- transversales entre varios módulos.

Formato:

```md
### FLOW-TAREAS-001 — Crear y asignar una tarea

- **Nombre:** ...
- **Objetivo:** ...
- **Módulo principal:** `MOD-TAREAS`
- **Módulos participantes:**
  - `MOD-TAREAS`
  - `MOD-PROYECTOS`
- **Roles participantes:**
  - `ROL-...`
- **Implementation status:** `IMPLEMENTED`
- **Evidence status:** `CONFIRMED`

#### Punto de inicio

...

#### Precondiciones

- ...

#### Secuencia principal

1. ...
2. ...
3. ...

#### Decisiones y bifurcaciones

1. Si ...
   - ...
2. Si ...
   - ...

#### Funcionalidades utilizadas

1. `FUN-...`
2. `FUN-...`

#### Entidades implicadas

- `ENT-...`

#### Estados iniciales

- ...

#### Estados finales

- ...

#### Resultado

...

#### Excepciones

- ...

#### Flujos relacionados

- `FLOW-...`

#### Fuentes

- `SRC-...`
```

---

## 18.1 Reglas para diagramabilidad

La descripción de un flujo DEBE contener información suficiente para que otro agente pueda generar un diagrama de flujo sin volver al código fuente.

Por tanto, debe expresar explícitamente:

- inicio;
- pasos;
- decisiones;
- condiciones;
- bifurcaciones;
- resultados;
- final;
- roles;
- entidades;
- módulos implicados.

---

# 19. RELACIONES ENTRE MÓDULOS

Las relaciones funcionalmente relevantes entre módulos deben identificarse explícitamente.

Las relaciones entre módulos distintos se definen canónicamente en `_relations.md` (sección 7.3).

Formato:

```md
## REL-TAREAS-PROYECTOS

- **Origen:** `MOD-TAREAS`
- **Destino:** `MOD-PROYECTOS`
- **Dirección:** `MOD-TAREAS` → `MOD-PROYECTOS`
- **Tipo:** USES
- **Descripción:** ...
- **Entidades compartidas:** ...
- **Funcionalidades relacionadas:** ...
- **Flujos relacionados:** ...
- **Datos intercambiados:** ...
- **Efectos cruzados:** ...
- **Evidence status:** `CONFIRMED`
- **Fuentes:** ...
```

Tipos recomendados:

```text
USES
DEPENDS_ON
PROVIDES_TO
CREATES_IN
TRIGGERS
SHARES_DATA_WITH
SYNCHRONIZES_WITH
REFERENCES
OTHER
```

---

# 20. FLUJOS TRANSVERSALES

Después de documentar los módulos individualmente debe existir una sección específica para procesos que atraviesen varios módulos.

Los flujos transversales se definen canónicamente en `_relations.md` (sección 7.3).

Formato:

```md
# 9. Flujos transversales

## FLOW-GLOBAL-001 — ...

- **Objetivo:** ...
- **Módulos:** ...
- **Roles:** ...
- **Entidades:** ...
- **Implementation status:** ...
- **Evidence status:** ...

### Secuencia

1. `MOD-X` / `FUN-X-001`: ...
2. `MOD-Y` / `FUN-Y-003`: ...
3. ...

### Resultado

...

### Fuentes

- ...
```

No debe duplicarse aquí la descripción detallada de las funcionalidades.

Se referencian mediante sus IDs.

---

# 21. GLOSARIO FUNCIONAL

El glosario debe ayudar a mantener terminología consistente en todos los artefactos posteriores.

El glosario completo del scope se define en `_glossary.md` (sección 7.3).

Formato:

```md
# 11. Glosario funcional

## Tarea

- **Término canónico:** Tarea
- **Significado:** ...
- **Término mostrado al usuario:** Tarea
- **Sinónimos encontrados:** ...
- **Términos técnicos relacionados:** ...
- **Uso recomendado en documentación:** ...
- **Notas:** ...
```

Debe prestarse especial atención a:

- diferencias entre nombres del código y nombres de UI;
- términos históricos;
- sinónimos;
- traducciones;
- abreviaturas;
- nombres que puedan resultar ambiguos.

Cuando exista un término visible actualmente en la interfaz, éste tiene prioridad para describir las acciones del usuario salvo que exista un motivo explícito para recomendar otro.

---

# 22. INCERTIDUMBRES, CONFLICTOS Y CARENCIAS

Todos los problemas de conocimiento detectados durante la extracción DEBEN centralizarse también en esta sección.

Esto no sustituye al `Evidence status` existente en cada elemento.

Las incertidumbres propias de un módulo se registran en el fichero de dicho módulo; las globales o transversales, en `_index.md`.

Los identificadores de incidencia llevan el ámbito como primer segmento, igual que las fuentes:

```text
INF-TAREAS-001
UNK-GLOBAL-001
CONFLICT-TAREAS-001
PARTIAL-TAREAS-001
```

## 22.1 Información inferida

Formato:

```md
# 12. Incertidumbres, conflictos y carencias

## Información inferida

### INF-TAREAS-001

- **Elemento:** `FUN-...`
- **Inferencia:** ...
- **Motivo:** ...
- **Fuentes:** ...
- **Impacto documental:** LOW | MEDIUM | HIGH
```

---

## 22.2 Información desconocida

```md
## Información desconocida

### UNK-TAREAS-001

- **Elemento:** `ENT-...`
- **Información no determinada:** ...
- **Fuentes revisadas:** ...
- **Qué sería necesario para resolverlo:** ...
- **Impacto documental:** LOW | MEDIUM | HIGH
```

---

## 22.3 Conflictos

```md
## Conflictos

### CONFLICT-TAREAS-001

- **Elemento:** `FUN-...`
- **Descripción:** ...
- **Fuente A:** `SRC-...`
- **Afirma:** ...
- **Fuente B:** `SRC-...`
- **Afirma:** ...
- **Resolución:** UNRESOLVED | ...
- **Impacto documental:** LOW | MEDIUM | HIGH
```

NO deben resolverse silenciosamente contradicciones entre:

- código y documentación;
- frontend y backend;
- planes distintos;
- especificaciones antiguas y actuales;
- diferentes implementaciones.

---

## 22.4 Implementaciones parciales

```md
## Implementaciones parciales

### PARTIAL-TAREAS-001

- **Elemento:** `FUN-...`
- **Parte implementada:** ...
- **Parte no implementada:** ...
- **Fuentes:** ...
```

---

## 22.5 Cierre de incidencias

Cuando una incidencia deje de describir el comportamiento actual (por ejemplo, porque el producto se ha corregido y se ha verificado), en la siguiente actualización del CFS la incidencia DEBE **eliminarse** de la sección.

- NO DEBE conservarse marcada como «resuelta» dentro de la sección de incertidumbres: el CFS describe el presente.
- Los IDs de incidencias retiradas NO DEBEN reutilizarse para incidencias nuevas.
- PUEDE dejarse una breve nota de retirada al final de la sección (mencionando los IDs sin backticks, para no crear referencias colgantes) que indique qué incidencias se retiraron, cuándo y por qué.

---

# 23. TRAZABILIDAD

El CFS debe permitir localizar el origen de las afirmaciones importantes.

Además de las referencias `Fuentes` incluidas dentro de cada elemento, debe existir una matriz resumen **en cada fichero**, con los elementos definidos en dicho fichero.

Formato:

```md
# 13. Trazabilidad

| Elemento | Tipo | Estado | Evidencia | Fuentes principales |
|---|---|---|---|---|
| `MOD-TAREAS` | Módulo | `IMPLEMENTED` | `CONFIRMED` | `SRC-TAREAS-CODE-001`, `SRC-TAREAS-UI-002` |
| `FUN-TAREAS-001` | Funcionalidad | `IMPLEMENTED` | `CONFIRMED` | `SRC-TAREAS-CODE-004` |
| `FLOW-TAREAS-001` | Flujo | `IMPLEMENTED` | `INFERRED` | `SRC-TAREAS-CODE-004`, `SRC-TAREAS-UI-003` |
```

## 23.1 Localización de evidencia

Cuando sea posible, una referencia a fuente debe incluir una localización concreta.

Ejemplos:

```text
SRC-TAREAS-CODE-003 — TaskController.cs → CloseTask()
SRC-TAREAS-CODE-007 — task.service.ts → closeTask()
SRC-TAREAS-UI-002 — task-detail.component.html → botón "Cerrar"
SRC-TAREAS-DOC-004 — plan-fase-4.md → sección "Cierre de tareas"
```

No es necesario registrar números de línea que puedan quedar obsoletos rápidamente salvo que resulte útil.

Se prefieren:

- clase;
- método;
- componente;
- endpoint;
- sección;
- heading;
- ruta;
- nombre funcional estable.

---

# 24. REGLAS PARA EVITAR DUPLICACIÓN

## 24.1 Roles

Un rol se define una sola vez en `Roles y modelo de acceso`.

Las funcionalidades sólo deben referenciar:

```text
ROL-ADMINISTRADOR
```

---

## 24.2 Entidades

Una entidad se define una sola vez en `Entidades funcionales`.

Los módulos y funcionalidades deben referenciar su ID.

---

## 24.3 Funcionalidades

Cada funcionalidad pertenece canónicamente a un módulo.

Otros módulos pueden referenciarla, pero no redefinirla.

---

## 24.4 Reglas

Cuando una regla afecta a varias funcionalidades debe definirse una sola vez y referenciarse desde todas ellas.

---

## 24.5 Flujos

Un flujo no debe copiar nuevamente toda la descripción de cada funcionalidad.

Debe secuenciar IDs y añadir únicamente la información necesaria para comprender la coordinación entre ellas.

---

## 24.6 Otros scopes

La funcionalidad de otro scope NO debe copiarse íntegramente.

Debe utilizarse:

```text
scope-id::ELEMENT-ID
```

cuando exista.

Si todavía no existe un CFS para ese scope, debe describirse únicamente la dependencia observada y marcar cualquier detalle no verificable como `UNKNOWN`.

---

# 25. INFORMACIÓN QUE NO DEBE INCLUIRSE

El CFS NO DEBE contener innecesariamente:

- Contraseñas.
- Tokens.
- API keys.
- Connection strings con credenciales.
- Secretos.
- Credenciales reales de prueba o producción.
- Datos personales reales encontrados en bases de datos o fixtures.
- Información sensible que no sea necesaria para describir el comportamiento funcional.
- Dumps completos de base de datos.
- Código fuente copiado extensamente.
- Listados exhaustivos de clases sin significado funcional.
- Detalles internos irrelevantes para el comportamiento.
- Información puramente histórica que ya no tenga impacto funcional, salvo que explique un conflicto.
- Funcionalidades hipotéticas inventadas.
- Recomendaciones de producto mezcladas con comportamiento existente.

Si una fuente contiene credenciales o información sensible, debe referenciarse la fuente sin reproducir esos valores.

---

# 26. REGLAS DE REDACCIÓN

El contenido funcional debe ser:

- preciso;
- explícito;
- neutral;
- estructurado;
- fácilmente procesable por otro agente;
- comprensible por un humano;
- consistente en terminología;
- suficientemente detallado para producir documentación derivada.

## 26.1 Evitar ambigüedad

Evitar expresiones como:

```text
etc.
y demás
entre otras cosas
parece que
normalmente
en principio
probablemente
más o menos
```

Si existe incertidumbre debe representarse formalmente mediante:

```text
INFERRED
UNKNOWN
CONFLICT
```

---

## 26.2 Diferenciar hechos de explicaciones

La descripción puede explicar el comportamiento, pero no debe añadir interpretaciones no respaldadas.

---

## 26.3 Terminología consistente

Una vez definido un término canónico en el glosario, debe utilizarse de manera consistente.

---

## 26.4 Perspectiva de usuario

Cuando se describa una funcionalidad user-facing se debe priorizar:

```text
El usuario puede...
```

sobre:

```text
El controlador ejecuta...
```

La segunda formulación sólo resulta relevante como evidencia técnica.

---

# 27. VALIDACIÓN FINAL

Antes de considerar terminado un CFS, el agente extractor DEBE realizar estas comprobaciones.

## 27.0 Niveles de validación

La validación se realiza a dos niveles:

1. **Por fichero**: front matter válido, secciones obligatorias presentes, integridad local del contenido.
2. **De scope**: unicidad global de IDs, resolución de todas las referencias entre ficheros y coherencia estructural (cada módulo del inventario de `_index.md` tiene fichero, cada fichero de módulo aparece en el inventario y en la matriz rol → módulo, y los nombres de fichero cumplen la sección 7.1).

Las comprobaciones estructurales DEBEN verificarse mecánicamente mediante la herramienta de lint del CFS (`tools/lint-cfs.mjs`) cuando esté disponible. La autodeclaración del agente no sustituye al lint.

## 27.1 Integridad estructural

- [ ] Existe front matter.
- [ ] `schema-version` coincide con este schema.
- [ ] Existe `scope-id`.
- [ ] Están presentes todas las secciones obligatorias.
- [ ] No existen IDs duplicados.
- [ ] No existen referencias internas a IDs inexistentes.
- [ ] Las referencias externas utilizan `scope::ID`.
- [ ] Los IDs existentes no han sido renumerados innecesariamente.
- [ ] Existen todos los ficheros obligatorios (`_index.md`, `_roles.md`, `_glossary.md`, `_relations.md`).
- [ ] El inventario de `_index.md` coincide con los ficheros existentes.
- [ ] Cada módulo tiene un fichero `mod-<modulo>.md` con nombre conforme a la sección 7.1 y aparece en la matriz rol → módulo.
- [ ] Cada elemento está definido en el fichero que le corresponde según la sección 7.3.
- [ ] Los módulos sin extraer están definidos como stubs en `_index.md` (sección 7.7) y no tienen fichero.
- [ ] Toda referencia externa `scope::ID` está declarada en la sección de dependencias de `_relations.md`.

---

## 27.2 Evidencia

- [ ] Todo elemento `CONFIRMED` tiene evidencia suficiente.
- [ ] Las inferencias están marcadas como `INFERRED`.
- [ ] La información desconocida está marcada como `UNKNOWN`.
- [ ] Los conflictos están marcados como `CONFLICT`.
- [ ] Ninguna funcionalidad aparece como `IMPLEMENTED` basándose exclusivamente en un plan futuro.
- [ ] Las contradicciones importantes aparecen también en la sección de incertidumbres.

---

## 27.3 Cobertura funcional

Debe poder responderse, utilizando únicamente el CFS:

- [ ] ¿Qué propósito tiene este scope?
- [ ] ¿Qué queda fuera del scope?
- [ ] ¿Qué módulos existen?
- [ ] ¿Para qué sirve cada módulo?
- [ ] ¿Qué roles existen?
- [ ] ¿A qué puede acceder cada rol?
- [ ] ¿Qué restricciones adicionales existen?
- [ ] ¿Qué entidades funcionales maneja el sistema?
- [ ] ¿Qué estados tienen?
- [ ] ¿Cómo cambian de estado?
- [ ] ¿Qué funcionalidades puede ejecutar cada rol?
- [ ] ¿Desde qué interfaz se ejecutan?
- [ ] ¿Qué precondiciones tiene cada acción?
- [ ] ¿Qué resultado produce?
- [ ] ¿Qué reglas de negocio la condicionan?
- [ ] ¿Qué automatismos existen?
- [ ] ¿Qué módulos se relacionan?
- [ ] ¿Cómo se relacionan?
- [ ] ¿Qué flujos principales existen?
- [ ] ¿Qué procesos atraviesan varios módulos?

---

## 27.4 Aptitud para documentación

A partir exclusivamente del CFS, otro agente debe poder generar:

- [ ] Una introducción funcional al producto.
- [ ] Un listado de módulos y objetivos.
- [ ] Una infografía global de módulos.
- [ ] Un diagrama de relaciones entre módulos.
- [ ] Una guía de cada módulo.
- [ ] Una matriz rol → funcionalidad.
- [ ] Un mapa de navegación.
- [ ] Un diagrama de entidades funcionales.
- [ ] Un diagrama de estados cuando existan estados.
- [ ] Un diagrama para cada flujo relevante.
- [ ] Instrucciones funcionales para realizar las principales operaciones.
- [ ] Un glosario para documentación de usuario.

Si alguna de estas tareas no puede realizarse debido a falta de información que podría obtenerse de las fuentes disponibles, la extracción debe ampliarse antes de finalizar.

---

## 27.5 Seguridad

- [ ] No se han copiado contraseñas.
- [ ] No se han copiado tokens.
- [ ] No se han copiado API keys.
- [ ] No se han copiado datos personales reales innecesarios.
- [ ] No se han incluido secretos encontrados accidentalmente en el repositorio.

---

# 28. ESQUELETOS DE LOS FICHEROS GENERADOS

Cada fichero del CFS deberá aproximarse a la estructura correspondiente de esta sección.

Todos los ficheros comienzan con el front matter definido en la sección 6 (omitido aquí por brevedad).

## 28.1 `_index.md`

```md
# CFS — <Nombre del scope>

# 1. Metainformación

## Resumen de generación
...

## Inventario de ficheros

| Fichero | Part | Módulo | generated-at | source-commit | generation-status |
|---|---|---|---|---|---|
| `_index.md` | INDEX | NOT_APPLICABLE | ... | ... | ... |
| `mod-<modulo>.md` | MODULE | `MOD-...` | ... | ... | ... |

# 2. Scope y límites

## Scope
...

## Incluye
...

## Excluye
...

## Dependencias con otros scopes
...

## Límites ambiguos
...

# 3. Cobertura global

## Resumen
...

## Fuentes no disponibles o no analizadas
...

# 4. Visión funcional global

## Propósito
...

## Usuarios principales
...

## Módulos
...

## Relaciones principales
...

## Flujos principales
...

# 5. Módulos pendientes de extracción

NONE | ### MOD-... (stubs, sección 7.7)

# 6. Entidades sin módulo propietario claro

NONE | ## ENT-...

# 7. Incertidumbres globales

## Información inferida
...

## Información desconocida
...

## Conflictos
...

# 8. Validación de scope

## Resultado
...

## Limitaciones finales
...
```

## 28.2 `_roles.md`

```md
# CFS — <Nombre del scope> — Roles y modelo de acceso

# 1. Metainformación
...

# 2. Roles

## ROL-...
...

# 3. Capabilities / permisos configurables

NONE | ## CAP-...

# 4. Matriz rol → módulo
...

# 5. Incertidumbres
...

# 6. Validación del fichero
...
```

## 28.3 `_glossary.md`

```md
# CFS — <Nombre del scope> — Glosario funcional

# 1. Metainformación
...

# 2. Glosario

## <Término>
...

# 3. Validación del fichero
...
```

## 28.4 `_relations.md`

```md
# CFS — <Nombre del scope> — Relaciones y flujos transversales

# 1. Metainformación
...

# 2. Relaciones entre módulos

## REL-...
...

# 3. Relaciones entre entidades de módulos distintos

NONE | ## REL-...

# 4. Flujos transversales

## FLOW-GLOBAL-...
...

# 5. Dependencias entre scopes
...

# 6. Resumen de relaciones intra-módulo

| ID | Fichero | Resumen |
|---|---|---|
| ... | ... | ... |

# 7. Incertidumbres
...

# 8. Validación del fichero
...
```

## 28.5 `mod-<modulo>.md`

```md
# CFS — <Nombre del scope> — Módulo <Nombre>

# 1. Metainformación
...

# 2. Módulo

## MOD-...
...

# 3. Fuentes y cobertura del módulo

## Fuentes analizadas

### SRC-<MODULO>-...
...

## Fuentes no disponibles o no analizadas
...

## Cobertura
...

# 4. Navegación e interfaces de usuario

## UI-...
...

# 5. Entidades funcionales

## ENT-...
...

### Estados

#### STA-...
...

### Transiciones
...

### Relaciones (intra-módulo)

#### REL-...
...

# 6. Funcionalidades

## FUN-...
...

# 7. Reglas de negocio

## RULE-...
...

# 8. Automatismos

## AUTO-...
...

# 9. Flujos internos

## FLOW-...
...

# 10. Incertidumbres del módulo

## Información inferida
...

## Información desconocida
...

## Conflictos
...

## Implementaciones parciales
...

# 11. Trazabilidad del módulo

| Elemento | Tipo | Estado | Evidencia | Fuentes principales |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

# 12. Validación del fichero

## Resultado
...

## Limitaciones
...
```

---

# 29. EVOLUCIÓN DEL SCHEMA

Este schema está versionado.

La versión debe seguir un esquema:

```text
MAJOR.MINOR
```

Ejemplos:

```text
1.0
1.1
2.0
```

## Cambio `MINOR`

Puede incrementarse cuando se introduzcan cambios compatibles, por ejemplo:

- nuevos campos opcionales;
- aclaraciones;
- nuevos tipos recomendados;
- nuevas reglas que no invaliden CFS anteriores.

Ejemplo:

```text
1.0 → 1.1
```

---

## Cambio `MAJOR`

Debe incrementarse cuando un cambio pueda hacer que un CFS válido anterior deje de cumplir el schema.

Ejemplos:

- nueva estructura obligatoria;
- cambio del formato de IDs;
- eliminación o renombrado de campos obligatorios;
- cambio de semántica de valores normalizados.

Ejemplo:

```text
1.1 → 2.0
```

---

## Historial de versiones

- **`2.1`** — Aclaraciones derivadas de la primera actualización conservadora (FONT-472): cierre de incidencias por eliminación con nota de retirada (sección 22.5), frescura por fuente en actualizaciones (sección 9.1) y semántica de `generated-at` (sección 6.6).
- **`2.0`** — Estructura multi-fichero por módulo (sección 7), front matter por fichero con `part` y `module-id` (sección 6), fuentes e incidencias con ámbito en el ID (secciones 9 y 22), prefijo `CAP-` para capabilities (sección 11.3), validación a dos niveles con lint mecánico (sección 27). Consolidada tras el piloto del scope `erp` con: stubs para módulos pendientes de extracción (sección 7.7), declaración obligatoria de referencias externas provisionales (sección 5) y baja lógica (sección 13.5).
- **`1.0`** — Versión inicial (documento único por scope).

---

## Prioridad normativa

En caso de discrepancia entre:

- `functional-schema.md`;
- `functional-schema-example/`;

prevalece siempre:

```text
functional-schema.md
```

El directorio:

```text
functional-schema-example/
```

contiene únicamente una implementación ilustrativa del schema (validada con el lint) y NO constituye una fuente normativa independiente.

---

# FIN DEL SCHEMA