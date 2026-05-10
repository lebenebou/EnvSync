#!/bin/bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/src"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILED=0

run_test()
{
    local name="$1"
    shift
    echo "[ RUN] $name"
    if "$@" > /dev/null 2>&1; then
        echo -e "${GREEN}[DONE]${NC} $name"
    else
        echo -e "${RED}[FAIL]${NC} $name"
        FAILED=1
    fi
}

run_test "ConfigScope bitwise OR" \
    python -c "from GlobalEnv import ConfigScope; exit(0 if (ConfigScope.MUREX | ConfigScope.LAPTOP) == 3 else 1)"

run_test "GlobalEnv is singleton" \
    python -c "from GlobalEnv import GlobalEnv; exit(0 if GlobalEnv() is GlobalEnv() else 1)"

exit $FAILED
