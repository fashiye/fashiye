#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "重启服务..."
$SCRIPT_DIR/stop.sh
sleep 2
$SCRIPT_DIR/start.sh
