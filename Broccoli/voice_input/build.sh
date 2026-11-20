#!/bin/sh
# Builds BroccoliVoice (the dictation helper) next to this script. Needs Xcode's command line
# tools with the macOS 26 SDK or later. The packaged app carries the built program in
# Contents/MacOS; it is signed there with the app's own identity.
set -e
cd "$(dirname "$0")"
swiftc -O -swift-version 5 -target arm64-apple-macos26.0 voice_input_helper.swift -o BroccoliVoice
echo "built: $(pwd)/BroccoliVoice"
