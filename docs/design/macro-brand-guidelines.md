# Banco Macro - Brand Guidelines para Frontend

> Resumen de las directrices de marca de Banco Macro aplicadas al frontend del sistema RAG enterprise.
> Fuente: Content Design System (croMa) y Brandbook institucional.

---

## 1. Tipografía

### Familia Tipográfica

**DM Sans** es la unica familia tipográfica permitida en la interfaz.

### Variantes y Uso

| Contexto | Peso | Ejemplo de clase |
|----------|------|------------------|
| Titulos principales (h1) | ExtraBold (800) | `font-extrabold` |
| Subtitulos (h2, h3) | Bold (700) o ExtraBold (800) | `font-bold` / `font-extrabold` |
| Cuerpo de texto | Medium (500) | `font-medium` |
| Labels / Captions | Regular (400) o Medium (500) | `font-normal` / `font-medium` |

### Ajustes Tipográficos

- **Interlineado**: Cerrado (leading-tight en Tailwind)
- **Interletrado**: -0.025em (tracking-tight en Tailwind, o `letter-spacing: -0.025em`)

---

## 2. Paleta de Colores

### Colores Primarios

| Color | HEX | HSL (CSS var) | Uso principal |
|-------|-----|---------------|---------------|
| Azul Macro | #0039E3 | 225 100% 45% | CTA, titulares, fondos principales |
| Azul Oscuro | #00237C | 223 100% 24% | Foreground sobre secondary, profundidad |
| Azul Claro | #2D5FFF | 226 100% 59% | Links, acentos, primary en dark mode |
| Azul Accent | #5A89FF | 223 100% 68% | Iconos interactivos, bordes de inputs |

### Colores por Segmento

| Segmento | Color | HEX | Uso |
|----------|-------|-----|-----|
| **Individuos** | Rosa | #FF7DCB | Botones CTA, acentos, destacados |
| **Agro** | Verde | #24BA4E | Acentos para seccion agro |
| **Empresas** | Azul Oscuro | #00237C | Acentos para seccion empresas |

### Colores Neutrales

| Nombre | HEX | Uso |
|--------|-----|-----|
| Neutral 50 | #FEFEFE | Cards, superficies |
| Neutral 100 | #F8FAFA | Background principal |
| Neutral 400 | #C4C7C7 | Bordes, separadores |

### Colores de Fondo

| Token | HEX | Uso |
|-------|-----|-----|
| Brand BG | #E9F3FF | Fondos claros, hover states |
| Brand BG 2 | #CFE3FF | Bordes suaves, secondary |

### Texto

- **Texto principal**: #343F49 (gris oscuro) sobre fondos claros
- **Texto sobre fondos oscuros**: #FFFFFF (blanco)
- **Texto muted**: Gris medio para descripciones secundarias

---

## 3. Morfologia

### Bordes Redondeados

Todos los elementos visuales deben tener bordes redondeados. **Nunca usar bordes rectos ni en punta.**

| Elemento | Radio | Token |
|----------|-------|-------|
| Text fields, autocomplete | 4px | `rounded-xs` |
| Chips, cards pequenas | 8px | `rounded-sm` |
| Cards, containers, FABs | 12px | `rounded-md` |
| Dialogs, bottom sheets | 16px | `rounded-lg` |
| Botones, badges, pastillas | 100px | `rounded-full` |

### Proporcion de Grilla

Las composiciones deben respetar la regla:
- **40%** Imagen/contenido visual
- **30%** Textos
- **30%** Margenes y espaciados

### Elementos de Fondo

Usar como estructuras compositivas:
- Circulos
- Arcos
- Medios arcos

### Cards

- **Traslucidas**: Compuestas por capas de fondo degradado, granulado, luminosidad y borde lineal
- **Pastillas de texto**: Completamente redondeadas (`rounded-full`), contenido en una sola linea

---

## 4. Elevacion (Sombras)

| Nivel | Uso | Token Tailwind |
|-------|-----|----------------|
| Level 1 | Cards base, hover sutil | `shadow-lvl-1` |
| Level 2 | Popovers, dropdowns | `shadow-lvl-2` |
| Level 3 | FABs, cards elevadas | `shadow-lvl-3` |
| Level 4 | Modales, dialogs | `shadow-lvl-4` |
| Level 5 | Notificaciones flotantes | `shadow-lvl-5` |

---

## 5. Fotografia

- Estetica minimalista, luminosa, cotidiana
- Sin sobrecarga visual
- Maximo una imagen de persona por composicion expansiva

---

## 6. Iconografia

Libreria: **Lucide React** (consistente con shadcn/ui)

| Tamano | Dimensiones | Uso |
|--------|-------------|-----|
| LG | 64x64 | Heroes, empty states |
| MD | 48x48 | Cards destacadas |
| SM | 32x32 | Navegacion, acciones |
| XS | 24x24 | Inline, listas |

**Reglas estrictas:**
- No alterar escalas ni grosor
- Siempre acompanar iconos con texto (no reemplazar palabras solo por iconos)

---

## 7. Logo y Assets

| Asset | Path | Uso |
|-------|------|-----|
| Logo completo | `frontend/public/logo-macro.svg` | Login, empty states |
| Isologo | `frontend/public/isologo-macro.svg` | Sidebar expandido |
| Isotype | `frontend/public/iso-macro.svg` | Sidebar colapsado, favicon |
| IA Platform | `frontend/public/ia-platform.svg` | Header del chat |
| Favicon | `frontend/public/favicon.svg` | Browser tab |

---

## 8. Dark Mode

El dark mode usa variaciones de los azules de marca:
- Background: Azul muy oscuro derivado de #00237C
- Textos: Azul muy claro para contraste
- Primary: Se sube a `--brand-primary-light` (#2D5FFF) para visibilidad

---

## Implementacion Tecnica

- **CSS Variables**: Definidas en `frontend/src/app/globals.css`
- **Tailwind Config**: Mapeadas en `frontend/tailwind.config.js`
- **Tokens de marca**: Usar clases Tailwind (`text-brand`, `bg-brand-individuos`, etc.), no hex hardcodeados
