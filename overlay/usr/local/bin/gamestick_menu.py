#!/usr/bin/env python3
import curses
import serial
import time
import subprocess
import os

SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200

def draw_menu(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    
    menu = ['1. Setup WiFi (ESP32 Modem)', '2. Setup Bluetooth', '3. Exit']
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
                setup_wifi(stdscr)
            elif current_row == 1:
                setup_bluetooth(stdscr)
            elif current_row == 2:
                break

def setup_wifi(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "Connecting to ESP32 Modem...", curses.A_BOLD)
    stdscr.refresh()
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        # Escape PPP mode if active
        time.sleep(1.2)
        ser.write(b'+++')
        time.sleep(1.2)
        ser.read_all()
        
        stdscr.addstr(4, 2, "Scanning for WiFi networks...")
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
            stdscr.addstr(6, 2, "No networks found. Press any key.")
            stdscr.getch()
            ser.close()
            return
            
        current_row = 0
        while True:
            stdscr.clear()
            stdscr.addstr(2, 2, "Select WiFi Network:", curses.A_BOLD)
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
        
        # Start pppd
        os.system(f"killall pppd 2>/dev/null")
        time.sleep(1)
        os.system(f"pppd {SERIAL_PORT} {BAUD_RATE} local noauth defaultroute persist maxfail 0 &")
        
        stdscr.addstr(9, 2, "WiFi configured! Press any key.")
        stdscr.getch()
        
    except Exception as e:
        stdscr.addstr(4, 2, f"Error: {e}")
        stdscr.addstr(6, 2, "Press any key.")
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
