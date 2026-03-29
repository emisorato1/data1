# T5-S6-01: Dark mode

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | - |
| Skill | `frontend/SKILL.md` |
| Estimacion | S (1-2h) |

## Contexto

Dark mode is a standard UX feature that reduces eye strain and is expected in modern enterprise applications. Quick win that improves user satisfaction.

## Spec

Implement dark mode toggle in the Next.js frontend using Tailwind CSS dark mode classes, with user preference persistence.

## Acceptance Criteria

- [x] Toggle dark/light mode en header o sidebar
- [x] Tailwind dark mode classes aplicados a todos los componentes existentes
- [x] Preferencia persistida en localStorage
- [x] Respeta preferencia del sistema operativo (prefers-color-scheme) como default
- [x] Transicion suave entre modos (no flash)
- [x] Todos los componentes (chat, sidebar, login, documents) funcionales en dark mode
- [x] Tests visuales basicos (manual verifications done)

## Archivos a crear/modificar

- `frontend/src/components/theme-toggle.tsx` (ya existe — revisar cobertura dark classes)
- `frontend/src/components/theme-provider.tsx` (ya existe — usa next-themes)
- `frontend/src/app/globals.css` (ya tiene variables .dark — validar completitud)
- `frontend/tailwind.config.js` (ya configurado darkMode: ["class"])

## Decisiones de diseno

- **Tailwind dark: class strategy**: Permite toggle manual ademas de media query.
- **localStorage**: Simple, no requiere backend.

## Out of scope

- Temas personalizados
- Branding configurable por tenant
