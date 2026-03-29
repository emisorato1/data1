#!/usr/bin/env bash
# scripts/audit/run_tests.sh
# Ejecuta la suite completa de tests y verifica cobertura.
# Exit code 0 = PASS, 1 = FAIL
set -euo pipefail

# Asegurar que uv esta en PATH (instalacion tipica en ~/.local/bin o ~/.cargo/bin)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Resolver runner: uv run o .venv/bin/activate como fallback
RUN_PREFIX=""
if command -v uv &> /dev/null; then
    RUN_PREFIX="uv run"
elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "INFO: uv no encontrado, usando .venv/bin/activate como fallback"
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
    RUN_PREFIX=""
else
    echo "ERROR: No se encontro uv ni .venv/bin/activate. Instalar uv o crear venv."
    exit 1
fi

RESULTS_DIR="$PROJECT_ROOT/.audit-results"
mkdir -p "$RESULTS_DIR"

TOTAL_FAILURES=0
REPORT="$RESULTS_DIR/tests.json"

echo "========================================"
echo "  AUDIT: Suite de Tests"
echo "========================================"
echo ""

# --- Unit Tests ---
echo ">> Ejecutando tests unitarios..."
UNIT_EXIT=0
UNIT_OUTPUT=$($RUN_PREFIX pytest -m unit --tb=short -q 2>&1) || UNIT_EXIT=$?

if [ $UNIT_EXIT -eq 0 ]; then
    echo "   [PASS] Tests unitarios"
    UNIT_STATUS="PASS"
else
    echo "   [FAIL] Tests unitarios (exit code: $UNIT_EXIT)"
    UNIT_STATUS="FAIL"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Integration Tests (requiere Docker) ---
echo ">> Verificando Docker para tests de integracion..."
INTEGRATION_EXIT=0
INTEGRATION_STATUS="SKIP"
INTEGRATION_OUTPUT=""

if docker info > /dev/null 2>&1; then
    echo "   Docker disponible. Ejecutando tests de integracion..."
    INTEGRATION_OUTPUT=$($RUN_PREFIX pytest -m integration --tb=short -q 2>&1) || INTEGRATION_EXIT=$?

    if [ $INTEGRATION_EXIT -eq 0 ]; then
        echo "   [PASS] Tests de integracion"
        INTEGRATION_STATUS="PASS"
    else
        echo "   [FAIL] Tests de integracion (exit code: $INTEGRATION_EXIT)"
        INTEGRATION_STATUS="FAIL"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
else
    echo "   [SKIP] Docker no disponible. Tests de integracion omitidos."
    INTEGRATION_STATUS="SKIP"
fi
echo ""

# --- E2E Tests (requiere Docker) ---
echo ">> Ejecutando tests e2e..."
E2E_EXIT=0
E2E_STATUS="SKIP"
E2E_OUTPUT=""

if docker info > /dev/null 2>&1; then
    E2E_OUTPUT=$($RUN_PREFIX pytest -m e2e --tb=short -q 2>&1) || E2E_EXIT=$?

    if [ $E2E_EXIT -eq 0 ]; then
        echo "   [PASS] Tests e2e"
        E2E_STATUS="PASS"
    else
        echo "   [FAIL] Tests e2e (exit code: $E2E_EXIT)"
        E2E_STATUS="FAIL"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
else
    echo "   [SKIP] Docker no disponible. Tests e2e omitidos."
    E2E_STATUS="SKIP"
fi
echo ""

# --- Coverage ---
echo ">> Verificando cobertura de codigo..."
COVERAGE_EXIT=0
COVERAGE_OUTPUT=$($RUN_PREFIX pytest --cov=src --cov-report=term-missing --cov-fail-under=80 -q 2>&1) || COVERAGE_EXIT=$?

if [ $COVERAGE_EXIT -eq 0 ]; then
    echo "   [PASS] Cobertura >= 80%"
    COVERAGE_STATUS="PASS"
else
    echo "   [FAIL] Cobertura < 80% (exit code: $COVERAGE_EXIT)"
    COVERAGE_STATUS="FAIL"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Generar JSON ---
cat > "$REPORT" <<EOF
{
  "point": 1,
  "name": "Suite de Tests",
  "status": "$([ $TOTAL_FAILURES -eq 0 ] && echo 'PASS' || echo 'FAIL')",
  "failures": $TOTAL_FAILURES,
  "details": {
    "unit": "$UNIT_STATUS",
    "integration": "$INTEGRATION_STATUS",
    "e2e": "$E2E_STATUS",
    "coverage": "$COVERAGE_STATUS"
  }
}
EOF

echo "========================================"
if [ $TOTAL_FAILURES -eq 0 ]; then
    echo "  RESULTADO: PASS"
else
    echo "  RESULTADO: FAIL ($TOTAL_FAILURES sub-checks fallaron)"
fi
echo "  Reporte: $REPORT"
echo "========================================"

exit $(( TOTAL_FAILURES > 0 ? 1 : 0 ))
