
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for file in "$SCRIPT_DIR"/*.py; do

    echo ""
    echo "[ RUN] python $file"

    python "$file" 1> /dev/null 2>stderr.output
    if [ $? -ne 0 ]; then

        cat stderr.output >&2
        echo -e "\033[91m[FAIL] python $file\033[0m"
        rm stderr.output
        exit 1

    fi

    rm stderr.output
    echo -e "\033[92m[ OK ] python $file\033[0m"

done