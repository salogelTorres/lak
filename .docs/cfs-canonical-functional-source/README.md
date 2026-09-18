# CFS — Canonical Functional Source

**Nombre localizado:** FFC — Fuente Funcional Canónica  
**Idioma del contenido:** Español (`es`)

## ÍNDICE

- [[#OBJETIVO]]
- [[#MOTIVACIÓN Y EVIDENCIA]]
- [[#PRINCIPIOS]]
- [[#ARCHIVOS]]
- [[#FLUJO DE GENERACIÓN]]
- [[#SCOPES]]
- [[#AUTORIDAD DE LA INFORMACIÓN]]
- [[#CONVENCIÓN GENERAL]]

---

## OBJETIVO

CFS (**Canonical Functional Source**) es una representación funcional, estructurada e intermedia del comportamiento de una aplicación o de uno de sus ámbitos funcionales.

Su objetivo es actuar como **fuente canónica intermedia** para la generación posterior de artefactos orientados al usuario, evitando que cada agente encargado de generar dichos artefactos tenga que analizar nuevamente el código fuente, planes de desarrollo, especificaciones y demás documentación del proyecto.

El CFS no constituye por sí mismo documentación final para el usuario.

A partir de él podrán generarse, entre otros:

- Documentación de usuario.
- Manuales funcionales.
- Infografías generales de la aplicación.
- Infografías específicas de módulos.
- Diagramas de relaciones entre módulos.
- Diagramas de flujos de trabajo.
- Diagramas de estados.
- Matrices de funcionalidades y permisos por rol.
- Material de onboarding.
- Ayuda contextual.
- Otros artefactos funcionales derivados.

El CFS debe contener suficiente información funcional para que los agentes encargados de generar estos artefactos puedan trabajar **sin necesidad de volver a consultar el código fuente ni la documentación de desarrollo**, salvo que se esté revisando o actualizando el propio CFS.

---

## MOTIVACIÓN Y EVIDENCIA

### Por qué existe este sistema

La documentación orientada al usuario (manuales, infografías, diagramas, ayuda contextual) se genera mediante agentes de IA. Sin una fuente intermedia, cada artefacto obliga a un agente a reinterpretar desde cero el código, los planes y las especificaciones. Ese enfoque directo presenta cuatro problemas estructurales:

1. **Coste repetido.** Cada artefacto paga un análisis completo del código, y vuelve a pagarlo en cada regeneración cuando el producto evoluciona.
2. **Incoherencia entre artefactos.** Dos agentes que leen el mismo código en sesiones distintas producen terminología, granularidad de módulos e inventarios de funcionalidades diferentes. En un conjunto de documentación de usuario (manual + infografía + ayuda describiendo la misma pantalla) esa divergencia es muy visible.
3. **Riesgo de invención.** Sin un modelo de evidencia explícito, el generador tiende a rellenar huecos con comportamientos plausibles («lo que suele hacer un ERP») que no existen en el producto.
4. **Verificación multiplicada.** Sin fuente canónica, un humano debe verificar los hechos de cada artefacto contra el código, en cada regeneración. Con CFS, los hechos se verifican una vez (en el CFS) y los artefactos son mayormente presentación.

### Ventajas del enfoque

- **Extraer una vez, generar N.** El coste del análisis profundo se paga por módulo, no por artefacto.
- **Coherencia garantizada.** Todos los artefactos comparten glosario, roles, estados e inventario de funcionalidades canónicos.
- **Modelo de evidencia.** La distinción `CONFIRMED` / `INFERRED` / `UNKNOWN` / `CONFLICT` impide afirmar lo no verificado y propaga las advertencias hasta los artefactos finales en lugar de ocultarlas.
- **Trazabilidad.** Cada afirmación funcional es rastreable hasta su fuente (clase, componente, pantalla, especificación).
- **Actualización barata y frescura visible.** La estructura multi-fichero permite regenerar solo los módulos afectados por cada fase, y el `source-commit` por fichero muestra qué partes del CFS están al día.
- **Validación mecánica.** El lint (`tools/lint-cfs.mjs`) verifica estructura, unicidad de IDs y referencias entre ficheros, sin depender de la autodeclaración del agente extractor.
- **Efecto secundario valioso:** la extracción rigurosa cruza frontend y backend, lo que aflora discrepancias reales del producto que el desarrollo no había detectado.

### Evidencia empírica: piloto del módulo Tareas (2026-09)

Antes de adoptar la metodología para todo el scope `erp` se ejecutó un piloto completo sobre el módulo de Tareas: extracción del CFS del módulo y generación de artefactos por dos vías — desde el CFS (con prohibición de leer código) y directamente desde el código (grupo de control) — para comparar coste y calidad.

| Métrica | Manual desde código (control) | Manual desde CFS | Diagrama de estados desde CFS |
|---|---|---|---|
| Operaciones de análisis del agente | 39 | 9 | 9 |
| Duración de generación | ~5,5 min | ~2,7 min | ~1,5 min |
| Huecos declarados | — | 5 marcas `[PENDIENTE]` | 0 |

Resultados cualitativos:

- **Convergencia factual.** Los dos manuales, derivados de forma independiente, coincidieron en prácticamente todos los hechos — indicador de fidelidad de la extracción.
- **Mayor seguridad para el usuario.** El manual desde CFS propagó como advertencias los conflictos conocidos (p. ej. campos de un formulario que el backend descartaba); el manual desde código, aun conociendo la discrepancia, los presentó como campos normales. Los huecos del CFS se declararon honestamente con `[PENDIENTE]` en lugar de rellenarse; no se detectó ninguna invención.
- **Integridad verificada mecánicamente.** El lint validó los 5 ficheros del piloto: 115 IDs definidos, 0 errores.
- **Detección de defectos reales.** La extracción afloró 3 defectos en la pantalla de Plantillas de tareas (contrato `daysOfWeek` incompatible entre frontend y backend, campos Categoría/Contacto descartados silenciosamente, reseteo de la prioridad al editar), identificados de forma independiente por los dos análisis. Fueron confirmados y corregidos posteriormente (FONT-472, 2026-09-11).
- **Coste de extracción acotado.** ~22 minutos de agente y ~45 ficheros analizados para un módulo mediano; coste que se amortiza frente a los múltiples artefactos previstos por módulo y a las actualizaciones incrementales por fase.

Conclusión del piloto: los artefactos generados desde el CFS resultaron de calidad igual o superior a los generados en directo, con ~4× menos operaciones de análisis y ~2× menos tiempo, coherencia terminológica garantizada y mejor tratamiento de la incertidumbre.

---

## PRINCIPIOS

### Fuente funcional intermedia

El CFS ocupa una posición intermedia dentro del proceso documental:

```text
Código + planes + especificaciones + documentación vigente
                          │
                          ▼
                         CFS
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Manuales   Infografías   Diagramas
                          │
                          ▼
                  Otros artefactos
```

Su finalidad es separar:

1. La **extracción y normalización del conocimiento funcional** del sistema.
2. La **generación de los distintos artefactos finales**.

De esta forma, todos los artefactos derivados utilizan una misma representación funcional del producto.

### Canonicalidad

El CFS es **canónico dentro del proceso de generación documental**.

Los agentes que generen documentación, diagramas, infografías u otros artefactos derivados deberán utilizar el CFS correspondiente como su fuente funcional de referencia y no reinterpretar independientemente el código fuente.

Esto permite mantener coherencia entre diferentes artefactos generados por distintos agentes.

### Trazabilidad

Siempre que sea razonablemente posible, la información funcional contenida en el CFS deberá poder relacionarse con las fuentes de las que ha sido extraída, como:

- Código fuente.
- Interfaces de usuario.
- Planes de desarrollo.
- Especificaciones.
- Documentación funcional.
- Otros documentos relevantes del proyecto.

### No invención

El CFS debe representar el comportamiento que pueda verificarse a partir de las fuentes disponibles.

No debe completar huecos suponiendo cómo debería funcionar el sistema.

Cuando una información no pueda confirmarse suficientemente, deberá quedar identificada siguiendo las reglas definidas en `functional-schema.md`.

---

## ARCHIVOS

Esta es la estructura de archivos:

```text
.docs/
├── ...
└── cfs-canonical-functional-source/
    ├── README.md
    ├── extraction-prompt.md
    ├── functional-schema.md
    ├── functional-schema-example/
    │
    ├── tools/
    │   └── lint-cfs.mjs
    │
    └── scopes/
        └── erp/
            ├── README.md
            └── functional-source/
                ├── _index.md
                ├── _roles.md
                ├── _glossary.md
                ├── _relations.md
                └── mod-<modulo>.md   (uno por módulo)
```

Los siguientes archivos **DEFINEN** cómo debe generarse un CFS:

- **`extraction-prompt.md`**  
  Es el prompt que define el objetivo del proceso de extracción, las fuentes que deben analizarse, las reglas que debe seguir el agente y qué tipo de información funcional debe obtener.

- **`functional-schema.md`**  
  Es el contrato que define la estructura y formato que deberá cumplir cualquier archivo CFS generado.

  Define, entre otros aspectos, cómo representar:

  - Módulos.
  - Funcionalidades.
  - Entidades.
  - Roles.
  - Estados.
  - Flujos.
  - Relaciones.
  - Reglas de negocio.
  - Evidencias.
  - Incertidumbres.
  - Referencias cruzadas.
  - Dependencias entre scopes.

- **`functional-schema-example/`**  
  Es un directorio con un ejemplo ficticio completo (`README.md` + un `functional-source/` multi-fichero) que cumple al 100 % el schema, se valida con el lint y está orientado a ayudar al agente extractor a interpretar correctamente su estructura.

  El ejemplo deberá utilizar módulos, funcionalidades, entidades y roles ficticios, inexistentes en el producto real, para evitar introducir accidentalmente información falsa en el sistema.

El siguiente directorio es **GENERADO** a partir de los anteriores:

- **`scopes/<scope>/functional-source/`**  
  Es el conjunto de ficheros que constituye el CFS generado para un scope concreto: cuatro ficheros globales (`_index.md`, `_roles.md`, `_glossary.md`, `_relations.md`) y un fichero por módulo (`mod-<modulo>.md`), conforme a la sección 7 de `functional-schema.md`.

  Constituye la fuente canónica para la posterior generación de documentación de usuario, infografías, diagramas y demás artefactos derivados correspondientes a ese ámbito funcional.

  Por ejemplo:

  ```text
  scopes/erp/functional-source/mod-tareas.md
  ```

Adicionalmente, `tools/lint-cfs.mjs` valida mecánicamente la estructura de un CFS generado (front matter, unicidad de IDs, referencias entre ficheros, nomenclatura). Forma parte del contrato de validación (sección 27 del schema).

Cada scope puede incluir adicionalmente un `README.md` que delimite expresamente qué parte del sistema pertenece a dicho ámbito y qué elementos quedan fuera de él.

---

## FLUJO DE GENERACIÓN

La relación principal entre los archivos es:

```text
                         DEFINEN
                            │
             ┌──────────────┼──────────────┐
             │              │              │
 extraction-prompt.md  functional-schema.md  functional-schema-example/
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                          GENERA
                            │
                            ▼
              scopes/<scope>/functional-source/
              (_index, _roles, _glossary,
               _relations, mod-<modulo>...)
                            │
                            ▼
                    ARTEFACTOS DERIVADOS
             ┌──────────────┼──────────────┐
             │              │              │
          Manuales      Infografías     Diagramas
```

Por tanto:

- `extraction-prompt.md` define **qué debe investigar y extraer el agente**.
- `functional-schema.md` define **cómo debe representar esa información**.
- `functional-schema-example/` muestra **cómo debe ser un resultado válido**.
- Los ficheros de `functional-source/` contienen **el conocimiento funcional normalizado resultante**.

Los agentes que generen artefactos finales deberán consumir preferentemente los ficheros del `functional-source/` del scope correspondiente y no las fuentes originales utilizadas para construirlo. Para un artefacto de módulo, la unidad de consumo prevista es `_index.md` + `_roles.md` + `_glossary.md` + `mod-<modulo>.md` (más `_relations.md` si el artefacto es transversal).

---

## SCOPES

Un **scope** representa un ámbito funcional del sistema que puede analizarse, mantenerse y documentarse de forma independiente.

Los scopes permiten utilizar una misma metodología CFS en soluciones compuestas por varios proyectos, productos, capas o subsistemas relacionados entre sí.

Cada scope vive bajo:

```text
scopes/<scope>/
```

y dispone como mínimo de:

```text
README.md
functional-source/
```

El `README.md` de cada scope debe delimitar claramente:

- Qué parte del sistema incluye.
- Qué parte del sistema excluye.
- Qué proyectos o componentes técnicos deben analizarse para construirlo.
- Qué dependencias funcionales mantiene con otros scopes, si existen.
- Qué límites funcionales deben respetarse para evitar duplicar información que pertenezca a otros scopes.

### Scopes actuales

Actualmente el sistema para esta aplicación incluye el siguiente scope:

- `erp`

```text
scopes/
└── erp/
    ├── README.md
    └── functional-source/
        ├── _index.md
        ├── _roles.md
        ├── _glossary.md
        ├── _relations.md
        └── mod-<modulo>.md
```

### Scopes no incluidos actualmente

Actualmente no existen CFS independientes para:

- `legna-core`
- `nexus-core`
- `fontenebro-nexus`

Estos ámbitos podrán incorporarse en el futuro si surge la necesidad de generar documentación funcional o cualquier otro artefacto derivado sobre ellos.

La estructura prevista permitiría hacerlo sin modificar la metodología:

```text
scopes/
├── erp/
├── fontenebro-nexus/
├── nexus-core/
└── legna-core/
```

La existencia de una dependencia técnica entre dos scopes no implica que su información funcional deba duplicarse.

Cuando una funcionalidad perteneciente a un scope sea utilizada desde otro, deberá documentarse en cada uno únicamente al nivel que corresponda a su responsabilidad funcional y, cuando resulte necesario, establecerse una referencia entre ambos.

Por ejemplo:

- Si el ERP utiliza la gestión de ficheros proporcionada por `legna-core`, el CFS del ERP deberá documentar qué puede hacer funcionalmente el usuario con esos ficheros dentro del ERP.
- No deberá duplicar la descripción interna completa del sistema de gestión de ficheros de `legna-core`.
- Si existe un CFS independiente para `legna-core`, podrá establecerse una referencia funcional entre ambos scopes.

El objetivo es evitar que existan varias fuentes canónicas describiendo de forma completa una misma responsabilidad funcional.

---

## AUTORIDAD DE LA INFORMACIÓN

Debe distinguirse entre la autoridad sobre **el comportamiento del producto** y la autoridad dentro del **proceso documental**.

### Sobre el comportamiento real del producto

El código fuente actual y las especificaciones vigentes continúan siendo la autoridad última sobre el comportamiento real del producto.

El CFS es una representación derivada de dichas fuentes y, por tanto, puede quedar desactualizado si el producto cambia y no se regenera o revisa posteriormente.

```text
Código + especificaciones vigentes
              │
              │ autoridad sobre el producto
              ▼
             CFS
              │
              │ autoridad documental
              ▼
     Artefactos derivados
```

Los planes de desarrollo, especificaciones históricas y demás documentación auxiliar pueden aportar contexto funcional, pero no deben prevalecer sobre el comportamiento actualmente implementado cuando exista una discrepancia verificable.

Cuando exista una contradicción entre fuentes, esta deberá quedar reflejada en el CFS conforme a las reglas establecidas en `functional-schema.md`.

### Sobre los artefactos documentales

Dentro del proceso de generación de documentación, el CFS correspondiente al scope constituye la **fuente funcional canónica**.

Los agentes encargados de generar:

- Documentación.
- Manuales.
- Diagramas.
- Infografías.
- Ayudas.
- Material de onboarding.
- Otros artefactos funcionales.

deberán utilizar el CFS como fuente de verdad funcional.

Podrán realizar verificaciones puntuales contra el código cuando lo consideren necesario, pero NO deberán modificar, ampliar ni contradecir el contenido del CFS dentro del artefacto generado.

Si una verificación puntual revela una discrepancia con el CFS, el artefacto no debe «corregirse» unilateralmente: la discrepancia debe reportarse como incidencia del CFS y resolverse primero en el CFS. De este modo, cada generación de artefactos actúa además como detector de obsolescencia del CFS.

Si durante la generación de un artefacto se detecta que falta información, existe una ambigüedad o se sospecha que el CFS está desactualizado, deberá tratarse como un problema del propio CFS.

El flujo correcto será:

```text
Se detecta inconsistencia o información insuficiente
                      │
                      ▼
             Revisar fuentes originales
                      │
                      ▼
              Corregir / regenerar CFS
                      │
                      ▼
          Regenerar artefactos afectados
```

No deberá solucionarse una carencia del CFS introduciendo directamente información nueva únicamente en un manual, infografía o diagrama derivado.

Esto garantiza que el conocimiento funcional normalizado permanezca centralizado y que todos los artefactos posteriores puedan mantenerse coherentes entre sí.

---

## CONVENCIÓN GENERAL

La estructura y nomenclatura técnica del sistema CFS se mantiene en inglés para poder reutilizarse de forma consistente entre proyectos desarrollados en diferentes idiomas.

Por ejemplo:

```text
cfs-canonical-functional-source/
functional-schema.md
extraction-prompt.md
scopes/
functional-source/
mod-tareas.md
```

El contenido funcional generado se redactará en el idioma correspondiente al producto o proyecto.

En este proyecto:

```text
Idioma: Español
Código de idioma: es
```

De esta forma, la metodología CFS y su estructura de archivos pueden mantenerse estables entre diferentes proyectos, independientemente del idioma utilizado para su documentación funcional.

## EJEMPLO DE GENERACIÓN DE UN CFS

Para generar o actualizar el CFS de un scope concreto, el agente debe tener acceso al repositorio completo y recibir una instrucción que le indique qué scope debe procesar.

No es necesario repetir en el prompt de ejecución las reglas de extracción ni la estructura del resultado, ya que éstas se encuentran definidas de forma canónica en:

```text
extraction-prompt.md
functional-schema.md
functional-schema-example/
scopes/<scope>/README.md
```

El prompt de ejecución debe limitarse principalmente a:

1. Identificar el scope que se quiere procesar.
2. Indicar al agente que lea y respete la estructura CFS.
3. Indicar el directorio `functional-source/` que debe generar o actualizar (y, en actualizaciones parciales, qué módulos).
4. Darle acceso al resto del repositorio para localizar y analizar las fuentes necesarias.

### Ejemplo: generar el CFS del ERP

Un prompt recomendado sería:

```text
Genera o actualiza el Canonical Functional Source (CFS) correspondiente al scope `erp` de este repositorio.

Antes de comenzar, lee y sigue las instrucciones y reglas definidas en:

- `.docs/cfs-canonical-functional-source/README.md`
- `.docs/cfs-canonical-functional-source/extraction-prompt.md`
- `.docs/cfs-canonical-functional-source/functional-schema.md`
- `.docs/cfs-canonical-functional-source/functional-schema-example/`
- `.docs/cfs-canonical-functional-source/scopes/erp/README.md`

Analiza el código fuente, especificaciones, planes de desarrollo y demás fuentes relevantes del repositorio que correspondan al scope `erp`, siguiendo los criterios de inclusión y exclusión definidos para dicho scope.

Genera o actualiza exclusivamente los ficheros del CFS bajo:

`.docs/cfs-canonical-functional-source/scopes/erp/functional-source/`

(ficheros globales `_index.md`, `_roles.md`, `_glossary.md`, `_relations.md` y un `mod-<modulo>.md` por módulo), siguiendo la estrategia de tres pasadas (inventario → módulos → consolidación) definida en `extraction-prompt.md`.

El resultado debe cumplir íntegramente `functional-schema.md`.

Si el directorio ya contiene ficheros, trátalo como una actualización conservadora: preserva los IDs y referencias existentes siempre que los conceptos funcionales sigan siendo los mismos, regenera sólo los ficheros de los módulos afectados y ejecuta después la pasada de consolidación.

No modifiques:

- `README.md`
- `extraction-prompt.md`
- `functional-schema.md`
- `functional-schema-example/`
- los README de los scopes
- los CFS de otros scopes
- el código fuente
- las especificaciones o planes originales

No generes todavía manuales, infografías, diagramas ni otros artefactos finales.

Antes de finalizar, ejecuta las validaciones establecidas en `functional-schema.md`.

Si detectas información insuficiente, contradicciones entre fuentes, elementos que no pueden determinarse o alguna limitación del propio schema, refléjalo conforme a las reglas CFS y notifícalo también brevemente al finalizar, sin modificar unilateralmente el schema.
```

### Uso para otros scopes

Para generar otro CFS debería ser suficiente con sustituir el identificador y las rutas correspondientes.

Por ejemplo:

```text
erp
→ scopes/erp/README.md
→ scopes/erp/functional-source/

fontenebro-nexus
→ scopes/fontenebro-nexus/README.md
→ scopes/fontenebro-nexus/functional-source/

nexus-core
→ scopes/nexus-core/README.md
→ scopes/nexus-core/functional-source/
```

De esta forma, las instrucciones generales permanecen estables y reutilizables, mientras que cada ejecución sólo necesita indicar qué scope debe analizarse.

### Principio recomendado

El prompt de ejecución NO debería volver a describir exhaustivamente cómo debe construirse el CFS.

La distribución de responsabilidades debe mantenerse así:

```text
Prompt de ejecución
        │
        │ indica QUÉ scope procesar
        ▼
extraction-prompt.md
        │
        │ define CÓMO investigar y extraer
        ▼
functional-schema.md
        │
        │ define CÓMO representar el resultado
        ▼
scopes/<scope>/README.md
        │
        │ define QUÉ pertenece al scope
        ▼
functional-source/ (multi-fichero)
        │
        │ contiene el conocimiento funcional resultante
        ▼
Artefactos derivados
```

Esto evita duplicar instrucciones en cada ejecución y reduce el riesgo de que diferentes prompts terminen generando CFS con criterios distintos.