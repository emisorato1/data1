#!/usr/bin/env bash
# scripts/audit/run_security_scan.sh
# Escaneo de seguridad: secretos, CVEs, archivos .env.
# Exit code 0 = PASS, 1+ = FAIL
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
REPORT="$RESULTS_DIR/security.json"

echo "========================================"
echo "  AUDIT: Escaneo de Seguridad"
echo "========================================"
echo ""

# --- Secretos Hardcodeados ---
echo ">> Buscando secretos hardcodeados..."
SECRETS_EXIT=0
SECRETS_STATUS="PASS"
SECRETS_FINDINGS=""

# Patrones de secretos comunes (excluyendo .env.example, tests, fixtures, .git)
SECRETS_OUTPUT=$(grep -rn \
    --include="*.py" --include="*.yml" --include="*.yaml" --include="*.toml" --include="*.json" --include="*.sh" \
    -E '(password|passwd|secret|api_key|apikey|token|private_key)\s*=\s*["\x27][^"\x27]{8,}' \
    --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=__pycache__ \
    --exclude-dir=.audit-results --exclude-dir=.opencode --exclude-dir=.agent --exclude-dir=.agents \
    --exclude="*.example" --exclude="conftest.py" --exclude="test_*.py" \
    "$PROJECT_ROOT/src/" "$PROJECT_ROOT/docker/" "$PROJECT_ROOT/scripts/" "$PROJECT_ROOT/dags/" 2>/dev/null || true)

if [ -n "$SECRETS_OUTPUT" ]; then
    # Filtrar falsos positivos comunes (settings.py con env vars, type hints, bash variables, etc.)
    REAL_SECRETS=$(echo "$SECRETS_OUTPUT" | grep -v 'os.environ\|os.getenv\|env(\|Settings\|Field(\|BaseSettings\|SecretStr\|# noqa\|\$[A-Z_]' || true)
    if [ -n "$REAL_SECRETS" ]; then
        echo "   [FAIL] Posibles secretos encontrados:"
        echo "$REAL_SECRETS" | head -10
        SECRETS_STATUS="FAIL"
        SECRETS_FINDINGS="$REAL_SECRETS"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    else
        echo "   [PASS] Sin secretos hardcodeados (falsos positivos filtrados)"
    fi
else
    echo "   [PASS] Sin secretos hardcodeados"
fi
echo ""

# --- Archivos .env committeados ---
echo ">> Verificando archivos .env en git..."
ENV_STATUS="PASS"
ENV_FILES=$(git ls-files '*.env' '.env*' 2>/dev/null | grep -v '.env.example' | grep -v '.env.test' || true)

if [ -n "$ENV_FILES" ]; then
    echo "   [FAIL] Archivos .env en git:"
    echo "$ENV_FILES"
    ENV_STATUS="FAIL"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
else
    echo "   [PASS] Sin archivos .env committeados (salvo .env.example)"
fi
echo ""

# --- CVEs en dependencias (pip-audit) ---
echo ">> Buscando CVEs en dependencias..."
CVE_EXIT=0
CVE_STATUS="SKIP"
CVE_OUTPUT=""

if $RUN_PREFIX pip-audit --version > /dev/null 2>&1; then
    CVE_OUTPUT=$($RUN_PREFIX pip-audit 2>&1) || CVE_EXIT=$?
    if [ $CVE_EXIT -eq 0 ]; then
        echo "   [PASS] Sin CVEs conocidos"
        CVE_STATUS="PASS"
    else
        echo "   [FAIL] CVEs encontrados:"
        echo "$CVE_OUTPUT" | tail -20
        CVE_STATUS="FAIL"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
else
    echo "   [SKIP] pip-audit no disponible. Instalar con: pip install pip-audit"
    CVE_STATUS="SKIP"
fi
echo ""

# --- detect-secrets ---
echo ">> Buscando secretos con detect-secrets..."
DETECT_SECRETS_STATUS="SKIP"

if command -v detect-secrets > /dev/null 2>&1 || $RUN_PREFIX detect-secrets --version > /dev/null 2>&1; then
    DS_OUTPUT=$(detect-secrets scan --exclude-files '\.env\.example$|\.lock$|node_modules|\.git|__pycache__|\.audit-results' 2>&1 || $RUN_PREFIX detect-secrets scan --exclude-files '\.env\.example$|\.lock$|node_modules|\.git|__pycache__|\.audit-results' 2>&1) || true
    DS_RESULTS=$(echo "$DS_OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('results',{})))" 2>/dev/null || echo "0")
    if [ "$DS_RESULTS" = "0" ]; then
        echo "   [PASS] detect-secrets: sin hallazgos"
        DETECT_SECRETS_STATUS="PASS"
    else
        echo "   [FAIL] detect-secrets: $DS_RESULTS archivos con posibles secretos"
        DETECT_SECRETS_STATUS="FAIL"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
else
    echo "   [SKIP] detect-secrets no disponible. Instalar con: pip install detect-secrets"
    DETECT_SECRETS_STATUS="SKIP"
fi
echo ""

# --- Generar JSON ---
cat > "$REPORT" <<EOF
{
  "point": 3,
  "name": "Seguridad y Cumplimiento (automatizado)",
  "status": "$([ $TOTAL_FAILURES -eq 0 ] && echo 'PASS' || echo 'FAIL')",
  "failures": $TOTAL_FAILURES,
  "details": {
    "hardcoded_secrets": "$SECRETS_STATUS",
    "env_files": "$ENV_STATUS",
    "cve_scan": "$CVE_STATUS",
    "detect_secrets": "$DETECT_SECRETS_STATUS"
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
