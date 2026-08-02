#!/bin/bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/src"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILED=0

BASH_PROFILE_PY="$REPO_ROOT/src/config/BashProfile.py"

echo "[ RUN] BashProfile.py generates correct bash syntax"
if py "$BASH_PROFILE_PY" | bash -n; then
    echo -e "${GREEN}[DONE]${NC} BashProfile.py generates correct bash syntax"
else
    echo -e "${RED}[FAIL]${NC} BashProfile.py generates correct bash syntax"
    FAILED=1
fi

HOME_BASH_PROFILE=$(py -c "from GlobalEnv import GlobalEnv; print(GlobalEnv().getBashProfilePath())")

echo "[ RUN] Home .bash_profile has correct bash syntax"
if bash -n "$HOME_BASH_PROFILE"; then
    echo -e "${GREEN}[DONE]${NC} Home .bash_profile has correct bash syntax"
else
    echo -e "${RED}[FAIL]${NC} Home .bash_profile has correct bash syntax"
    FAILED=1
fi

exit $FAILED
