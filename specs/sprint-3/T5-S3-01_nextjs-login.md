# T5-S3-01: Setup Next.js + login screen

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T5-S3-02 |
| Depende de | T2-S2-01 |
| Skill | `frontend/SKILL.md` > Seccion "Autenticacion" |
| Estimacion | L (4-8h) |

## Contexto

Inicializar frontend y primera pantalla funcional. Ema pivota de backend a frontend en Sprint 3. El frontend es Next.js con App Router, TypeScript estricto, y shadcn/ui.

## Spec

Setup completo de Next.js con TypeScript estricto, Tailwind, shadcn/ui, y pantalla de login funcional que integra con la API de auth.

## Acceptance Criteria

- [ ] Next.js >= 15.5.10 inicializado en `frontend/` con React >= 19.2.4
- [ ] TypeScript estricto configurado (`strict: true`, `noUncheckedIndexedAccess: true`, prohibido `any`)
- [ ] Tailwind CSS + shadcn/ui instalados
- [ ] Pantalla de login: email + password -> llama `POST /api/v1/auth/login`
- [ ] JWT almacenado en HTTPOnly cookie (set por backend)
- [ ] Redirect a chat despues de login exitoso
- [ ] Pantalla de error si credenciales invalidas
- [ ] Layout base con sidebar (vacia por ahora) + main content area

## Archivos a crear/modificar

- `frontend/package.json` (crear)
- `frontend/tsconfig.json` (crear)
- `frontend/next.config.js` (crear)
- `frontend/tailwind.config.ts` (crear)
- `frontend/app/(auth)/login/page.tsx` (crear)
- `frontend/app/(chat)/layout.tsx` (crear)
- `frontend/components/ui/` (crear — shadcn components)

## Decisiones de diseno

- Next.js App Router sobre Pages Router: mejor para streaming SSE, server components
- TypeScript strict sin `any`: calidad de codigo, previene bugs en produccion
- shadcn/ui sobre MUI/Ant: componentes copiados (no dependencia), totalmente customizables

## Out of scope

- Chat UI (spec T5-S3-02)
- Admin dashboard (post-MVP)
- Dark mode (post-MVP)
- Tests de frontend (post-MVP)
