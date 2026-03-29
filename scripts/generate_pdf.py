import json

from jinja2 import Template

TRANSLATIONS = {
    "Successful Response": "Respuesta Exitosa",
    "Validation Error": "Error de Validación",
    "Login Endpoint": "Endpoint de Inicio de Sesión",
    "Logout Endpoint": "Endpoint de Cierre de Sesión",
    "Refresh Endpoint": "Endpoint de Renovación de Token",
    "Create a new conversation": "Crear una nueva conversación",
    "List conversations with cursor pagination": "Listar conversaciones",
    "Get conversation detail with messages": "Obtener detalles de conversación y mensajes",
    "Rename conversation": "Renombrar conversación",
    "Soft-delete conversation": "Eliminar conversación",
    "Send message and stream RAG response via SSE": "Enviar mensaje y recibir respuesta (SSE)",
    (
        "Authenticate user and set JWT cookies.\n\nReturns user info in the response body.\n"
        "Access token (15min) and refresh token (7d) are set as HTTPOnly cookies."
    ): (
        "Autentica al usuario y establece las cookies JWT.\n\nRetorna la información del usuario "
        "en el cuerpo de la respuesta.\nEl token de acceso (15min) y el de refresco (7 días) se "
        "configuran como cookies HTTPOnly por seguridad."
    ),
    "Invalidate refresh token and clear cookies.": ("Invalida el token de refresco y limpia las cookies de la sesión."),
    (
        "Rotate refresh token and issue new access token.\n\nThe old refresh token is revoked. "
        "If a revoked token is reused,\nall tokens for that user are revoked (theft detection)."
    ): (
        "Rota el token de refresco y emite un nuevo token de acceso.\n\nEl token de refresco "
        "anterior es revocado. Si un token revocado es reutilizado, todos los tokens de ese "
        "usuario son eliminados (detección de robo)."
    ),
    ("Create a new conversation. Returns the conversation with its thread_id (= id)."): (
        "Crea una nueva conversación. Retorna los datos de la conversación junto con su identificador (thread_id)."
    ),
    ("List active conversations for the current user, ordered by most recent activity."): (
        "Lista las conversaciones activas del usuario actual, ordenadas por actividad más reciente."
    ),
    "Get a single conversation with all its messages.": (
        "Obtiene los detalles de una conversación específica junto con todos sus mensajes."
    ),
    "Rename a conversation. Only the owner can rename.": (
        "Cambia el título de una conversación. Solo el propietario puede realizar esta acción."
    ),
    "Soft-delete a conversation. Only the owner can delete.": (
        "Aplica un borrado lógico (soft-delete) a una conversación. Solo el propietario puede eliminarla."
    ),
    (
        "Send a user message and receive the RAG response as an SSE stream.\n\n"
        "SSE events emitted:\n"
        '- ``event: token``  -- incremental content (``{"content": "..."}``)\n'
        '- ``event: done``   -- final event (``{"sources": [...], "message_id": "..."}``)\n'
        '- ``event: error``  -- error event (``{"code": "...", "message": "..."}``)'
    ): (
        "Envía un mensaje de usuario y recibe la respuesta del sistema RAG como un flujo "
        "SSE (Server-Sent Events).\n\nEventos SSE emitidos:\n"
        "- `event: token` -- contenido incremental (flujo de texto)\n"
        "- `event: done` -- evento final (incluye fuentes y ID del mensaje)\n"
        "- `event: error` -- evento de error"
    ),
    "Request body para POST /api/v1/auth/login.": "Cuerpo de la petición para iniciar sesión.",
    "Body for POST /api/v1/conversations.": "Cuerpo de la petición para crear una conversación.",
    "Body for PATCH /api/v1/conversations/{id}.": "Cuerpo de la petición para renombrar una conversación.",
    "Body for POST /api/v1/conversations/{id}/messages.": "Cuerpo de la petición para enviar un mensaje.",
    "Titulo opcional. Si se omite queda NULL hasta que el usuario lo asigne.": "Título opcional de la conversación.",
    "Nuevo titulo de la conversacion.": "Nuevo título a asignar.",
    "Pregunta del usuario para el sistema RAG.": "Texto o pregunta del usuario.",
    "Opaque cursor for next page": "Cursor para obtener la siguiente página de resultados.",
    "Items per page (max 100)": "Cantidad de elementos por página (máximo 100).",
}


def translate(text):
    if not text:
        return text
    return TRANSLATIONS.get(text, text)


with open("openapi.json") as f:
    spec = json.load(f)

info = spec.get("info", {})
title = info.get("title", "API Manual")
version = info.get("version", "1.0.0")
description = info.get("description", "Documentación oficial y referencia de integración de la API.")
paths = spec.get("paths", {})
components = spec.get("components", {}).get("schemas", {})

endpoints = []
for path, methods in paths.items():
    # EXCLUDE HEALTH ENDPOINTS
    if path in ["/health", "/health/ready"]:
        continue

    for method, details in methods.items():
        params = details.get("parameters", [])
        for p in params:
            if p.get("name") in ["access_token", "refresh_token"]:
                p["required"] = True
                if not p.get("description"):
                    p["description"] = (
                        "Token JWT de autenticación transmitido como cookie. Obligatorio por reglas de negocio para consumir este endpoint."
                    )
            elif "description" in p:
                p["description"] = translate(p["description"])

        responses = details.get("responses", {})
        needs_auth = any(p.get("name") in ["access_token", "refresh_token"] for p in params)
        if needs_auth and "401" not in responses:
            responses["401"] = {"description": "No Autorizado (Falta token o expiró)", "content": {}}

        for code, resp in responses.items():
            if "description" in resp:
                resp["description"] = translate(resp["description"])

        endpoints.append(
            {
                "path": path,
                "method": method.upper(),
                "summary": translate(details.get("summary", "")),
                "description": translate(details.get("description", "")),
                "tags": details.get("tags", []),
                "parameters": params,
                "requestBody": details.get("requestBody", {}),
                "responses": responses,
            }
        )

for name, schema in components.items():
    if "description" in schema:
        schema["description"] = translate(schema["description"])
    if "properties" in schema:
        for prop_name, prop_data in schema["properties"].items():
            if "description" in prop_data:
                prop_data["description"] = translate(prop_data["description"])

template_str = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        @page {
            size: A4;
            margin: 20mm;
            @bottom-right {
                content: "Página " counter(page);
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 10px;
                color: #666;
            }
        }
        @page cover_page {
            margin: 0;
            @bottom-right { content: none; }
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            font-size: 11px;
        }

        .cover {
            page: cover_page;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: #f8f9fa;
            text-align: center;
            padding: 2cm;
            page-break-after: always;
        }
        .cover h1 {
            font-size: 38px;
            color: #2c3e50;
            margin-bottom: 10px;
            border: none;
        }
        .cover h2 {
            font-size: 20px;
            color: #7f8c8d;
            font-weight: 300;
            border: none;
        }
        .cover .version {
            margin-top: 30px;
            font-size: 14px;
            color: #95a5a6;
            background: #ecf0f1;
            padding: 5px 15px;
            border-radius: 20px;
        }

        h1, h2, h3, h4 { color: #2c3e50; font-family: 'Helvetica Neue', Arial, sans-serif; }
        h1 { font-size: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 40px;}
        h2 { font-size: 18px; margin-top: 30px; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }
        h3 { font-size: 14px; margin-top: 20px; color: #34495e; }
        p { margin-bottom: 15px; }
        
        pre {
            background-color: #f4f6f7;
            border: 1px solid #dcdde1;
            border-left: 4px solid #3498db;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10px;
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            page-break-inside: avoid;
        }
        code {
            background-color: #f4f6f7;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10px;
            color: #c0392b;
            word-wrap: break-word !important;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            table-layout: fixed;
            word-wrap: break-word;
            page-break-inside: auto;
        }
        tr { page-break-inside: avoid; page-break-after: auto; }
        th, td {
            border: 1px solid #e0e0e0;
            padding: 8px;
            text-align: left;
            vertical-align: top;
            font-size: 10px;
        }
        th {
            background-color: #f8f9fa;
            color: #2c3e50;
            font-weight: bold;
        }
        td.col-name { width: 25%; font-weight: bold; color: #2980b9; }
        td.col-type { width: 20%; font-family: monospace; color: #8e44ad; }
        td.col-desc { width: 55%; }

        .endpoint {
            margin-bottom: 40px;
            page-break-inside: avoid;
        }
        .method-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: white;
            margin-right: 10px;
            text-transform: uppercase;
        }
        .method-GET { background-color: #3498db; }
        .method-POST { background-color: #2ecc71; }
        .method-PUT { background-color: #f39c12; }
        .method-DELETE { background-color: #e74c3c; }
        .method-PATCH { background-color: #9b59b6; }
        .path {
            font-family: monospace;
            font-size: 14px;
            color: #2c3e50;
            vertical-align: middle;
        }
        
        .section-title {
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            color: #7f8c8d;
            margin-bottom: 10px;
            margin-top: 20px;
        }
        
        .schema-box {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }

        .toc {
            page-break-after: always;
        }
        .toc h1 {
            border-bottom: none;
        }
        .toc-item {
            margin-bottom: 8px;
        }
        .toc-item a {
            text-decoration: none;
            color: #34495e;
            font-size: 12px;
        }
        .toc-item a:hover {
            color: #3498db;
        }
    </style>
</head>
<body>

    <div class="cover">
        <h1>{{ title }}</h1>
        <h2>Manual de Integración API</h2>
        <div class="version">Versión {{ version }}</div>
        <p style="margin-top:40px; max-width: 600px; color:#555; font-size:14px;">{{ description }}</p>
    </div>

    <div class="toc">
        <h1>Índice</h1>
        {% for ep in endpoints %}
            <div class="toc-item">
                <a href="#ep-{{ loop.index }}">
                    <span style="display:inline-block; width: 60px; font-family: monospace; font-size:11px;" class="method-{{ ep.method }}">{{ ep.method }}</span> 
                    {{ ep.path }} - {{ ep.summary }}
                </a>
            </div>
        {% endfor %}
        <div class="toc-item" style="margin-top: 15px; font-weight: bold;">
            <a href="#modelos">Modelos de Datos (Schemas)</a>
        </div>
    </div>

    <h1>Referencia de Endpoints</h1>
    {% for ep in endpoints %}
        <div class="endpoint" id="ep-{{ loop.index }}">
            <div style="display:flex; align-items:center; border-bottom: 1px solid #ecf0f1; padding-bottom: 10px; margin-bottom: 15px;">
                <span class="method-badge method-{{ ep.method }}">{{ ep.method }}</span>
                <span class="path">{{ ep.path }}</span>
            </div>
            
            <h3>{{ ep.summary }}</h3>
            {% if ep.description %}
                <pre style="background:transparent; border:none; padding:0; font-family: inherit; font-size: 11px; color: #555;">{{ ep.description }}</pre>
            {% endif %}

            {% if ep.parameters %}
                <div class="section-title">Parámetros</div>
                <table>
                    <thead>
                        <tr>
                            <th>Nombre (Técnico)</th>
                            <th>Ubicación</th>
                            <th>Obligatorio</th>
                            <th>Tipo</th>
                            <th>Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in ep.parameters %}
                        <tr>
                            <td class="col-name">{{ p.name }}</td>
                            <td>{{ p.in }}</td>
                            <td>
                                {% if p.get('required') %}
                                    <span style="color: #c0392b; font-weight: bold;">Sí</span>
                                {% else %}
                                    No
                                {% endif %}
                            </td>
                            <td class="col-type">
                                {% if 'schema' in p %}
                                    {% if 'type' in p['schema'] %}
                                        {{ p['schema']['type'] }}
                                    {% elif 'anyOf' in p['schema'] %}
                                        {{ p['schema']['anyOf'][0].get('type', 'any') if p['schema']['anyOf']|length > 0 else 'any' }}
                                    {% else %}
                                        string
                                    {% endif %}
                                {% else %}
                                    string
                                {% endif %}
                            </td>
                            <td class="col-desc">{{ p.get('description', '') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% endif %}

            {% if ep.requestBody %}
                <div class="section-title">Cuerpo de la Petición (Request Body)</div>
                {% if 'content' in ep.requestBody and 'application/json' in ep.requestBody['content'] %}
                    {% set schema_ref = ep.requestBody['content']['application/json'].get('schema', {}).get('$ref') %}
                    {% if schema_ref %}
                        {% set ref = schema_ref.split('/')[-1] %}
                        <p>Referencia a modelo JSON: <a href="#schema-{{ ref }}"><code>{{ ref }}</code></a></p>
                    {% endif %}
                {% endif %}
            {% endif %}

            <div class="section-title">Respuestas</div>
            <table>
                <thead>
                    <tr>
                        <th style="width:15%">Código HTTP</th>
                        <th style="width:35%">Resultado</th>
                        <th style="width:50%">Estructura de Datos</th>
                    </tr>
                </thead>
                <tbody>
                    {% for code, resp in ep.responses.items() %}
                    <tr>
                        <td><strong>{{ code }}</strong></td>
                        <td>{{ resp.get('description', '') }}</td>
                        <td>
                            {% if 'content' in resp and 'application/json' in resp['content'] %}
                                {% set schema_ref = resp['content']['application/json'].get('schema', {}).get('$ref') %}
                                {% if schema_ref %}
                                    {% set ref = schema_ref.split('/')[-1] %}
                                    <a href="#schema-{{ ref }}"><code>{{ ref }}</code></a>
                                {% else %}
                                    <i>N/A</i>
                                {% endif %}
                            {% else %}
                                <i>N/A</i>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <hr style="border:0; border-top: 1px dashed #dcdde1; margin: 30px 0;">
    {% endfor %}

    <h1 id="modelos">Modelos de Datos (Schemas)</h1>
    {% for name, schema in components.items() %}
        <div class="schema-box" id="schema-{{ name }}">
            <h3>{{ name }}</h3>
            {% if schema.get('description') %}
                <p>{{ schema['description'] }}</p>
            {% endif %}
            
            {% if 'properties' in schema %}
                <table>
                    <thead>
                        <tr>
                            <th>Propiedad (JSON)</th>
                            <th>Tipo de Dato</th>
                            <th>Requerido</th>
                            <th>Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for prop_name, prop_data in schema['properties'].items() %}
                        <tr>
                            <td class="col-name">{{ prop_name }}</td>
                            <td class="col-type">
                                {% if 'type' in prop_data %}
                                    {{ prop_data['type'] }}
                                    {% if 'items' in prop_data %}
                                        {% if 'type' in prop_data['items'] %}
                                            [{{ prop_data['items']['type'] }}]
                                        {% elif '$ref' in prop_data['items'] %}
                                            [{{ prop_data['items']['$ref'].split('/')[-1] }}]
                                        {% endif %}
                                    {% endif %}
                                {% elif 'anyOf' in prop_data %}
                                    {{ prop_data['anyOf'][0].get('type', 'any') if prop_data['anyOf']|length > 0 else 'any' }}
                                {% elif '$ref' in prop_data %}
                                    <a href="#schema-{{ prop_data['$ref'].split('/')[-1] }}">{{ prop_data['$ref'].split('/')[-1] }}</a>
                                {% else %}
                                    any
                                {% endif %}
                            </td>
                            <td>
                                {% if 'required' in schema and prop_name in schema['required'] %}
                                    Sí
                                {% else %}
                                    No
                                {% endif %}
                            </td>
                            <td class="col-desc">{{ prop_data.get('description', '') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <p><i>Este modelo no define propiedades estructuradas.</i></p>
            {% endif %}
        </div>
    {% endfor %}

</body>
</html>
"""

jinja_template = Template(template_str)
html_content = jinja_template.render(
    title=title, version=version, description=description, endpoints=endpoints, components=components
)

from weasyprint import HTML

HTML(string=html_content, base_url=".").write_pdf("API_Manual.pdf")
