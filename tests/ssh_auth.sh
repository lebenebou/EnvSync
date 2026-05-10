#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0

NUM_AGENTS=$(ps aux 2>/dev/null | grep -c 'ssh.*agent')
if [ "$NUM_AGENTS" -ne 1 ]; then
    echo -e "${YELLOW}[WARN]${NC} Expected 1 ssh-agent process, found $NUM_AGENTS"
fi

echo "[ RUN] SSH authentication to GitHub"
ssh -T git@github.com > /dev/null 2>&1
SSH_EXIT=$?
if [ $SSH_EXIT -eq 1 ]; then
    echo -e "${GREEN}[DONE]${NC} SSH authentication to GitHub"
else
    echo -e "${RED}[FAIL]${NC} SSH authentication to GitHub"
    FAILED=1
fi

exit $FAILED
