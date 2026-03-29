# Plan de Testing Interno - Sprint 7

## Objetivo

Validar el funcionamiento completo de la plataforma RAG antes de avanzar a integración en DEV. Este testing cubre flujos funcionales, autenticación, manejo de errores y permisos.

## Alcance

| Incluido | Excluido |
|----------|----------|
| Testing funcional de features | Performance/carga (T1-S9-01) |
| Flujos de autenticación | Seguridad/pentesting (T2-S9-01) |
| Manejo de errores | Datos de producción |
| Permisos y aislamiento | Integración con OpenText real |
| Tests automatizados existentes | UI/UX detallado |

## Severidad de Bugs

| Nivel | Descripción | Acción |
|-------|-------------|--------|
| **Crítico** | Bloquea funcionalidad core, crashea sistema | Fix inmediato en sprint |
| **Alto** | Afecta funcionalidad importante, workaround difícil | Fix en sprint si posible |
| **Medio** | Experiencia degradada, workaround existe | Backlog priorizado |
| **Bajo** | Cosmético, mejora menor | Backlog normal |

## Prerrequisitos

- [ ] Backend corriendo (`uvicorn src.main:app`)
- [ ] Frontend corriendo (`npm run dev`)
- [ ] PostgreSQL + pgvector disponible
- [ ] Redis disponible
- [ ] Usuarios de prueba creados (ver seed data)
- [ ] Documentos de prueba indexados

---

## Área 1: Autenticación (AUTH)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| AUTH-01 | Login exitoso | 1. Ir a /login<br>2. Ingresar credenciales válidas<br>3. Click Login | Redirect a /chat, cookies JWT establecidas | Alta |
| AUTH-02 | Login fallido - password incorrecto | 1. Ir a /login<br>2. Ingresar email válido + password incorrecto<br>3. Click Login | Error "Credenciales inválidas", no redirect | Alta |
| AUTH-03 | Login fallido - usuario inexistente | 1. Ir a /login<br>2. Ingresar email no registrado<br>3. Click Login | Error "Credenciales inválidas" (sin revelar si existe) | Alta |
| AUTH-04 | Login fallido - campos vacíos | 1. Ir a /login<br>2. Dejar campos vacíos<br>3. Click Login | Validación en cliente, botón deshabilitado o error | Media |
| AUTH-05 | Logout exitoso | 1. Estar logueado<br>2. Click en Logout<br>3. Verificar estado | Redirect a /login, cookies limpiadas | Alta |
| AUTH-06 | Token refresh automático | 1. Login<br>2. Esperar expiración de access token<br>3. Realizar acción | Nuevo access token emitido, sesión continua | Alta |
| AUTH-07 | Sesión expirada completa | 1. Login<br>2. Esperar expiración de refresh token (o invalidar manualmente)<br>3. Realizar acción | Redirect a /login con mensaje | Alta |
| AUTH-08 | Acceso protegido sin auth | 1. Sin login, ir a /chat directamente | Redirect a /login | Alta |

---

## Área 2: Chat y Streaming (CHAT)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| CHAT-01 | Envío de mensaje simple | 1. Login<br>2. Ir a /chat<br>3. Escribir pregunta simple<br>4. Enviar | Respuesta generada correctamente | Alta |
| CHAT-02 | Streaming SSE funcional | 1. Enviar mensaje<br>2. Observar respuesta | Texto aparece token por token (streaming) | Alta |
| CHAT-03 | Citaciones mostradas | 1. Preguntar algo con documentos disponibles<br>2. Ver respuesta | Citaciones visibles con documento fuente | Alta |
| CHAT-04 | Click en citación | 1. Recibir respuesta con citaciones<br>2. Click en citación | Muestra detalle/preview del documento | Media |
| CHAT-05 | Mensaje vacío rechazado | 1. Intentar enviar mensaje vacío | Validación en cliente, no se envía | Media |
| CHAT-06 | Mensaje muy largo | 1. Escribir mensaje de 5000+ caracteres<br>2. Enviar | Aceptado o error claro de límite | Media |
| CHAT-07 | Caracteres especiales | 1. Enviar mensaje con emojis, HTML, markdown<br>2. Ver respuesta | Sin inyección, renderizado seguro | Alta |
| CHAT-08 | Múltiples mensajes seguidos | 1. Enviar mensaje<br>2. Sin esperar respuesta completa, enviar otro | Manejo correcto (queue o bloqueo) | Media |

---

## Área 3: Conversaciones (CONV)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| CONV-01 | Nueva conversación | 1. Login<br>2. Click "Nueva conversación" | Conversación creada, lista actualizada | Alta |
| CONV-02 | Listar conversaciones | 1. Login<br>2. Ver sidebar/lista de conversaciones | Muestra conversaciones del usuario actual | Alta |
| CONV-03 | Seleccionar conversación | 1. Click en conversación existente | Carga historial de mensajes | Alta |
| CONV-04 | Eliminar conversación | 1. Seleccionar conversación<br>2. Click eliminar<br>3. Confirmar | Conversación eliminada de la lista | Media |
| CONV-05 | Conversación vacía | 1. Crear nueva conversación<br>2. No enviar mensajes<br>3. Verificar lista | Manejo correcto (elimina vacías o las muestra) | Baja |

---

## Área 4: Documentos (DOC)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| DOC-01 | Listar documentos | 1. Login<br>2. Ir a sección documentos | Lista de documentos accesibles al usuario | Alta |
| DOC-02 | Upload documento válido | 1. Click upload<br>2. Seleccionar PDF válido<br>3. Confirmar | Documento subido, aparece en lista | Alta |
| DOC-03 | Upload formato inválido | 1. Intentar subir .exe o formato no soportado | Error claro, upload rechazado | Alta |
| DOC-04 | Upload archivo muy grande | 1. Intentar subir archivo > límite (ej: 50MB) | Error claro de tamaño | Media |
| DOC-05 | Documento sin permisos | 1. Como usuario A, ver documentos<br>2. Verificar que no ve documentos de usuario B | Aislamiento correcto | Alta |

---

## Área 5: Feedback (FEED)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| FEED-01 | Enviar feedback positivo | 1. Recibir respuesta<br>2. Click en thumbs up | Feedback registrado, UI actualizada | Alta |
| FEED-02 | Enviar feedback negativo | 1. Recibir respuesta<br>2. Click en thumbs down | Feedback registrado, opción de comentario | Alta |
| FEED-03 | Feedback con comentario | 1. Dar feedback negativo<br>2. Agregar comentario<br>3. Enviar | Comentario guardado | Media |
| FEED-04 | Cambiar feedback | 1. Dar thumbs up<br>2. Cambiar a thumbs down | Feedback actualizado correctamente | Baja |

---

## Área 6: Manejo de Errores (ERR)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| ERR-01 | Backend no disponible | 1. Detener backend<br>2. Intentar enviar mensaje | Error amigable "Servicio no disponible" | Alta |
| ERR-02 | Timeout en generación | 1. Enviar consulta muy compleja<br>2. Esperar timeout (si aplica) | Error claro, posibilidad de reintentar | Media |
| ERR-03 | Error de red | 1. Desconectar red durante streaming<br>2. Observar comportamiento | Manejo graceful, mensaje de error | Media |
| ERR-04 | Rate limiting | 1. Enviar 20+ mensajes rápidamente<br>2. Observar respuesta | Error 429 con mensaje claro | Media |
| ERR-05 | Input malicioso (XSS) | 1. Enviar `<script>alert('xss')</script>`<br>2. Ver respuesta | Sin ejecución de script, sanitizado | Alta |

---

## Área 7: Permisos y Aislamiento (PERM)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Prioridad |
|----|----------------|-------|-------------------|-----------|
| PERM-01 | Usuario solo ve sus conversaciones | 1. Login como Usuario A<br>2. Crear conversaciones<br>3. Login como Usuario B<br>4. Verificar lista | Usuario B no ve conversaciones de A | Alta |
| PERM-02 | Usuario solo ve sus documentos | 1. Login como Usuario A<br>2. Subir documento<br>3. Login como Usuario B<br>4. Verificar documentos | Usuario B no ve documentos de A | Alta |
| PERM-03 | RAG respeta permisos | 1. Login como agente_cat_1<br>2. Preguntar sobre RRHH | No recupera documentos de RRHH (ver xECM scenarios) | Alta |
| PERM-04 | Manager cross-department | 1. Login como manager_cross<br>2. Preguntar sobre CAT y RRHH | Recupera de ambos departamentos | Alta |
| PERM-05 | Usuario sin documentos | 1. Login como usuario sin permisos<br>2. Hacer consulta | Respuesta "No tengo documentos disponibles" | Alta |

---

## Área 8: Tests Automatizados (AUTO)

| ID | Caso de Prueba | Comando | Resultado Esperado | Prioridad |
|----|----------------|---------|-------------------|-----------|
| AUTO-01 | Tests unitarios | `pytest tests/unit -v` | Todos pasan | Alta |
| AUTO-02 | Tests integración | `pytest tests/integration -v` | Todos pasan (con DB) | Alta |
| AUTO-03 | Tests E2E | `pytest tests/e2e -v` | Todos pasan | Alta |
| AUTO-04 | Coverage >= 80% | `pytest --cov=src --cov-fail-under=80` | Coverage cumple mínimo | Alta |
| AUTO-05 | Linting ruff | `ruff check .` | 0 errores | Alta |
| AUTO-06 | Type checking mypy | `mypy src` | 0 errores | Alta |

---

## Resumen de Casos

| Área | Casos | Prioridad Alta |
|------|-------|---------------|
| AUTH | 8 | 7 |
| CHAT | 8 | 4 |
| CONV | 5 | 3 |
| DOC | 5 | 4 |
| FEED | 4 | 2 |
| ERR | 5 | 2 |
| PERM | 5 | 5 |
| AUTO | 6 | 6 |
| **Total** | **46** | **33** |

---

## Ejecución

### Orden Recomendado

1. **AUTO**: Ejecutar tests automatizados primero
2. **AUTH**: Validar que se puede acceder al sistema
3. **CHAT**: Validar funcionalidad core
4. **PERM**: Validar aislamiento crítico
5. **CONV/DOC/FEED**: Funcionalidades secundarias
6. **ERR**: Edge cases y errores

### Criterios de Aceptación

- [ ] 100% de casos de prioridad Alta ejecutados
- [ ] 0 bugs críticos abiertos
- [ ] Coverage de tests automatizados >= 80%
- [ ] Todos los escenarios xECM (PERM-03 a PERM-05) validados

---

## Referencias

- [Escenarios xECM](./xecm-test-scenarios.md) - Escenarios detallados de permisos
- [Resultados de Testing](./internal-test-results.md) - Registro de ejecución
- [Bug Report](./bug-report-sprint7.md) - Bugs encontrados
