# Escenarios de Prueba xECM - Sprint 6 (T6-S6-02)

Este documento detalla los escenarios de validación de permisos de acceso (ACLs) y recuperación de información basándose en la estructura jerárquica y roles del banco (OpenText Content Server / xECM).

**Objetivo:** Asegurar el aislamiento estricto de información entre departamentos críticos (CAT y RRHH) y el correcto funcionamiento del pipeline RAG respetando el principio de "Zero Trust" y "Late Binding".

## Estructura Sintética de Permisos (Seed)

| Usuario | Rol / Grupo | Descripción |
| :--- | :--- | :--- |
| `agente_cat_1` | `CAT_Users` | Acceso solo a Base de Conocimiento CAT. |
| `analista_rrhh_1` | `RRHH_Team` | Acceso solo a Políticas y Beneficios RRHH. |
| `manager_cross` | `CAT_Users`, `RRHH_Team` | Acceso a ambos departamentos (Gerente Gral). |
| `empleado_base` | `Public_All` | Acceso solo a documentos públicos transversales. |

---

## Escenarios CAT (Centro de Atención Telefónica)

### Escenario 1: Consulta de Procedimiento CAT (Usuario Autorizado)
- **Usuario:** `agente_cat_1`
- **Contexto:** El agente busca cómo bloquear una tarjeta.
- **Query:** *"¿Cuál es el procedimiento paso a paso para bloquear una tarjeta por robo?"*
- **Respuesta Esperada:** El RAG recupera `Procedimiento_Bloqueo_Tarjetas.pdf` y genera los pasos correctamente.

### Escenario 2: Intento de Acceso a RRHH desde CAT (Fuga de Información)
- **Usuario:** `agente_cat_1`
- **Contexto:** El agente intenta buscar beneficios internos de empleados.
- **Query:** *"¿Cuáles son los convenios de vacaciones para empleados este año?"*
- **Respuesta Esperada:** El RAG **NO** recupera documentos de RRHH. Responde: *"Lo siento, no tengo esa información en mis registros actuales."* (Aislamiento verificado).

### Escenario 3: Consulta de Normativa Pública (Usuario CAT)
- **Usuario:** `agente_cat_1`
- **Contexto:** El agente busca una política corporativa pública.
- **Query:** *"¿Cuál es la política general de uso de correo corporativo?"*
- **Respuesta Esperada:** El RAG recupera `Politica_Uso_Correo.pdf` (pública) y resume la política.

---

## Escenarios RRHH (Recursos Humanos)

### Escenario 4: Consulta de Convenios RRHH (Usuario Autorizado)
- **Usuario:** `analista_rrhh_1`
- **Contexto:** Analista revisa la nueva escala salarial.
- **Query:** *"¿Qué dice el convenio colectivo 2026 sobre bonos anuales?"*
- **Respuesta Esperada:** El RAG recupera `Convenio_Colectivo_2026.pdf` y lista las condiciones del bono.

### Escenario 5: Intento de Acceso a CAT desde RRHH (Fuga de Información)
- **Usuario:** `analista_rrhh_1`
- **Contexto:** Analista intenta ver cómo se procesa una hipoteca de cliente.
- **Query:** *"¿Cuáles son las tasas actuales para créditos hipotecarios de clientes premier?"*
- **Respuesta Esperada:** El RAG **NO** recupera circulares CAT. Responde: *"Lo siento, no tengo esa información..."* (Aislamiento verificado).

### Escenario 6: Consulta de Política de Beneficios Oculta a Empleados Base
- **Usuario:** `analista_rrhh_1`
- **Contexto:** Analista revisa beneficios exclusivos de gerencia.
- **Query:** *"¿Cuál es el bono de retención para directores?"*
- **Respuesta Esperada:** El RAG recupera `Beneficios_Directores_Privado.pdf` (Visible para RRHH, no para `empleado_base`).

---

## Escenarios Cross-Area y Edge Cases

### Escenario 7: Consulta Cross-Department (Manager Autorizado)
- **Usuario:** `manager_cross`
- **Contexto:** El gerente busca consolidar información de operaciones y personal.
- **Query:** *"Resume el impacto operativo de la nueva normativa CAT y cómo afecta los horarios del personal de RRHH."*
- **Respuesta Esperada:** El RAG recupera exitosamente tanto normativas de `CAT_Users` como políticas de `RRHH_Team` y genera un resumen cruzado sin errores de acceso.

### Escenario 8: Documento Compartido Específicamente (ACL por Documento)
- **Usuario:** `agente_cat_1`
- **Contexto:** Existe un documento de RRHH (ej. *Protocolo_Evacuacion_CallCenter.pdf*) que tiene un ACL explícito permitiendo a `CAT_Users` verlo, a pesar de estar en la carpeta RRHH.
- **Query:** *"¿Cuál es el protocolo de evacuación para el edificio del Call Center?"*
- **Respuesta Esperada:** El RAG recupera el documento, validando que el `PermissionResolver` respeta ACLs a nivel de nodo (DTreeACL) y no solo por herencia de carpeta.

### Escenario 9: Usuario Revocado (Cambio de Grupo Dinámico)
- **Usuario:** `agente_cat_1` (simulado post-remoción del grupo `CAT_Users`)
- **Contexto:** Se elimina a `agente_cat_1` del grupo CAT en OpenText. La vista materializada se actualiza.
- **Query:** *"¿Cómo anulo una transferencia?"*
- **Respuesta Esperada:** El RAG **NO** recupera documentos. El Late Binding bloquea el acceso en tiempo real de consulta vectorial (Hybrid Search + ACL filter).

### Escenario 10: Denegación Explícita (Negative ACLs)
- **Usuario:** `analista_rrhh_1`
- **Contexto:** Un documento público tiene una regla explícita denegando el acceso a `RRHH_Team` (caso hipotético/forense).
- **Query:** *"Detalles de la auditoría sorpresa RRHH."*
- **Respuesta Esperada:** El RAG bloquea la recuperación validando que los permisos negativos (si aplica el modelo de OpenText) o la falta de permiso explícito impiden el acceso.
