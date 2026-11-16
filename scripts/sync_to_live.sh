#!/usr/bin/env bash
set -e

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/custom_components/smart_storage_ems"
TARGET_DIR="/Volumes/config/custom_components/smart_storage_ems"

if [ ! -d "/Volumes/config" ]; then
  echo "Błąd: /Volumes/config nie jest zamontowany!"
  exit 1
fi

echo "Synchronizacja $SOURCE_DIR -> $TARGET_DIR..."
cp -R "$SOURCE_DIR/" "$TARGET_DIR/"
echo "Gotowe! Zsynchronizowano pomyślnie."
