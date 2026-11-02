#!/bin/bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="${1:-$SOURCE_DIR/../Hexwise.app}"
if [ -e "$APP_PATH" ]; then
  echo "Output already exists. Choose a fresh .app path."
  exit 1
fi
mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources/app"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/hexwise-build.XXXXXX")"
trap 'rm -rf "$BUILD_DIR"' EXIT
swiftc -target "$(uname -m)-apple-macos12.0" -module-cache-path "$BUILD_DIR/modules" "$SOURCE_DIR/macos/Hexwise.swift" -o "$APP_PATH/Contents/MacOS/Hexwise" -framework Cocoa -framework WebKit -O
swiftc -module-cache-path "$BUILD_DIR/modules" "$SOURCE_DIR/macos/Icon.swift" -o "$BUILD_DIR/make-icon" -framework AppKit
"$BUILD_DIR/make-icon" "$BUILD_DIR/AppIcon.iconset"
python3 - "$BUILD_DIR/AppIcon.iconset" "$APP_PATH/Contents/Resources/AppIcon.icns" <<'PYICON'
import struct,sys
from pathlib import Path
root=Path(sys.argv[1]);chunks=[]
for kind,name in [('icp4','icon_16x16'),('icp5','icon_32x32'),('icp6','icon_32x32@2x'),('ic07','icon_128x128'),('ic08','icon_256x256'),('ic09','icon_512x512'),('ic10','icon_512x512@2x')]:
    image=(root/(name+'.png')).read_bytes()
    chunks.append(kind.encode()+struct.pack('>I',len(image)+8)+image)
body=b''.join(chunks)
Path(sys.argv[2]).write_bytes(b'icns'+struct.pack('>I',len(body)+8)+body)
PYICON
cp "$SOURCE_DIR/core.py" "$SOURCE_DIR/providers.py" "$SOURCE_DIR/runner.py" "$SOURCE_DIR/server.py" "$SOURCE_DIR/preferences.py" "$SOURCE_DIR/templates.py" "$SOURCE_DIR/validation.py" "$APP_PATH/Contents/Resources/app/"
cp -R "$SOURCE_DIR/web" "$SOURCE_DIR/profiles" "$APP_PATH/Contents/Resources/app/"
cat > "$APP_PATH/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>Hexwise</string>
<key>CFBundleIdentifier</key><string>com.hexwise.studio</string>
<key>CFBundleName</key><string>Hexwise</string>
<key>CFBundleIconFile</key><string>AppIcon</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.2.3</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
PLIST
codesign --force --deep --sign - "$APP_PATH"
echo "Built $APP_PATH"
