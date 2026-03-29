#!/usr/bin/env bash
# scripts/audit/run_linters.sh
# Ejecuta ruff check, ruff format y mypy.
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
REPORT="$RESULTS_DIR/linters.json"

echo "========================================"
echo "  AUDIT: Linting y Type Checking"
echo "========================================"
echo ""

# --- Ruff Check ---
echo ">> Ejecutando ruff check..."
RUFF_CHECK_EXIT=0
RUFF_CHECK_OUTPUT=$($RUN_PREFIX ruff check src/ 2>&1) || RUFF_CHECK_EXIT=$?

if [ $RUFF_CHECK_EXIT -eq 0 ]; then
    echo "   [PASS] ruff check"
    RUFF_CHECK_STATUS="PASS"
else
    echo "   [FAIL] ruff check (exit code: $RUFF_CHECK_EXIT)"
    echo "$RUFF_CHECK_OUTPUT" | tail -20
    RUFF_CHECK_STATUS="FAIL"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Ruff Format ---
echo ">> Ejecutando ruff format --check..."
RUFF_FORMAT_EXIT=0
RUFF_FORMAT_OUTPUT=$($RUN_PREFIX ruff format --check . 2>&1) || RUFF_FORMAT_EXIT=$?

if [ $RUFF_FORMAT_EXIT -eq 0 ]; then
    echo "   [PASS] ruff format"
    RUFF_FORMAT_STATUS="PASS"
else
    echo "   [FAIL] ruff format (exit code: $RUFF_FORMAT_EXIT)"
    echo "$RUFF_FORMAT_OUTPUT" | tail -20
    RUFF_FORMAT_STATUS="FAIL"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Mypy ---
echo ">> Ejecutando mypy src/..."
MYPY_EXIT=0
MYPY_OUTPUT=$($RUN_PREFIX mypy src/ 2>&1) || MYPY_EXIT=$?

if [ $MYPY_EXIT -eq 0 ]; then
    echo "   [PASS] mypy"
    MYPY_STATUS="PASS"
else
    echo "   [FAIL] mypy (exit code: $MYPY_EXIT)"
    echo "$MYPY_OUTPUT" | tail -20
    MYPY_STATUS="FAIL"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Generar JSON ---
cat > "$REPORT" <<EOF
{
  "point": 2,
  "name": "Linting y Type Checking",
  "status": "$([ $TOTAL_FAILURES -eq 0 ] && echo 'PASS' || echo 'FAIL')",
  "failures": $TOTAL_FAILURES,
  "details": {
    "ruff_check": "$RUFF_CHECK_STATUS",
    "ruff_format": "$RUFF_FORMAT_STATUS",
    "mypy": "$MYPY_STATUS"
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

exit $TOTAL_FAILURES
