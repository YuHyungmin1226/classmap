#!/bin/bash

# Ensure pyinstaller is available
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -m pip install pyinstaller

# Clean old builds
rm -rf build/ dist/ ClassMap.spec

echo "Building ClassMap Executable..."

# Run PyInstaller
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -m PyInstaller --name "ClassMap" \
    --onefile \
    --add-data "app/templates:app/templates" \
    --add-data "app/static:app/static" \
    --hidden-import "eventlet" \
    --hidden-import "engineio.async_drivers.eventlet" \
    --hidden-import "gevent" \
    --hidden-import "geventwebsocket" \
    --hidden-import "engineio.async_drivers.gevent" \
    run.py

echo "Build complete! The standalone executable is located in the dist/ directory."
