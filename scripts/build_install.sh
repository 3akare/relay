#!/bin/bash
command -v pyinstaller >/dev/null 2>&1 || { echo "PyInstaller not found. Install it first."; exit 1; }
if [ ! -d "src/relay" ]; then
    echo "Directory src/relay not found."
    exit 1
fi

if [ ! -f "src/relay/relay.py" ]; then
    echo "File src/relay/relay.py not found."
    exit 1
fi

[ -d /opt ] || sudo mkdir -p /opt
[ -d /usr/local/bin ] || sudo mkdir -p /usr/local/bin
sudo pyinstaller --onedir src/relay/relay.py --clean --add-data "src/relay:relay" --hidden-import toml --hidden-import json --hidden-import platform

if [ ! -d dist/relay ]; then
    echo "Build failed. dist/relay not found."
    exit 1
fi

sudo mv dist/relay /opt/. || { echo "Failed to move relay to /opt."; exit 1; }
[ -L /usr/local/bin/relay ] && sudo rm /usr/local/bin/relay
sudo ln -s /opt/relay/relay /usr/local/bin/relay || { echo "Failed to create symlink."; exit 1; }
[ -d build ] && sudo rm -rf build
[ -d dist ] && sudo rm -rf dist
[ -f *.spec ] && sudo rm -f *.spec
echo "Build and installation complete."