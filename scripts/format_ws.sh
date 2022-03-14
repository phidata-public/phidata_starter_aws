#!/bin/bash

############################################################################
#
# Format workspace using black and mypy
# Usage:
#   ./scripts/format_ws.sh
#
############################################################################

CURR_SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_DIR="$( dirname $CURR_SCRIPT_PATH )"
DATA_DIR=$ROOT_DIR/data

print_horizontal_line() {
  echo "------------------------------------------------------------"
}

print_heading() {
  print_horizontal_line
  echo "--*--> $1"
  print_horizontal_line
}

main() {
  print_heading "Running: black $DATA_DIR"
  black $DATA_DIR
  # currently skipped
  # print_heading "Running: mypy $DATA_DIR"
  # mypy $DATA_DIR
}

main "$@"
