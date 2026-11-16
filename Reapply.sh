#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
exec ./theme.py reapply
