#!/bin/bash

# EnvSync Repository Reset Script
# This script removes all generated/extracted files to reset the repo to initial state
# It deletes: encrypted/, config.json, and bin/ folders
# 
# Usage: ./reset.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verify we're in the repo root
if [ ! -d "$REPO_ROOT/.git" ]; then
    log_error "Not in EnvSync repository root. .git folder not found."
    echo "Expected: $REPO_ROOT/.git"
    exit 1
fi

log_info "Starting EnvSync reset..."
log_info "Repository root: $REPO_ROOT"
echo ""

# Reset encrypted/ folder
ENCRYPTED_DIR="$REPO_ROOT/encrypted"
if [ -d "$ENCRYPTED_DIR" ]; then
    log_info "Deleting encrypted/ folder..."
    rm -rf "$ENCRYPTED_DIR"
    log_info "encrypted/ folder deleted"
else
    log_warn "encrypted/ folder not found, skipping"
fi

echo ""

# Reset config.json file
CONFIG_FILE="$REPO_ROOT/config.json"
if [ -f "$CONFIG_FILE" ]; then
    log_info "Deleting config.json file..."
    rm -f "$CONFIG_FILE"
    log_info "config.json file deleted"
else
    log_warn "config.json file not found, skipping"
fi

echo ""

# Reset bin/ folder
BIN_DIR="$REPO_ROOT/bin"
if [ -d "$BIN_DIR" ]; then
    log_info "Deleting bin/ folder..."
    rm -rf "$BIN_DIR"
    log_info "bin/ folder deleted"
else
    log_warn "bin/ folder not found, skipping"
fi

echo ""
log_info "EnvSync reset completed successfully!"
exit 0
