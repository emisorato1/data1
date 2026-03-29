#!/usr/bin/env bash
# scripts/audit/run_full_audit.sh
# Orquestador: ejecuta los 3 scripts de auditoria (tests, linters, security) y consolida resultados.
# Puntos: 1 (Tests), 2 (Linting), 3 (Seguridad automatizada).
# El punto 3 tiene ademas una parte manual (cifrado, RBAC) que el agente evalua aparte.
# Exit code 0 = todos PASS, 1 = al menos 1 FAIL
set -uo pipefail

# Asegurar que uv esta en PATH (instalacion tipica en ~/.local/bin o ~/.cargo/bin)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Verificar entorno: uv o .venv (los sub-scripts resuelven su propio runner)
if ! command -v uv &> /dev/null && [ ! -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "ERROR: No se encontro uv ni .venv/bin/activate. Instalar uv o crear venv."
    exit 1
fi

RESULTS_DIR="$PROJECT_ROOT/.audit-results"
rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

TOTAL_FAILURES=0
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "╔════════════════════════════════════════╗"
echo "║  AUDITORIA COMPLETA DE SPRINT          ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                  ║"
echo "╚════════════════════════════════════════╝"
echo ""

# --- Punto 1: Suite de Tests ---
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PUNTO 1: Suite de Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TESTS_EXIT=0
bash "$SCRIPT_DIR/run_tests.sh" || TESTS_EXIT=$?
if [ $TESTS_EXIT -ne 0 ]; then
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Punto 2: Linting y Type Checking ---
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PUNTO 2: Linting y Type Checking"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LINTERS_EXIT=0
bash "$SCRIPT_DIR/run_linters.sh" || LINTERS_EXIT=$?
if [ $LINTERS_EXIT -ne 0 ]; then
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Punto 3: Seguridad y Cumplimiento (parte automatizada) ---
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PUNTO 3: Seguridad y Cumplimiento (automatizado)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SECURITY_EXIT=0
bash "$SCRIPT_DIR/run_security_scan.sh" || SECURITY_EXIT=$?
if [ $SECURITY_EXIT -ne 0 ]; then
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi
echo ""

# --- Leer resultados individuales ---
TESTS_STATUS="UNKNOWN"
LINTERS_STATUS="UNKNOWN"
SECURITY_STATUS="UNKNOWN"

if [ -f "$RESULTS_DIR/tests.json" ]; then
    TESTS_STATUS=$(python3 -c "import json; print(json.load(open('$RESULTS_DIR/tests.json'))['status'])" 2>/dev/null || echo "UNKNOWN")
fi
if [ -f "$RESULTS_DIR/linters.json" ]; then
    LINTERS_STATUS=$(python3 -c "import json; print(json.load(open('$RESULTS_DIR/linters.json'))['status'])" 2>/dev/null || echo "UNKNOWN")
fi
if [ -f "$RESULTS_DIR/security.json" ]; then
    SECURITY_STATUS=$(python3 -c "import json; print(json.load(open('$RESULTS_DIR/security.json'))['status'])" 2>/dev/null || echo "UNKNOWN")
fi

# --- Generar reporte consolidado ---
OVERALL_STATUS="PASS"
if [ $TOTAL_FAILURES -gt 0 ]; then
    OVERALL_STATUS="FAIL"
fi

cat > "$RESULTS_DIR/full-audit.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "overall_status": "$OVERALL_STATUS",
  "total_automated_failures": $TOTAL_FAILURES,
  "points": {
    "1_tests": "$TESTS_STATUS",
    "2_linters": "$LINTERS_STATUS",
    "3_security_automated": "$SECURITY_STATUS"
  },
  "note": "El punto 3 tiene una parte automatizada (este reporte) y una parte manual (cifrado, RBAC) que requiere revision por el agente."
}
EOF

# --- Resumen final ---
echo "╔════════════════════════════════════════╗"
echo "║  RESUMEN DE AUDITORIA AUTOMATIZADA     ║"
echo "╠════════════════════════════════════════╣"
echo "║                                        ║"
printf "║  Punto 1 (Tests):        %-13s ║\n" "$TESTS_STATUS"
printf "║  Punto 2 (Linters):      %-13s ║\n" "$LINTERS_STATUS"
printf "║  Punto 3 (Seguridad):    %-13s ║\n" "$SECURITY_STATUS"
echo "║                                        ║"
echo "╠════════════════════════════════════════╣"

if [ $TOTAL_FAILURES -eq 0 ]; then
    printf "║  RESULTADO: PASS (3/3 automatizados)   ║\n"
else
    printf "║  RESULTADO: FAIL (%d/3 fallaron)         ║\n" "$TOTAL_FAILURES"
fi

echo "║                                        ║"
echo "║  Nota: Punto 3 tiene ademas revision   ║"
echo "║  manual (cifrado, RBAC) por el agente.  ║"
echo "║                                        ║"
echo "╠════════════════════════════════════════╣"
echo "║  Reportes en: .audit-results/           ║"
echo "╚════════════════════════════════════════╝"

if [ $TOTAL_FAILURES -gt 0 ]; then
    exit 1
else
    exit 0
fi
