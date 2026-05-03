#!/bin/bash

# EnvSync Repository Initialization Script
# This script orchestrates the initialization of the EnvSync repository
# It decrypts encrypted files, updates bash profile, and syncs vim configuration
# 
# Usage: ./init.sh

set -e  # Exit on any error

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_ROOT/src"
CONFIG_DIR="$SRC_DIR/config"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_success() {
    echo -e "${GREEN}[DONE]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ ERR]${NC} $1"
}

# Verify we're in the repo root
if [ ! -d "$REPO_ROOT/.git" ]; then
    log_error "Not in EnvSync repository root. .git folder not found."
    echo "Expected: $REPO_ROOT/.git"
    exit 1
fi

echo "Starting EnvSync initialization..."
echo "Repository root: $REPO_ROOT"

# Step 1: Decrypt encrypted files
echo ""
echo "Step 1: Decrypting files (GlobalEnv --decrypt)..."
if python "$SRC_DIR/GlobalEnv.py" --decrypt; then
    log_success "Decryption check passed"
else
    DECRYPT_EXIT=$?
    log_error "Decryption check failed with exit code: $DECRYPT_EXIT"
    exit $DECRYPT_EXIT
fi

# Step 2: Update bash profile
echo ""
echo "Step 2: Updating bash profile (--in_place)..."
if python "$CONFIG_DIR/BashProfile.py" --in_place; then
    log_success "Bash profile updated successfully"
else
    BASH_EXIT=$?
    log_error "Bash profile update failed with exit code: $BASH_EXIT"
    exit $BASH_EXIT
fi

# Step 3: Update vim configuration
echo ""
echo "Step 3: Updating vim configuration (--in_place)..."
if python "$CONFIG_DIR/VimRC.py" --in_place; then
    log_success "Vim configuration updated successfully"
else
    VIM_EXIT=$?
    log_error "Vim configuration update failed with exit code: $VIM_EXIT"
    exit $VIM_EXIT
fi

# Step 4: Sync vim plugins (optional, graceful failure)
echo ""
echo "Step 4: Syncing vim plugins..."
if command -v vim &> /dev/null; then
    if vim +PlugInstall +qall 2>/dev/null; then
        log_success "Vim plugins installed"
    else
        log_warn "Vim plugin installation encountered an issue (non-critical)"
    fi
    
    if vim +PlugClean +qall 2>/dev/null; then
        log_success "Vim plugins cleaned"
    else
        log_warn "Vim plugin cleanup encountered an issue (non-critical)"
    fi
else
    log_warn "vim not found in PATH, skipping plugin sync"
fi

# Step 5: Install utility binaries (optional, graceful failure)
echo ""
echo "Step 5: Installing utility binaries (jq, fd, bat)..."

# Create bin directory if it doesn't exist
mkdir -p "$REPO_ROOT/bin"

# Install jq
echo "  Installing jq..."
JQ_URL="https://github.com/jqlang/jq/releases/latest/download/jq-win64.exe"
JQ_PATH="$REPO_ROOT/bin/jq.exe"
if [ -f "$JQ_PATH" ]; then
    log_success "  jq already installed"
else
    if curl -L "$JQ_URL" -o "$JQ_PATH" -s 2>/dev/null; then
        log_success "  jq installed successfully"
    else
        log_warn "  jq installation encountered an issue (non-critical)"
    fi
fi

# Install fd
echo "  Installing fd..."
FD_URL="https://github.com/sharkdp/fd/releases/download/v10.3.0/fd-v10.3.0-i686-pc-windows-msvc.zip"
FD_ZIP="$REPO_ROOT/bin/fd.zip"
FD_DIR="$REPO_ROOT/bin/fd"
FD_EXE="$FD_DIR/fd.exe"
if [ -f "$FD_EXE" ]; then
    log_success "  fd already installed"
else
    rm -rf "$FD_DIR" "$FD_ZIP" 2>/dev/null
    if curl -Ls "$FD_URL" -o "$FD_ZIP" 2>/dev/null; then
        if unzip.exe "$FD_ZIP" -d "$REPO_ROOT/bin" &>/dev/null; then
            if mv "$REPO_ROOT/bin/fd-v10.3.0-i686-pc-windows-msvc" "$FD_DIR" 2>/dev/null; then
                rm -f "$FD_ZIP" 2>/dev/null
                log_success "  fd installed successfully"
            else
                log_warn "  fd installation encountered an issue (non-critical)"
            fi
        else
            log_warn "  fd installation encountered an issue (non-critical)"
        fi
    else
        log_warn "  fd installation encountered an issue (non-critical)"
    fi
fi

# Install bat
echo "  Installing bat..."
BAT_URL="https://github.com/sharkdp/bat/releases/download/v0.26.1/bat-v0.26.1-x86_64-pc-windows-msvc.zip"
BAT_ZIP="$REPO_ROOT/bin/bat.zip"
BAT_DIR="$REPO_ROOT/bin/bat"
BAT_EXE="$BAT_DIR/bat.exe"
if [ -f "$BAT_EXE" ]; then
    log_success "  bat already installed"
else
    rm -rf "$BAT_DIR" "$BAT_ZIP" 2>/dev/null
    if curl -L "$BAT_URL" -o "$BAT_ZIP" -s 2>/dev/null; then
        if unzip.exe "$BAT_ZIP" -d "$REPO_ROOT/bin" &>/dev/null; then
            if mv "$REPO_ROOT/bin/bat-v0.26.1-x86_64-pc-windows-msvc" "$BAT_DIR" 2>/dev/null; then
                rm -f "$BAT_ZIP" 2>/dev/null
                log_success "  bat installed successfully"
            else
                log_warn "  bat installation encountered an issue (non-critical)"
            fi
        else
            log_warn "  bat installation encountered an issue (non-critical)"
        fi
    else
        log_warn "  bat installation encountered an issue (non-critical)"
    fi
fi

echo ""
log_success "EnvSync initialization completed successfully!"
exit 0