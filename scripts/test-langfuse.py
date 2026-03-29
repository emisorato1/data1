"""Script de verificacion: envia un trace a Langfuse y confirma que se registro.

Uso:
    python scripts/test-langfuse.py

Requiere las variables de entorno:
    LANGFUSE_HOST         URL de Langfuse (ej: http://localhost:3000)
    LANGFUSE_PUBLIC_KEY   Public key del proyecto
    LANGFUSE_SECRET_KEY   Secret key del proyecto

Resultado esperado:
    - Crea un trace de prueba con un span y una generacion
    - Verifica via API que el trace existe
    - Imprime OK si todo funciona
"""

from __future__ import annotations

import os
import sys
import time
from datetime import UTC, datetime

import httpx
from langfuse import Langfuse


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"ERROR: variable de entorno '{name}' no configurada.")
        sys.exit(1)
    return value


def _create_test_trace(client: Langfuse) -> str:
    """Crea un trace de prueba con span + generation y retorna el trace_id."""
    trace = client.trace(
        name="test-langfuse-connectivity",
        user_id="test-script",
        metadata={
            "source": "scripts/test-langfuse.py",
            "timestamp": datetime.now(tz=UTC).isoformat(),
        },
    )

    # Span simulando retrieval
    span = trace.span(
        name="test-retrieval",
        input={"query": "Prueba de conectividad Langfuse"},
        output={"documents": 3},
        metadata={"latency_ms": 42.0},
    )
    span.end()

    # Generation simulando llamada a LLM
    trace.generation(
        name="test-generation",
        model="gemini-2.0-flash",
        input="Pregunta de prueba",
        output="Respuesta de prueba desde el script de verificacion",
        usage={
            "input": 10,
            "output": 25,
            "total": 35,
        },
        metadata={"cost_usd": 0.0001},
    )

    # Flush para asegurar que se envio
    client.flush()

    return trace.id


def _verify_trace(host: str, public_key: str, secret_key: str, trace_id: str) -> bool:
    """Verifica que el trace exista en Langfuse via API REST."""
    url = f"{host.rstrip('/')}/api/public/traces/{trace_id}"

    # Reintentar hasta 5 veces con backoff (Langfuse procesa async)
    for attempt in range(1, 6):
        time.sleep(2 * attempt)
        try:
            response = httpx.get(
                url,
                auth=(public_key, secret_key),
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == trace_id:
                    return True
                print(f"  Intento {attempt}/5: trace encontrado pero ID no coincide")
            else:
                print(f"  Intento {attempt}/5: HTTP {response.status_code}")
        except httpx.RequestError as exc:
            print(f"  Intento {attempt}/5: error de conexion - {exc}")

    return False


def main() -> None:
    host = _require_env("LANGFUSE_HOST")
    public_key = _require_env("LANGFUSE_PUBLIC_KEY")
    secret_key = _require_env("LANGFUSE_SECRET_KEY")

    print(f"Langfuse host: {host}")
    print(f"Public key:    {public_key[:12]}...")
    print()

    # Paso 1: Verificar conectividad basica
    print("[1/3] Verificando conectividad con Langfuse...")
    try:
        health_url = f"{host.rstrip('/')}/api/public/health"
        resp = httpx.get(health_url, timeout=10.0)
        if resp.status_code == 200:
            print("  OK - Langfuse responde en /api/public/health")
        else:
            print(f"  WARN - Health check retorno HTTP {resp.status_code}")
    except httpx.RequestError as exc:
        print(f"  ERROR - No se pudo conectar a Langfuse: {exc}")
        print("  Verificar que el port-forward este activo:")
        print("    kubectl port-forward svc/langfuse-web 3000:3000 -n langfuse")
        sys.exit(1)

    # Paso 2: Enviar trace de prueba
    print("[2/3] Enviando trace de prueba...")
    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )
    trace_id = _create_test_trace(client)
    print(f"  Trace creado: {trace_id}")

    # Paso 3: Verificar que el trace aparezca
    print("[3/3] Verificando trace en Langfuse (puede tardar unos segundos)...")
    if _verify_trace(host, public_key, secret_key, trace_id):
        print("  OK - Trace verificado exitosamente")
        print()
        print("=" * 60)
        print("RESULTADO: Langfuse funciona correctamente")
        print(f"Ver trace en: {host}/trace/{trace_id}")
        print("=" * 60)
    else:
        print("  ERROR - No se pudo verificar el trace en Langfuse")
        print("  El trace se envio pero no se encontro via API.")
        print("  Verificar manualmente en la UI de Langfuse.")
        sys.exit(1)

    client.shutdown()


if __name__ == "__main__":
    main()
