#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define directories
TARGET_DIR="data/raw/github/standards-data"

if [ -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR already exists. Skipping clone."
else
    echo "Cloning SirFizX/standards-data..."
    git clone https://github.com/SirFizX/standards-data.git "$TARGET_DIR"
    echo "Clone complete."
fi
