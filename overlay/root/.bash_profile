#!/bin/bash
if [ -f /usr/local/bin/first_boot.sh ]; then
    /usr/local/bin/first_boot.sh
fi

# Run headless WiFi setup silently in background
/usr/local/bin/gamestick_menu.py --headless &

# Start the menu after first boot
if [ ! -f /usr/local/bin/first_boot.sh ]; then
    echo "Welcome to GameStickArch!"
    echo "Type 'gamestick_menu.py' to configure WiFi/Bluetooth interactively."
    echo "Type 'lynx' to browse the web."
fi
