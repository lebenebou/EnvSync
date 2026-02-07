
unzip()
{
  local zip="$1"
  local dirname="${zip%.zip}"

  if [[ -d "$dirname" ]]; then
    echo "[ERROR] directory '$dirname' already exists" >&2
    return 1
  fi

  mkdir "$dirname" && unzip.exe "$zip" -d "$dirname"

  if [[ $(ls -A "$dirname" | wc -l) -eq 1 ]] && [[ -d "$dirname/$dirname" ]]; then
    echo "[INFO] flattening '$dirname/$dirname'..." >&2
    shopt -s dotglob
    mv "$dirname/$dirname"/* "$dirname/"
    rm -r "$dirname/$dirname"
  fi

  return $?
}
