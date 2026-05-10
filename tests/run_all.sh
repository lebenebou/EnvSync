
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for file in "$SCRIPT_DIR"/*.sh; do

    # skip this script itself
    [ "$file" = "$SCRIPT_DIR/run_all.sh" ] && continue

    echo ""
    echo "[ RUN] bash $file"

    if bash "$file" >stdout.output 2>stderr.output; then

        rm -f stdout.output stderr.output
        echo -e "\033[92m[DONE] bash $file\033[0m"

    else

        cat stdout.output
        cat stderr.output >&2
        echo -e "\033[91m[FAIL] bash $file\033[0m"
        rm -f stdout.output stderr.output
        exit 1

    fi

done