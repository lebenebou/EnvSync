
#!/usr/bin/env bash

zip="$1"
dirname="${zip%.zip}"

if [[ -z "$zip" ]]; then
    echo "Usage: $0 <file.zip>" >&2
    exit 1
fi

if [[ -d "$dirname" ]]; then
    echo "[ERROR] directory '$dirname' already exists" >&2
    exit 1
fi

mkdir "$dirname" && unzip.exe "$zip" -d "$dirname"

if [[ $(ls -A "$dirname" | wc -l) -eq 1 ]] && [[ -d "$dirname/$dirname" ]]; then
    echo "[INFO] flattening '$dirname/$dirname'..." >&2
    shopt -s dotglob
    mv "$dirname/$dirname"/* "$dirname/"
    rm -r "$dirname/$dirname"
fi

exit $?