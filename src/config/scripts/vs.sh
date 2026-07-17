
#!/usr/bin/env bash

file="$1"

if [[ -z "$file" ]]; then
    file="$(paste)"
fi

if [[ ! -f "$file" ]]; then
    echo "[ERROR] File not found: $file" >&2
    exit 1
fi

vsExe="/c/Program Files/Microsoft Visual Studio/18/Professional/Common7/IDE/devenv.exe"

if [[ ! -f "$vsExe" ]]; then
    echo "[ERROR] VS devenv not found: $vsExe" >&2
    exit 1
fi

win 3
"$vsExe" //edit "$file"