# CFS — Extraction Prompt

## Objetivo

Generar o actualizar el Canonical Functional Source (CFS) correspondiente a un scope concreto del sistema.

El CFS es una representación funcional canónica intermedia destinada a servir como fuente de verdad para la posterior generación de documentación, manuales, diagramas, infografías y otros artefactos derivados.

Este prompt define el PROCEDIMIENTO DE EXTRACCIÓN.

La estructura, campos, identificadores, estados, valores normalizados y reglas de representación del resultado están definidos exclusivamente en:

`functional-schema.md`

No dupliques ni redefinas aquí dichas reglas.

---

## 1. Archivos normativos y de contexto

Antes de comenzar debes leer:

1. `functional-schema.md`
2. `functional-schema-example/`
3. `scopes/<scope>/README.md`
4. Los ficheros existentes bajo `scopes/<scope>/functional-source/`, si se trata de una actualización.

La prioridad normativa es:

1. `functional-schema.md`
2. Este `extraction-prompt.md`
3. `scopes/<scope>/README.md`
4. `functional-schema-example/`

`functional-schema-example/` es únicamente ilustrativo y nunca prevalece sobre el schema.

---

## 2. Resultado

Debes generar o actualizar exclusivamente los ficheros del CFS bajo:

`scopes/<scope>/functional-source/`

es decir, los ficheros globales (`_index.md`, `_roles.md`, `_glossary.md`, `_relations.md`) y un `mod-<modulo>.md` por módulo, conforme a la estructura multi-fichero definida en `functional-schema.md` (sección 7).

El resultado DEBE cumplir íntegramente `functional-schema.md`.

### 2.1 Estrategia de generación en tres pasadas

Para scopes con más de un módulo, la generación DEBE organizarse así:

1. **Inventario**: identificar los módulos del scope, asignar ID canónico a todos (extraídos o no) y crear o actualizar el esqueleto de `_index.md`: inventario de ficheros, scope y límites, visión global provisional y stubs de los módulos pendientes de extracción (sección 7.7 del schema).
2. **Extracción por módulo**: generar o actualizar cada `mod-<modulo>.md` de forma autocontenida, con sus propias fuentes y cobertura.
3. **Consolidación** (obligatoria, nunca omitirla): actualizar `_roles.md`, `_glossary.md`, `_relations.md` y `_index.md` con los impactos de la pasada anterior, verificar las referencias cruzadas entre ficheros y ejecutar la validación de scope.

Una actualización parcial (sólo algunos módulos) DEBE ejecutar igualmente la pasada de consolidación.

No generes documentación de usuario, infografías, diagramas ni otros artefactos finales.

---

## 3. Archivos que NO debes modificar

Durante la extracción de un scope NO DEBES modificar:

- `README.md` del CFS.
- `extraction-prompt.md`.
- `functional-schema.md`.
- `functional-schema-example/`.
- CFS pertenecientes a otros scopes.
- Código fuente del producto.
- Especificaciones o planes originales.

Si descubres una situación que el schema no permite representar adecuadamente, NO modifiques el schema.

Registra la incidencia o indícala expresamente al finalizar para que pueda evaluarse una evolución deliberada del schema.

---

## 4. Delimitación del scope

Utiliza:

`scopes/<scope>/README.md`

como definición de qué debe incluirse y excluirse del análisis.

No incorpores funcionalidad perteneciente a otros scopes salvo al nivel necesario para explicar una dependencia funcional.

Cuando exista un CFS para el scope externo, utiliza las referencias entre scopes definidas en `functional-schema.md`.

Evita duplicar responsabilidades funcionales pertenecientes canónicamente a otro scope.

---

## 5. Fuentes de información

Analiza todas las fuentes relevantes disponibles dentro del ámbito definido para el scope.

Según corresponda, pueden incluir:

- Código backend.
- Código frontend.
- Interfaces de usuario.
- Configuración.
- Modelo de datos.
- APIs.
- Tests.
- Especificaciones.
- Planes de desarrollo.
- Documentación funcional.
- Documentación técnica que aporte información funcional.

No asumas que una única fuente representa completamente el comportamiento.

Cruza información cuando sea necesario.

---

## 6. Prioridad entre fuentes

El objetivo principal es describir el comportamiento real y actual del producto.

Como regla general:

1. El comportamiento verificable en la implementación actual tiene prioridad para determinar qué está implementado.
2. Las especificaciones vigentes aportan intención y contexto funcional.
3. Los planes históricos aportan contexto, pero no demuestran por sí mismos que una funcionalidad esté implementada.

Una funcionalidad presente únicamente en un plan NO DEBE clasificarse como `IMPLEMENTED`.

Si diferentes fuentes se contradicen y no puedes resolver la contradicción con suficiente evidencia, utiliza `CONFLICT`.

No soluciones silenciosamente las discrepancias.

---

## 7. No inventar

No completes huecos suponiendo cómo debería funcionar la aplicación.

No utilices como evidencia:

- patrones típicos de un ERP;
- buenas prácticas generales;
- comportamientos habituales de otros productos;
- lo que resultaría lógico implementar;
- nombres de clases o métodos sin verificar su significado funcional.

Utiliza los estados de evidencia definidos en `functional-schema.md`:

- `CONFIRMED`
- `INFERRED`
- `UNKNOWN`
- `CONFLICT`

Diferencia además el estado de evidencia del estado de implementación.

---

## 8. Perspectiva funcional

Extrae principalmente información necesaria para responder:

- Qué puede hacer el usuario.
- Qué roles pueden hacerlo.
- Desde dónde puede hacerlo.
- Sobre qué entidades actúa.
- Qué datos necesita.
- Qué condiciones deben cumplirse.
- Qué reglas limitan la acción.
- Qué resultado obtiene.
- Qué estados cambian.
- Qué automatismos se ejecutan.
- Qué efectos secundarios existen.
- Qué otros módulos participan.
- Qué excepciones pueden producirse.
- Cómo encaja la acción en un flujo de trabajo mayor.

No conviertas el CFS en documentación de arquitectura ni en un inventario exhaustivo de componentes técnicos.

Los detalles técnicos deben utilizarse principalmente como evidencia y trazabilidad.

---

## 9. Análisis de frontend

No te limites a analizar servicios o endpoints.

El frontend puede revelar información funcional esencial como:

- Acciones realmente disponibles.
- Botones y menús.
- Terminología visible al usuario.
- Validaciones.
- Campos obligatorios.
- Restricciones según estado.
- Diferencias según rol.
- Navegación.
- Flujos.
- Confirmaciones.
- Opciones que el backend admite pero que el usuario no tiene expuestas.

Documenta las superficies de UI conforme a `functional-schema.md`.

No documentes cada componente Angular únicamente por existir.

---

## 10. Análisis de backend

Utiliza el backend para verificar, entre otros:

- Operaciones disponibles.
- Reglas de negocio.
- Permisos.
- Validaciones.
- Estados.
- Transiciones.
- Automatismos.
- Efectos secundarios.
- Integraciones.
- Persistencia.
- Restricciones no visibles directamente desde frontend.

No confundas la existencia de un método o endpoint con una funcionalidad accesible al usuario.

Cruza la información con frontend y otras fuentes cuando sea necesario.

---

## 11. Terminología

Prioriza la terminología que realmente ve el usuario.

Cuando código, base de datos, documentación e interfaz utilicen términos diferentes para el mismo concepto:

1. Identifica la equivalencia.
2. Regístrala en el glosario.
3. Utiliza de manera consistente el término funcional canónico definido.

No renombres silenciosamente conceptos para hacerlos más comprensibles.

---

## 12. Creación de un CFS nuevo

Si el CFS del scope (`scopes/<scope>/functional-source/`) todavía no existe:

1. Analiza el scope completo.
2. Identifica los elementos funcionales.
3. Asigna identificadores siguiendo `functional-schema.md`.
4. Genera todas las secciones obligatorias.
5. Registra fuentes y cobertura.
6. Realiza la validación final definida por el schema.

---

## 13. Actualización de un CFS existente

Si el directorio `functional-source/` ya contiene ficheros, trátalo como una actualización conservadora.

DEBES:

- Limitar la regeneración a los ficheros de los módulos afectados y ejecutar después la pasada de consolidación sobre los ficheros globales.
- Mantener IDs existentes cuando el concepto funcional siga siendo el mismo.
- Mantener terminología canónica salvo evidencia de que ha cambiado.
- Actualizar evidencia cuando aparezcan nuevas fuentes.
- Incorporar funcionalidades nuevas con IDs nuevos.
- Actualizar estados de implementación cuando corresponda.
- Marcar como `REMOVED` o `DEPRECATED` elementos que hayan dejado de formar parte del producto cuando exista evidencia suficiente.
- Revisar referencias afectadas por los cambios.
- Actualizar matrices, relaciones, flujos y trazabilidad afectados.

NO DEBES:

- Renumerar IDs para que vuelvan a quedar consecutivos.
- Reutilizar IDs eliminados.
- Crear un ID nuevo para una funcionalidad existente únicamente porque haya cambiado su nombre visible.
- Reescribir innecesariamente partes no afectadas.
- Eliminar información histórica funcionalmente relevante sin justificarlo.

El objetivo es mantener estabilidad referencial entre versiones del CFS.

---

## 14. Valores desconocidos y ausencia de elementos

Respeta estrictamente la diferencia definida por el schema entre:

- `NONE`
- `UNKNOWN`
- `NOT_APPLICABLE`

No utilices `NONE` cuando simplemente no hayas encontrado información.

No omitas silenciosamente campos obligatorios.

---

## 15. Trazabilidad

Registra las fuentes conforme a `functional-schema.md`.

Siempre que sea razonablemente posible, identifica una localización funcionalmente estable:

- archivo;
- clase;
- método;
- componente;
- servicio;
- endpoint;
- sección;
- ruta;
- pantalla;
- plan;
- especificación.

Evita depender exclusivamente de números de línea si una referencia semántica más estable es posible.

---

## 16. Seguridad

No copies al CFS:

- Contraseñas.
- Tokens.
- API keys.
- Connection strings con secretos.
- Credenciales reales.
- Datos personales reales innecesarios.
- Información sensible encontrada accidentalmente.

Puedes registrar la existencia de una configuración o credencial cuando tenga significado funcional, pero nunca su valor real.

---

## 17. Exhaustividad

El objetivo no es producir un resumen.

El objetivo es producir una representación funcional suficientemente completa para que otros agentes puedan generar artefactos derivados sin volver a investigar el producto.

Antes de finalizar, comprueba que has identificado, cuando existan:

- Módulos.
- Roles.
- Entidades.
- Estados.
- Transiciones.
- Superficies de UI.
- Funcionalidades.
- Reglas de negocio.
- Automatismos.
- Relaciones.
- Flujos internos.
- Flujos transversales.
- Dependencias con otros scopes.
- Terminología funcional.
- Incertidumbres.
- Conflictos.
- Carencias.
- Evidencias.

---

## 18. Validación

Antes de dar por terminada la generación o actualización:

1. Ejecuta todas las comprobaciones establecidas en la sección de validación de `functional-schema.md`, en sus dos niveles (por fichero y de scope).
2. Comprueba que no existen referencias internas rotas.
3. Comprueba que no existen IDs duplicados.
4. Comprueba que no has utilizado información planificada como evidencia de implementación actual.
5. Comprueba que los elementos `CONFIRMED` tienen evidencia.
6. Comprueba que incertidumbres y conflictos están expresados explícitamente.
7. Comprueba que el scope no contiene responsabilidad funcional duplicada innecesariamente desde otro scope.
8. Comprueba que otro agente podría generar los artefactos documentales previstos utilizando únicamente este CFS.
9. Si existe `tools/lint-cfs.mjs` (relativo a la raíz del sistema CFS), ejecútalo sobre `scopes/<scope>/functional-source/` y corrige cualquier error estructural antes de finalizar.

Si la cobertura es insuficiente porque no has podido acceder a fuentes relevantes, establece:

`generation-status: PARTIAL`

y explica claramente las limitaciones.

---

## 19. Resultado final de la ejecución

Al terminar:

- Guarda el CFS generado o actualizado en la ruta correspondiente.
- No generes otros artefactos.
- No modifiques los archivos normativos.
- Informa de forma breve de:
  - resultado de la generación;
  - cobertura;
  - principales incertidumbres o conflictos;
  - fuentes relevantes que no hayan podido analizarse;
  - cualquier posible limitación detectada en el propio schema.

El contenido funcional completo debe quedar en el CFS, no únicamente en el mensaje final.