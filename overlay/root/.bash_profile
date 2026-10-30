#!/bin/bash
if [ -f /usr/local/bin/first_boot.sh ]; then
    /usr/local/bin/first_boot.sh
fi

# Start the menu after first boot
if [ ! -f /usr/local/bin/first_boot.sh ]; then
    echo "Welcome to GameStickArch!"
    echo "Type 'gamestick_menu.py' to configure WiFi/Bluetooth."
    echo "Type 'lynx' to browse the web."
fi
