#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p bin
c++ -std=c++17 -O2 -Wall -Wextra -fPIC app/reatheme.cpp -o bin/REATheme $(pkg-config --cflags --libs Qt6Widgets Qt6Gui Qt6Core)
