#!/bin/bash
set -e

APP="SendEmailGUI3.app"
INSTALL_DIR="/Applications"

echo "SendEmailGUI3 – macOS installer"
echo "================================"
echo ""

if [ ! -d "$APP" ]; then
  echo "Error: $APP not found in the current directory."
  echo "Please run this script from the folder where you extracted SendEmailGUI3-mac.zip"
  exit 1
fi

echo "Removing macOS quarantine restriction..."
xattr -dr com.apple.quarantine "$APP"
echo "Done."
echo ""

read -p "Move SendEmailGUI3.app to /Applications? [Y/n] " answer
answer=${answer:-Y}

if [[ "$answer" =~ ^[Yy]$ ]]; then
  if [ -d "$INSTALL_DIR/$APP" ]; then
    echo "Replacing existing installation..."
    rm -rf "$INSTALL_DIR/$APP"
  fi
  mv "$APP" "$INSTALL_DIR/"
  echo "Installed: $INSTALL_DIR/$APP"
  echo ""
  echo "You can now launch SendEmailGUI3 from Launchpad or Spotlight."
else
  echo "Skipped. You can run $APP from this folder."
fi
