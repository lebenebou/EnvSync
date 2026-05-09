#!/bin/bash

# EnvSync Repository Initialization Script
# This script orchestrates the initialization of the EnvSync repository
# It decrypts encrypted files, updates bash profile, and syncs vim configuration
# 
# Usage: ./init.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_ROOT/src"
CONFIG_DIR="$SRC_DIR/config"

VERBOSE=false
SOFT=false
FAIL_FAST=false
for arg in "$@"; do
    case "$arg" in
        --verbose) VERBOSE=true ;;
        --fail-fast) FAIL_FAST=true ;;
        --soft)    SOFT=true ;;
    esac
done

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_success()
{
    echo -e "${GREEN}[DONE]${NC} $1"
}

log_warn()
{
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error()
{
    echo -e "${RED}[ ERR]${NC} $1"
}

ensure_jq()
{
    local JQ_URL="https://github.com/jqlang/jq/releases/latest/download/jq-win64.exe"
    local JQ_EXE="$REPO_ROOT/bin/jq.exe"

    if [ -f "$JQ_EXE" ]; then
        $VERBOSE && log_success "jq installed"
        return 0
    fi

    log_warn "jq not found, installing..."
    if ! curl -L "$JQ_URL" -o "$JQ_EXE" -s 2>/dev/null; then
        log_error "jq installation encountered an issue"
        return 1
    fi

    log_success "jq installed"
    return 0
}

ensure_fd()
{
    local FD_URL="https://github.com/sharkdp/fd/releases/download/v10.3.0/fd-v10.3.0-i686-pc-windows-msvc.zip"
    local FD_ZIP="$REPO_ROOT/bin/fd.zip"
    local FD_DIR="$REPO_ROOT/bin/fd"
    local FD_EXE="$FD_DIR/fd.exe"

    if [ -f "$FD_EXE" ]; then
        $VERBOSE && log_success "fd installed"
        return 0
    fi

    log_warn "fd not found, installing..."
    rm -rf "$FD_DIR" "$FD_ZIP" 2>/dev/null
    if ! curl -Ls "$FD_URL" -o "$FD_ZIP" 2>/dev/null; then
        log_error "fd installation encountered an issue"
        return 1
    fi

    if ! unzip.exe "$FD_ZIP" -d "$REPO_ROOT/bin" &>/dev/null; then
        log_error "extraction of $FD_ZIP encountered an issue"
        return 1
    fi

    if ! mv "$REPO_ROOT/bin/fd-v10.3.0-i686-pc-windows-msvc" "$FD_DIR" 2>/dev/null; then
        log_error "fd installation encountered an issue"
        return 1
    fi

    rm -f "$FD_ZIP" 2>/dev/null
    log_success "fd installed"
    return 0
}

ensure_bat()
{
    local BAT_URL="https://github.com/sharkdp/bat/releases/download/v0.26.1/bat-v0.26.1-x86_64-pc-windows-msvc.zip"
    local BAT_ZIP="$REPO_ROOT/bin/bat.zip"
    local BAT_DIR="$REPO_ROOT/bin/bat"
    local BAT_EXE="$BAT_DIR/bat.exe"

    if [ -f "$BAT_EXE" ]; then
        $VERBOSE && log_success "bat installed"
        return 0
    fi

    log_warn "bat not found, installing..."
    rm -rf "$BAT_DIR" "$BAT_ZIP" 2>/dev/null

    if ! curl -L "$BAT_URL" -o "$BAT_ZIP" -s 2>/dev/null; then
        log_error "bat installation encountered an issue"
        return 1
    fi

    if ! unzip.exe "$BAT_ZIP" -d "$REPO_ROOT/bin" &>/dev/null; then
        log_error "extraction of $BAT_ZIP encountered an issue"
        return 1
    fi

    if ! mv "$REPO_ROOT/bin/bat-v0.26.1-x86_64-pc-windows-msvc" "$BAT_DIR" 2>/dev/null; then
        log_error "bat installation encountered an issue"
        return 1
    fi

    rm -f "$BAT_ZIP" 2>/dev/null

    log_success "bat installed"
    return 0
}

ensure_python()
{
    if ! command -v python &> /dev/null; then
        log_error "Python is not installed or not in PATH. Please install Python to continue."
        return 1
    fi

    pversion=$(python -V 2>&1 | awk '{print $2}')
    log_success "Python version: $pversion"

    return 0
}

step_decrypt()
{
    echo ""
    echo -ne "Checking decryption...\r"

    out="/dev/null"
    if $VERBOSE; then
        out="/dev/stdout"
    fi

    python "$SRC_DIR/GlobalEnv.py" --decrypt >"$out" 2>&1

    local EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        log_error "Decryption check failed with exit code: $EXIT_CODE"
        return $EXIT_CODE
    fi

    log_success "Decryption check passed"
    return 0
}

step_update_bash_profile()
{
    out="/dev/null"
    if $VERBOSE; then
        out="/dev/stdout"
    fi

    python "$CONFIG_DIR/BashProfile.py" --in_place >"$out" 2>&1

    local EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        log_error "Bash profile update failed with exit code: $EXIT_CODE"
        return $EXIT_CODE
    fi

    log_success "Bash profile updated successfully"
    return 0
}

step_update_vimrc()
{
    out="/dev/null"
    if $VERBOSE; then
        out="/dev/stdout"
    fi

    python "$CONFIG_DIR/VimRC.py" --in_place >"$out" 2>&1

    local EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        log_error "Vim configuration update failed with exit code: $EXIT_CODE"
        return $EXIT_CODE
    fi
    log_success "Vim configuration updated successfully"
    return 0
}

step_sync_vim_plugins()
{
    echo ""

    $VERBOSE && echo "Checking vim installation..."
    if ! command -v vim &> /dev/null; then
        log_warn "vim not found in PATH, skipping plugin sync"
        return 0
    fi

    local VIM_PLUG="$HOME/.vim/autoload/plug.vim"
    local VIM_PLUG_URL="https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
    if [ ! -f "$VIM_PLUG" ]; then
        $VERBOSE && log_warn "vim-plug not found, installing..."
        if ! curl -fLo "$VIM_PLUG" --create-dirs "$VIM_PLUG_URL" 2>/dev/null; then
            log_error "vim-plug installation encountered an issue"
            return 1
        fi
        $VERBOSE && log_success "vim-plug installed"
    fi

    $VERBOSE && echo "Syncing vim plugins..."
    if vim +PlugInstall +qall 2>/dev/null; then
        log_success "Vim plugins installed"
    else
        log_warn "Vim plugin installation encountered an issue"
    fi

    $VERBOSE && echo "Cleaning vim plugins..."
    if vim +PlugClean +qall 2>/dev/null; then
        log_success "Vim plugins cleaned"
    else
        log_warn "Vim plugin cleanup encountered an issue"
    fi

    return 0
}

verify_repo_root()
{
    if [ ! -d "$REPO_ROOT/.git" ]; then
        log_error "Not in EnvSync repository root. .git folder not found."
        echo "Expected: $REPO_ROOT/.git"
        return 1
    fi

    # Check if main branch is ahead of the current commit
    cd "$REPO_ROOT"
    echo -ne "git fetch --all...\r"
    git fetch --all &> /dev/null
    if [ $? -ne 0 ]; then
        log_warn "Failed to fetch remote repository. Skipping update check."
        return 0
    fi

    echo -ne "Checking EnvSync status...\r"
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null)
    BASE=$(git merge-base @ @{u} 2>/dev/null)

    if [ -z "$REMOTE" ]; then
        log_warn "No upstream branch found. Skipping update check."

    elif [ $LOCAL = $REMOTE ]; then
        log_success "Repository is up to date with remote."

    elif [ $LOCAL = $BASE ]; then
        log_warn "Your local repository is behind the remote. Consider pulling the latest changes."

    elif [ $REMOTE = $BASE ]; then
        log_warn "Your local repository is ahead of the remote. Consider pushing your changes."

    else
        log_warn "Your local repository has diverged from the remote. Please resolve the divergence."
    fi

    return 0
}

main()
{
    clear

    echo -e \\nWelcome $(whoami)!\\n

    ensure_python "$@" || exit $?
    verify_repo_root || exit $?

    echo ""
    step_update_bash_profile || { $FAIL_FAST && exit 1; }
    step_update_vimrc || { $FAIL_FAST && exit 1; }


    step_decrypt || { $FAIL_FAST && exit 1; }

    if ! $SOFT; then
        # steps inside this block may take time

        step_sync_vim_plugins || { $FAIL_FAST && exit 1; }
    fi

    echo ""
    mkdir -p "$REPO_ROOT/bin"

    out="/dev/null"
    if $VERBOSE; then
        out="/dev/stdout"
    fi

    ensure_jq  || { $FAIL_FAST && exit 1; }
    ensure_fd  || { $FAIL_FAST && exit 1; }
    ensure_bat || { $FAIL_FAST && exit 1; }
    if [ $? -eq 0 ]; then
        log_success "Bin utilities check"
    fi

    echo ""
    log_success "EnvSync Ready!"
    return 0
}

main "$@"
exit $?