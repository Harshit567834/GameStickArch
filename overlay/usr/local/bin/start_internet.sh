#!/bin/bash
echo "================================================="
echo " Transitioning from Terminal to Full Internet..."
echo "================================================="

PORT=""
for p in /dev/ttyUSB0 /dev/ttyACM0 /dev/ttyS0; do
    if [ -e "$p" ]; then
        PORT="$p"
        break
    fi
done

if [ -z "$PORT" ]; then
    echo "Error: No serial port found!"
    exit 1
fi

echo "Using port: $PORT"
echo "Sending switch signal to ESP32..."
echo -n "+++PPP" > "$PORT"

echo "Stopping serial terminal service..."
systemctl stop serial-getty@$(basename $PORT).service

echo "Starting PPP Daemon..."
killall pppd 2>/dev/null
sleep 1
pppd "$PORT" 115200 local noauth defaultroute persist maxfail 0 &

echo ""
echo "Success! The ESP32 is now acting as a NAT Router."
echo "Please wait ~10 seconds for the IP connection to negotiate."
echo "You can now open a fresh terminal on your PC and run:"
echo "    ssh root@gamestick.local"
echo ""
echo "(Note: This terminal will now detach because the port is in use by PPP)"

# Kill the current shell so it stops fighting pppd for the serial port
kill -9 $PPID
