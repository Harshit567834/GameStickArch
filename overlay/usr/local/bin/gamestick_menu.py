#!/usr/bin/env python3
import curses
import serial
import time
import subprocess
import os
import glob

BAUD_RATE = 115200

def find_esp32_port():
    # Check common USB serial ports first, then fallback to hardware UART
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + ['/dev/ttyS0']
    for port in ports:
        if os.path.exists(port):
            return port
    return None

def draw_menu(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    
    menu = [
        '1. Setup WiFi (ESP32 Modem)', 
        '2. Setup WiFi (Standard USB Wi-Fi Adapter)', 
        '3. Setup Bluetooth', 
        '4. Exit'
    ]
    current_row = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        title = " GameStick Lite 4K Configuration "
        stdscr.addstr(2, width//2 - len(title)//2, title, curses.A_BOLD | curses.A_REVERSE)
        
        for idx, row in enumerate(menu):
            x = width//2 - len(row)//2
            y = height//2 - len(menu)//2 + idx
            if idx == current_row:
                stdscr.addstr(y, x, row, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, row)
                
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu)-1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if current_row == 0:
                setup_esp32_wifi(stdscr)
            elif current_row == 1:
                setup_usb_wifi(stdscr)
            elif current_row == 2:
                setup_bluetooth(stdscr)
            elif current_row == 3:
                break

def setup_esp32_wifi(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "Connecting to ESP32 Modem...", curses.A_BOLD)
    
    serial_port = find_esp32_port()
    if not serial_port:
        stdscr.addstr(4, 2, "Error: Could not find ESP32 on /dev/ttyUSB*, /dev/ttyACM*, or /dev/ttyS0")
        stdscr.addstr(6, 2, "Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    stdscr.addstr(3, 2, f"Found device on {serial_port}")
    stdscr.refresh()
    
    try:
        ser = serial.Serial(serial_port, BAUD_RATE, timeout=2)
        # Escape PPP mode if active
        time.sleep(1.2)
        ser.write(b'+++')
        time.sleep(1.2)
        ser.read_all()
        
        stdscr.addstr(5, 2, "Scanning for WiFi networks...")
        stdscr.refresh()
        
        ser.write(b'SCAN\n')
        networks = []
        start = time.time()
        while time.time() - start < 10:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line == 'SCAN_DONE':
                break
            if line and line != 'OK':
                networks.append(line)
        
        if not networks:
            stdscr.addstr(7, 2, "No networks found. Press any key.")
            stdscr.getch()
            ser.close()
            return
            
        current_row = 0
        while True:
            stdscr.clear()
            stdscr.addstr(2, 2, "Select WiFi Network (ESP32):", curses.A_BOLD)
            for idx, net in enumerate(networks):
                if idx == current_row:
                    stdscr.addstr(4 + idx, 4, net, curses.A_REVERSE)
                else:
                    stdscr.addstr(4 + idx, 4, net)
            
            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(networks)-1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                ssid = networks[current_row]
                break
                
        # Get password
        curses.echo()
        stdscr.clear()
        stdscr.addstr(2, 2, f"Enter password for {ssid}: ", curses.A_BOLD)
        password = stdscr.getstr(4, 2, 64).decode('utf-8')
        curses.noecho()
        
        stdscr.addstr(6, 2, "Sending credentials to ESP32...")
        stdscr.refresh()
        
        ser.write(f'CONNECT {ssid} {password}\n'.encode('utf-8'))
        ser.readline() # Wait for OK
        
        stdscr.addstr(7, 2, "Starting PPP connection...")
        stdscr.refresh()
        
        ser.write(b'START\n')
        ser.close()
        
        # Start pppd as a server
        os.system(f"killall pppd 2>/dev/null")
        time.sleep(1)
        os.system(f"pppd {serial_port} {BAUD_RATE} 10.0.0.1:10.0.0.2 proxyarp local noauth defaultroute persist maxfail 0 &")
        
        stdscr.addstr(9, 2, "WiFi configured via ESP32! Press any key.")
        stdscr.getch()
        
    except Exception as e:
        stdscr.addstr(5, 2, f"Error: {e}")
        stdscr.addstr(7, 2, "Press any key.")
        stdscr.getch()

def setup_usb_wifi(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "Scanning for Wi-Fi networks (USB Adapter)...", curses.A_BOLD)
    stdscr.refresh()
    
    # Ensure NetworkManager is running and Wi-Fi is enabled
    os.system("systemctl start NetworkManager >/dev/null 2>&1")
    os.system("nmcli radio wifi on >/dev/null 2>&1")
    time.sleep(2)
    
    try:
        # Scan for SSIDs
        output = subprocess.check_output("nmcli -t -f SSID dev wifi", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        networks = list(set([line for line in output.split('\n') if line.strip()]))
    except Exception:
        stdscr.addstr(4, 2, "Failed to scan. Is a USB Wi-Fi adapter plugged in?")
        stdscr.addstr(6, 2, "Press any key to return.")
        stdscr.getch()
        return

    if not networks:
        stdscr.addstr(4, 2, "No networks found. Ensure Wi-Fi adapter is connected.")
        stdscr.addstr(6, 2, "Press any key to return.")
        stdscr.getch()
        return
        
    current_row = 0
    while True:
        stdscr.clear()
        stdscr.addstr(2, 2, "Select WiFi Network (USB Adapter):", curses.A_BOLD)
        for idx, net in enumerate(networks):
            if idx == current_row:
                stdscr.addstr(4 + idx, 4, net, curses.A_REVERSE)
            else:
                stdscr.addstr(4 + idx, 4, net)
        
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(networks)-1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            ssid = networks[current_row]
            break
            
    # Get password
    curses.echo()
    stdscr.clear()
    stdscr.addstr(2, 2, f"Enter password for {ssid}: ", curses.A_BOLD)
    password = stdscr.getstr(4, 2, 64).decode('utf-8')
    curses.noecho()
    
    stdscr.addstr(6, 2, "Connecting...")
    stdscr.refresh()
    
    # Connect using nmcli
    result = os.system(f"nmcli dev wifi connect '{ssid}' password '{password}' >/dev/null 2>&1")
    
    if result == 0:
        stdscr.addstr(8, 2, "Successfully connected! Press any key.")
    else:
        stdscr.addstr(8, 2, "Failed to connect. Press any key.")
        
    stdscr.getch()

def setup_bluetooth(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "Bluetooth Setup", curses.A_BOLD)
    stdscr.addstr(4, 2, "To setup Bluetooth, we will drop you into 'bluetoothctl'.")
    stdscr.addstr(5, 2, "Type 'scan on', wait for devices, then 'pair <MAC>'")
    stdscr.addstr(6, 2, "Type 'quit' to return to this menu.")
    stdscr.addstr(8, 2, "Press any key to enter bluetoothctl...")
    stdscr.refresh()
    stdscr.getch()
    
    curses.endwin()
    subprocess.call("bluetoothctl", shell=True)
    stdscr.clear()

if __name__ == '__main__':
    curses.wrapper(draw_menu)
