#!/bin/bash

# EnvSync Repository Initialization Script
# This script orchestrates the initialization of the EnvSync repository
# It decrypts encrypted files, updates bash profile, and syncs vim configuration
# 
# Usage: ./init.sh [--verbose] [--fail-fast] [--soft] [--full]

_esync_pre_vars=$(compgen -v)
_esync_pre_fns=$(declare -F | awk '{print $3}')

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$REPO_ROOT/init.sh" ] || REPO_ROOT="/c/EnvSync"
[ -f "$REPO_ROOT/init.sh" ] || REPO_ROOT="$HOME/EnvSync"
cd "$REPO_ROOT" || { echo "Failed to change directory to repository root: $REPO_ROOT"; exit 1; }

SRC_DIR="$REPO_ROOT/src"
CONFIG_DIR="$SRC_DIR/config"

VERBOSE=false
SOFT=false
FULL=false
FAIL_FAST=false

print_help()
{
    cat <<EOF
EnvSync Repository Initialization Script

Usage:
    ./init.sh [OPTIONS]

Options:
    -h, --help      Show this help message and exit
    --verbose       Enable verbose output
    --fail-fast     Stop immediately when a step fails
    --soft          Perform validation and authentication only.
                    Skip bash/vim configuration updates.
    --full          Run the complete setup:
                      - update configurations
                      - sync vim plugins
                      - install bin utilities
                      - run repository tests

Examples:
    ./init.sh
        Standard initialization

    ./init.sh --verbose
        Standard initialization with additional logging

    ./init.sh --soft
        Validate repository, SSH, Git, and Python only

    ./init.sh --full --verbose
        Run the complete setup with verbose logging

Notes:
    --full overrides --soft.
EOF
}

for arg in "$@"; do
    case "$arg" in
        -h|--help)
            print_help
            exit 0
            ;;
        --verbose)
            VERBOSE=true
            ;;
        --fail-fast)
            FAIL_FAST=true
            ;;
        --soft)
            SOFT=true
            ;;
        --full)
            FULL=true
            SOFT=false
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Run './init.sh --help' for usage information."
            exit 1
            ;;
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
    echo ""

    if ! command -v python &> /dev/null; then
        log_error "Python is not installed or not in PATH. Please install Python to continue."
        return 1
    fi

    pversion=$(python -V 2>&1 | awk '{print $2}')

    local JQ_EXE="$REPO_ROOT/bin/jq.exe"
    if $FULL && [ -f "$JQ_EXE" ]; then

        latestVersion=$(curl -s https://endoflife.date/api/python.json | "$JQ_EXE" -r '.[0].latest')
        pMajorMinor=$(echo "$pversion" | cut -d. -f1,2)
        latestMajorMinor=$(echo "$latestVersion" | cut -d. -f1,2)
        if [ "$pMajorMinor" != "$latestMajorMinor" ]; then
            log_warn "Consider updating python to $latestVersion."
        fi
    fi

    log_success "Python version: $pversion"

    return 0
}

ensure_git()
{
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed or not in PATH. Please install Git to continue."
        return 1
    fi

    gversion=$(git --version 2>&1 | awk '{print $3}')
    log_success "Git version: $gversion"

    return 0
}

ensure_auth_ssh()
{
    echo ""
    echo -ne "Checking auth...\r"

    python "$SRC_DIR/GlobalEnv.py" --decrypt

    local RETURN_CODE=$?
    if [ $RETURN_CODE -ne 0 ]; then
        log_error "Decryption failed with exit code: $RETURN_CODE"
        return $RETURN_CODE
    fi

    log_success "Decryption success"

    # kill running ssh-agents if any
    ps aux | grep ssh-agent | awk '{print $1}' | xargs -r kill 2>/dev/null
    eval "$(ssh-agent -s)" &>/dev/null

    local KEY="$REPO_ROOT/encrypted/github_key"
    if [ ! -f "$KEY" ]; then
        log_error "SSH github key file not found at: $KEY"
        return 1
    fi

    ssh-add "$KEY" &>/dev/null
    if [ $? -ne 0 ]; then
        log_error "SSH Failed. Could not add key: $KEY"
        return 1
    fi

    git remote set-url origin git@github.com:lebenebou/EnvSync.git

    ssh -T git@github.com >/dev/null 2>&1
    local SSH_EXIT=$?
    if [ $SSH_EXIT -ne 0 ] && [ $SSH_EXIT -ne 1 ]; then
        log_error "SSH Failed. Could not connect to github with SSH."
        return 1
    fi

    log_success "Init SSH"
    return 0
}

update_bash_profile()
{
    python "$CONFIG_DIR/BashProfile.py" --in_place 2> /dev/null

    local EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        log_error "Bash profile update failed with exit code: $EXIT_CODE"
        return $EXIT_CODE
    fi

    log_success "Bash profile updated"
    return 0
}

update_vimrc()
{
    python "$CONFIG_DIR/VimRC.py" --in_place 2> /dev/null

    local EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        log_error "Vim configuration update failed with exit code: $EXIT_CODE"
        return $EXIT_CODE
    fi

    log_success "Vim configuration updated"
    return 0
}

sync_vim_plugins()
{
    echo ""

    $VERBOSE && echo "Checking vim installation..."
    if ! command -v vim &> /dev/null; then
        log_warn "vim not found in PATH, skipping plugin sync"
        return 1
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

verify_repo()
{
    echo ""

    if [ ! -d "$REPO_ROOT/.git" ]; then
        log_error "Not in EnvSync repository root. .git folder not found."
        echo "Expected: $REPO_ROOT/.git"
        return 1
    fi

    if $SOFT; then
        return 0
    fi

    # Check if main branch is ahead of the current commit
    cd "$REPO_ROOT"
    echo -ne "git fetch --all...\r"
    git fetch --all &> /dev/null
    if [ $? -ne 0 ]; then
        log_warn "Failed to fetch remote repository. Skipping update check."
        return 1
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

ensure_bin_utils()
{
    echo ""
    mkdir -p "$REPO_ROOT/bin"

    ensure_jq  || return 1
    ensure_fd  || return 1
    ensure_bat || return 1

    log_success "Bin utilities check"
    return 0
}

_esync_main()
{
    echo -e \\nWelcome $(whoami)!\\n

    ensure_git || return $?
    ensure_auth_ssh || return $?
    verify_repo || return $?

    ensure_python || return $?

    echo ""
    if ! $SOFT; then
        update_bash_profile || { $FAIL_FAST && return 1; }
        update_vimrc || { $FAIL_FAST && return 1; }
    fi

    if $FULL; then
        # steps inside this block may take time
        sync_vim_plugins || { $FAIL_FAST && return 1; }
    fi

    ensure_bin_utils || { $FAIL_FAST && return 1; }

    if $FULL; then

        if ! "$REPO_ROOT/tests/run_all.sh" ; then
            log_error "Some tests failed. Please review the test output above."
            $FAIL_FAST && return 1
        else
            log_success "All tests passed successfully!"
        fi
    fi

    echo ""
    log_success "EnvSync Ready!"
    return 0
}

clear
_esync_main

# Cleanup functions
unset -f $(comm -13 <(sort <<< "$_esync_pre_fns") <(declare -F | awk '{print $3}' | sort))

# Cleanup variables
unset $(comm -13 <(sort <<< "$_esync_pre_vars") <(compgen -v | sort) | grep -v '^SSH_'); unset _esync_pre_vars _esync_pre_fns