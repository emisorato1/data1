# T5-S7-02: Integración Diseño Macro en Frontend

| ID | T5-S7-02 |
| - | - |
| Track | T5 (Frontend) |
| Sprint | 7 |
| Estado | Done |
| Owner | Ema |
| Bloqueado por | T5-S3-01, T5-S3-02, T5-S4-01 |
| Bloquea a | T5-S8-01, T5-S8-02 |

## Contexto

El proyecto requiere la creación y estandarización del diseño frontend aplicando el Content Design System (croMa) y el Brandbook institucional de Banco Macro [1, 2]. El agente debe utilizar un enfoque de "Fidelidad Progresiva", asegurando primero la estructura y flujos, para luego aplicar un sistema de diseño que proyecte profesionalismo, digitalización e innovación, manteniendo una voz integradora, simple, pragmática y confiable [3-5].

## Spec

Ejecutar el diseño y maquetación de las interfaces digitales aplicando estrictamente el modelo de Atomic Design [6]. Se deben respetar a rajatabla las proporciones de layout, paletas de color por segmento, uso tipográfico específico y las directrices de UX Writing y accesibilidad dictadas por el manual de marca de Banco Macro [7, 8].

## Acceptance Criteria

- [ ] **Fidelidad Progresiva:** Aplicar flujos de usuario y wireframes validados antes de pasar al diseño visual de alta fidelidad y código final [5].
- [ ] **Tipografía:** Usar exclusivamente la familia **DM Sans** [9].
  - Títulos (h1, h2): Variante **ExtraBold**, interlineado cerrado, interletrado de -25 [9, 10].
  - Párrafos (p): Variante **Medium**, interlineado cerrado, interletrado de -25 [9, 10].
- [ ] **Sistema Cromático:**
  - **Color Principal:** Azul Macro (HEX #0039E3) para botones CTA, titulares y fondos [11-13].
  - **Textos:** Uso de color gris para párrafos de lectura; blanco para versiones negativas sobre fondos oscuros [12].
  - **Segmentos:** Aplicar color identitario en acentos o botones según corresponda: Individuos (Rosa HEX #FF7DCB), Agro (Verde HEX #24BA4E), o Empresas (Azules específicos como #00237C o #E9F3FF) [13, 14].
- [ ] **Morfología y Layout:**
  - **Bordes:** Todos los elementos gráficos (cards, botones, contenedores) deben tener **bordes redondeados** [15].
  - **Proporción de Grilla:** Las piezas deben ser aireadas respetando la regla: **40% Imagen, 30% Textos, 30% Márgenes y espaciados** [16, 17].
  - **Elementos de fondo:** Utilizar círculos, arcos o medios arcos como estructuras compositivas [15].
  - **Cards:** Utilizar cards traslúcidas (capas de fondo degradado, granulado, luminosidad y borde lineal) o pastillas de texto (100% redondeadas, en una sola línea) [18, 19].
- [ ] **Fotografía e Imágenes:**
  - Estética minimalista, luminosa, cotidiana y sin sobrecarga [20]. 
  - No utilizar más de una imagen de persona en la misma composición expansiva [21].
- [ ] **Iconografía y Accesibilidad (WCAG):**
  - **Tamaños en grilla:** LG (64x64), MD (48x48), SM (32x32), XS (24x24) [22]. No alterar las escalas ni grosor de los iconos [23].
  - **Accesibilidad:** Uso obligatorio de etiquetas `alt` y `title` en imágenes, y `<title>` / `<desc>` en SVGs [24]. Garantizar contrastes altos [24].
  - **Regla estricta:** No reemplazar palabras únicamente por iconos; siempre deben ir acompañados de texto para dar contexto [24, 25].
- [ ] **Tono de Voz y UX Writing:**
  - **Economía de palabras ("lo que no suma, resta"):** Eliminar tecnicismos y priorizar lenguaje cotidiano (Ej: "Validá tu DNI" en vez de "Enrolar tu DNI") [26, 27].
  - **Inclusividad:** Usar sustantivos epicenos, términos inclusivos o pronombres como "quien", evitando sesgos de género [28].
  - **Estilo de redacción:** Escribir productos genéricos en minúscula (Ej: "tarjeta de crédito") y evitar abreviaturas (no usar "TC") [29, 30]. Uso moderado de imperativos, combinándolos con preguntas o primera persona del plural (Ej: "¿Ya conocés nuestras promociones?") [30].

## Archivos a crear/modificar

- `.agents/skills/custom-frontend-design/SKILL.md` (crear)
- `docs/design/macro-brand-guidelines.md` (crear)
- `docs/design/macro-ux-writing-rules.md` (crear)
- `src/components/ui/...` (modificar/crear según se requiera aplicando DM Sans y Azul Macro)

## Decisiones de diseño

- **Diseño centrado en las personas:** La experiencia debe ser intuitiva y resolver los objetivos de los clientes de Macro de forma amigable [4].
- **Morfología curva y amigable:** Se descartan los bordes rectos o en punta para transmitir la cercanía y contención que define a la marca [15].
- **Atomic Design:** Todo componente (botones, pastillas, cards traslúcidas) será construido desde su expresión más simple para mantener consistencia en todo el ecosistema digital del banco [6].

## Out of scope

- Testing de usabilidad con usuarios finales reales (se abordará en una spec posterior).
- Testing de performance/carga.
- Integración con el backend para datos reales de clientes.

---

## Implementación Realizada

### Iteración 1: Mockup inicial (commit b0ba248)

Primera implementación del mockup de diseño Macro aplicando los lineamientos base de croMa.

### Iteración 2: Sistema de Citaciones y Source Panel

Se implementó el sistema completo de citaciones inline y panel de fuentes para los mensajes del asistente RAG, siguiendo el estilo visual de Gemini.

#### Cambios en Backend (Python)

| Archivo | Cambio |
|---------|--------|
| `src/application/graphs/nodes/retrieve.py` | **Fix `SET LOCAL hnsw.ef_search`**: PostgreSQL no acepta bind parameters (`$1`) en comandos `SET`. Se cambió de bind parameter a interpolación f-string con validación `int()` (el valor proviene de Pydantic settings, no de input del usuario). |
| `src/application/graphs/nodes/assemble_context.py` | **Se agregó `chunk_text: content`** al diccionario de sources para que el frontend reciba el fragmento original del documento y pueda mostrarlo en el panel de fuentes. |

#### Cambios en Frontend (TypeScript/React)

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/chat/message-bubble.tsx` | **Reescritura mayor**: Se creó la función `injectCitationChips()` que recorre recursivamente los children de React para reemplazar patrones `[N]` en texto con componentes `<CitationChip>` inline. Se usa `useMemo` para generar `mdComponents` que sobreescriben los elementos de bloque de ReactMarkdown (`p`, `li`, `td`, `th`, `blockquote`), inyectando las citaciones dentro del mismo elemento DOM sin provocar saltos de línea. Props agregados: `activeCitationIndex`, `onCitationClick`, `onSourceBadgeClick`. |
| `frontend/src/components/chat/citation-chip.tsx` | **Actualizado**: Muestra icono `Link` (lucide-react) + numero de fuente en formato superscript. Estilos actualizados para flujo inline con el texto. |
| `frontend/src/components/chat/source-panel.tsx` | **Rediseñado**: Layout de card individual por chunk (header con icono + nombre de documento + pagina, cuerpo con excerpto en blockquote). Chips de navegacion al pie con icono link + numero para consistencia visual. Se reemplazo `BookOpen` por `Link` como icono principal. |
| `frontend/src/app/(chat)/chat/page.tsx` | **Modificado**: Se restauró estado `activeCitationIndex`. Se agregaron handlers `handleCitationClick` (para chips inline) y `handleSourceBadgeClick` (para badges de documento). Ambos abren el panel de fuentes. Se pasan todos los props necesarios a `MessageBubble`. |

#### Decisiones Tecnicas

1. **ReactMarkdown + componentes inline**: Usar `content.split(/(\[\d+\])/g)` y renderizar cada parte como un `<ReactMarkdown>` separado generaba saltos de linea (cada uno crea su propio `<p>` wrapper). La solucion fue usar la prop `components` de ReactMarkdown para sobreescribir elementos de bloque y dentro de esos overrides recorrer recursivamente los children para reemplazar patrones `[N]` con `<CitationChip>`.
2. **`SET LOCAL` de PostgreSQL**: `SET LOCAL hnsw.ef_search = :ef_search` falla con asyncpg porque PostgreSQL no soporta bind parameters en `SET`. Se usa f-string con `int()` como validacion dado que el valor proviene de configuracion validada por Pydantic, no de input del usuario.
3. **`chunk_text` en sources**: Se agrego el campo al diccionario de sources en `assemble_context_node`. Los sources se almacenan como JSONB `{"items": [...]}` en la tabla `messages`. Agregar `chunk_text` incrementa el almacenamiento pero es aceptable para la funcionalidad del panel de fuentes.

#### Estado de Build

- TypeScript build pasa correctamente.
- Errores pre-existentes de imports de test (`@testing-library/react`, `vitest`) no relacionados con estos cambios.