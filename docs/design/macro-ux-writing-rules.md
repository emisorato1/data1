# Banco Macro - Reglas de UX Writing

> Directrices de redacción y tono de voz para la interfaz del sistema RAG enterprise.
> Fuente: Content Design System (croMa) y Brandbook institucional.

---

## Principio Rector

> **"Lo que no suma, resta."**

Cada palabra en la interfaz debe justificar su presencia. Si no aporta claridad o contexto, se elimina.

---

## 1. Economía de Palabras

### Reglas

- Eliminar tecnicismos bancarios innecesarios
- Priorizar lenguaje cotidiano
- Ir directo al punto

### Ejemplos

| Mal | Bien |
|-----|------|
| "Proceda a enrolar su DNI para validar su identidad" | "Valida tu DNI" |
| "El sistema procesara su solicitud en las proximas 48hs habiles" | "Tu solicitud estara lista en 48hs habiles" |
| "Ingrese sus credenciales de acceso al sistema" | "Ingresa tu usuario y contrasena" |

---

## 2. Inclusividad

### Reglas

- Usar sustantivos epicenos (que no marcan genero)
- Usar terminos inclusivos o pronombres como "quien"
- Evitar sesgos de genero

### Ejemplos

| Mal | Bien |
|-----|------|
| "El usuario debera..." | "Quien use el sistema debera..." |
| "Los empleados del banco" | "El personal del banco" |
| "Estimado cliente" | "Hola" / "Te damos la bienvenida" |

### Formas Verbales

- Usar voseo argentino: "consulta" -> "**consulta**" o "**ingresa**"
- Combinar imperativo con primera persona del plural: "Pensamos en grande"

---

## 3. Estilo de Redaccion

### Productos y Servicios

- Productos genericos en **minuscula**: "tarjeta de credito", "cuenta corriente", "plazo fijo"
- Productos propios con nombre de marca en **mayuscula**: "Macro Selecta", "Plan Sueldo"

### Abreviaturas

**Prohibidas.** Siempre escribir el nombre completo.

| Mal | Bien |
|-----|------|
| TC | tarjeta de credito |
| CC | cuenta corriente |
| CBU | CBU (es una sigla oficial, se acepta) |

**Excepcion**: Siglas oficiales del sistema financiero (CBU, CVU, CUIT) se pueden usar por ser ampliamente reconocidas.

### Imperativos

Usar de forma **moderada**, combinandolos con:
- Preguntas: "Ya conoces nuestras promociones?"
- Primera persona del plural: "Pensamos en grande?"
- Invitaciones: "Te invitamos a explorar..."

---

## 4. Tono de Voz

### Caracteristicas

| Atributo | Descripcion |
|----------|-------------|
| **Integrador** | Incluye a todos, sin distinciones |
| **Simple** | Facil de entender, sin jerga |
| **Pragmatico** | Va al punto, resuelve |
| **Confiable** | Transmite seguridad sin ser frio |

### Lo que SI hacer

- Hablar en segunda persona informal (vos/tu)
- Ser directo pero amigable
- Usar verbos de accion
- Confirmar acciones con mensajes claros

### Lo que NO hacer

- Usar jerga tecnica sin explicacion
- Ser condescendiente
- Usar humor inapropiado para un banco
- Generar incertidumbre ("su solicitud podria o no ser procesada")

---

## 5. Patrones de UI

### Botones

| Tipo | Ejemplo |
|------|---------|
| Accion principal | "Ingresar", "Enviar", "Confirmar" |
| Accion secundaria | "Cancelar", "Volver" |
| Accion destructiva | "Eliminar conversacion" (con confirmacion) |

### Placeholders

| Mal | Bien |
|-----|------|
| "Ingrese su email" | "nombre@macro.com.ar" |
| "Escriba aqui" | "Hace tu consulta..." |

### Mensajes de Error

| Mal | Bien |
|-----|------|
| "Error 401: Unauthorized" | "Credenciales invalidas" |
| "Network error" | "Error de conexion con el servidor" |
| "Validation failed" | "Revisa los datos ingresados" |

### Estados Vacios

| Mal | Bien |
|-----|------|
| "No hay datos" | "Pensamos en grande?" (invitacion a interactuar) |
| "Lista vacia" | "Empeza una nueva conversacion" |

### Streaming / Carga

| Mal | Bien |
|-----|------|
| "Loading..." | "Analizando documentos..." |
| "Processing" | "Buscando en la base documental..." |

---

## 6. Checklist de UX Writing

Para cada texto nuevo en la interfaz, verificar:

- [ ] Es necesario? (lo que no suma, resta)
- [ ] Usa lenguaje cotidiano? (no tecnicismos)
- [ ] Es inclusivo? (sin sesgos de genero)
- [ ] Productos en minuscula? (salvo nombres propios)
- [ ] Sin abreviaturas? (excepto siglas oficiales)
- [ ] Tono integrador, simple, pragmatico, confiable?
- [ ] Tildes correctas en espanol?
