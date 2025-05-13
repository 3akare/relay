#!/bin/bash
[ -d /opt/relay ] && sudo rm -rf /opt/relay
[ -L /usr/local/bin/relay ] && sudo rm /usr/local/bin/relay
echo "Uninstallation complete."