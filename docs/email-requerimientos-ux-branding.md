**Asunto:** Requerimientos de Marca y Comunicación Visual — Plataforma IA

---

Hola equipo,

Les escribimos desde el equipo de desarrollo de la plataforma de IA. Estamos en la fase de integración visual del frontend y necesitamos alinear la interfaz con la identidad de marca de Banco Macro.

Para avanzar sin bloqueos, les detallamos a continuación todo lo que necesitamos. Organizamos los requerimientos en tres bloques para que sea más fácil de gestionar.

---

## 1. Identidad Visual / Manual de Marca

### 1.1 Logotipo

- Logo principal del banco en formato **SVG** (vectorial, para uso web).
- Variante **isotipo o ícono** (sin texto), para utilizarlo como avatar del agente en el chat y en el menú lateral cuando está colapsado.
- Variantes para **fondo claro y fondo oscuro**, o indicación de cuál corresponde usar en cada caso.
- Si existe un logo secundario aprobado para productos digitales internos, también nos sería útil.

### 1.2 Favicon

- Ícono para la pestaña del navegador en formato **SVG o PNG de 512×512 px** (nosotros generamos los tamaños adicionales que requiere la web).

### 1.3 Paleta de colores

Necesitamos los códigos **hexadecimales exactos** de los siguientes colores:

- **Primario** — color principal de la marca (botones, links, elementos destacados).
- **Secundario** — color complementario.
- **Acento** — para highlights, estados activos, elementos interactivos secundarios.
- **Semánticos** (si los tienen definidos): éxito (verde), error (rojo), advertencia (amarillo).

La aplicación soporta **modo claro y modo oscuro**. Si cuentan con una paleta definida para modo oscuro, necesitamos esas variantes. En caso contrario, la derivamos nosotros a partir de la paleta principal y se las enviamos para aprobación.

### 1.4 Tipografía

- ¿Cuáles son las familias tipográficas aprobadas para **uso en web**?
- Actualmente utilizamos **Inter** (para cuerpo de texto) y **Outfit** (para títulos), ambas de Google Fonts. ¿Son compatibles con los lineamientos del banco, o hay una tipografía institucional que debamos usar?

### 1.5 Otros elementos

- ¿Tienen un estándar de **bordes redondeados** (radio de esquinas)? Ej: 4px, 8px, 12px, o esquinas rectas.
- ¿Existe una **grilla o sistema de espaciado** base definido en la guía de diseño digital?

> **Documento solicitado:** Manual de Marca / Brand Guidelines completo (PDF, Figma o link).

---

## 2. Comunicación y Tono de Voz

La interfaz tiene textos visibles al usuario en toda la experiencia (login, chat, mensajes del asistente, disclaimers). Necesitamos alinear estos textos con los lineamientos de comunicación del banco.

### 2.1 Tratamiento

Actualmente toda la interfaz utiliza **voseo argentino** de tono cercano (ej: *"Escribí tu consulta"*, *"Consultá normativas"*). ¿Es el tratamiento correcto, o prefieren el uso de **usted** (*"Escriba su consulta"*)?

### 2.2 Tono general

- ¿El asistente debe comunicarse de forma **cercana y amigable**, o **formal e institucional**?
- ¿Existen **palabras, expresiones o formatos prohibidos** en la comunicación digital del banco?

### 2.3 Textos de interfaz que requieren validación

A continuación listamos los textos actuales de la aplicación. Pueden aprobarlos tal cual, sugerirnos alternativas, o indicarnos si requieren revisión de otra área (ej: Legales):

| Ubicación en la app | Texto actual |
|---|---|
| Mensaje de bienvenida | *"¿En qué puedo ayudarte?"* |
| Subtítulo de bienvenida | *"Consultá normativas, procesos y documentos internos. Las respuestas se generan con información de la base documental oficial."* |
| Disclaimer al pie del chat | *"Las respuestas se generan a partir de la base documental interna del banco."* |
| Indicador de estado del asistente | *"En línea"* |
| Placeholder del campo de texto | *"Escribí tu consulta sobre normativas, procesos o documentos..."* |
| Texto mientras procesa la respuesta | *"Analizando documentos..."* |

### 2.4 Consultas sugeridas

Al iniciar una conversación nueva, mostramos al usuario 4 tarjetas con consultas de ejemplo. Actualmente tenemos:

1. **Política de Créditos** — *"Límites, requisitos y condiciones"*
2. **Onboarding de Clientes** — *"Proceso de registro y validación"*
3. **Manual de Riesgos** — *"Guía de evaluación y mitigación"*
4. **Procedimientos RRHH** — *"Beneficios, licencias y normas"*

¿Son representativos de los casos de uso que quieren destacar, o prefieren otros ejemplos?

> **Documento solicitado:** Manual o Guía de Comunicación / Tono de Voz (PDF o Doc), si existe.

---

## 3. Nombre del Producto y del Agente

Actualmente usamos nombres provisionales en la interfaz. Necesitamos las definiciones oficiales:

| Elemento | Nombre provisional actual | ¿Qué necesitamos? |
|---|---|---|
| Nombre del producto | *"Enterprise RAG"* | Nombre oficial de la herramienta (aparece en login, pestaña del navegador y menú lateral) |
| Nombre del agente | *"Asistente Bancario"* | Nombre que ve el usuario en el chat (ej: *"Asistente Macro"*, un nombre propio, etc.) |
| Tagline / subtítulo | *"Acceso Seguro al Conocimiento Corporativo"* | Frase breve que acompaña al nombre en la pantalla de login |
| Descripción corta | *"Base Documental"* | Texto que aparece debajo del nombre en el menú lateral |
| Dominio de email | *nombre@banco.com* | Dominio correcto para el placeholder del campo de login (ej: `@macro.com.ar`) |

---

## Resumen de entregables

Para facilitar el seguimiento, este es el listado consolidado de lo que necesitamos recibir:

| # | Entregable | Formato preferido |
|---|---|---|
| 1 | Manual de Marca / Brand Guidelines | PDF / Figma / Link |
| 2 | Manual de Comunicación / Tono de Voz | PDF / Doc |
| 3 | Logo SVG — versión completa + isotipo | `.svg` |
| 4 | Variantes de logo para fondo claro y oscuro | `.svg` o `.png` |
| 5 | Favicon | `.svg` o `.png` 512×512 |
| 6 | Paleta de colores con códigos hexadecimales | En el manual o listado aparte |
| 7 | Tipografía web (si es propietaria) | `.woff2` + indicación de pesos |
| 8 | Nombre oficial del producto y del agente | Texto |
| 9 | Validación o alternativas para los textos de interfaz | Texto |

---

Con esta información podemos avanzar con la integración visual sin necesidad de agendar una reunión. Si algún punto requiere mayor contexto o prefieren que lo veamos en una llamada breve, quedo a disposición.

Quedo atento a sus comentarios.

Saludos cordiales
