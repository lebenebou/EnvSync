
#!/bin/bash

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CURRENT_DIR/.." && pwd)"

# build a single import statement from requirements.txt
packagesStr=$(cat "$REPO_ROOT/requirements.txt" | tr '\n\r' ' ' | sed 's/\s\+/; import /g' | sed 's/; import\s*$//')

# run python import + packagesStr
OUTPUT=$(python -c "import $packagesStr" 2>&1)
if [ $? -eq 0 ]; then
    echo -e "\033[92m[DONE] python import requirements.txt\033[0m"
else
    echo -e "\033[91m[FAIL] \033[0m $OUTPUT"
    exit 1
fi