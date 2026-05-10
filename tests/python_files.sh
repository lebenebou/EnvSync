#!/bin/bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/src"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILED=0

for dir in "$REPO_ROOT/src/config" "$REPO_ROOT/src"; do
    for file in "$dir"/*.py; do
        [ -f "$file" ] || continue

        echo "[ RUN] python $file"
        if python "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}[DONE]${NC} python $file"
        else
            echo -e "${RED}[FAIL]${NC} python $file"
            FAILED=1
        fi
    done
done

exit $FAILED
