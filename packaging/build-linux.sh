#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 packaging/build.py
echo "Binario: dist/musetop/musetop"
echo "Escritorio: dist/musetop/musetop.desktop"
