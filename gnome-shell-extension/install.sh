#!/bin/bash

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DEST="${HOME}/.local/share/gnome-shell/extensions/homeautomation@alerighi.it"
mkdir -pv $(dirname "${DEST}")
ln -svf --backup "${SCRIPT_DIR}" "${DEST}"

