import tkinter as tk
from tkinter import messagebox
import socket
import threading
import urllib.request
import urllib.parse
import sys

# ESP32 Default AP IP and TCP Port
ESP32_IP = "192.168.4.1"
ESP32_PORT = 23

class GameStickTerminalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GameStick Wireless Terminal")
        self.root.geometry("800x600")
        
        self.sock = None
        self.connected = False
        
        # --- UI LAYOUT ---
        # Top Frame: Wi-Fi Configuration
        top_frame = tk.Frame(self.root, bg="#2d2d2d", pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="ESP32 IP:", bg="#2d2d2d", fg="white").pack(side=tk.LEFT, padx=5)
        self.ip_entry = tk.Entry(top_frame, width=15)
        self.ip_entry.insert(0, ESP32_IP)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(top_frame, text="Connect Terminal", command=self.connect_terminal)
        self.connect_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Label(top_frame, text=" | ", bg="#2d2d2d", fg="white").pack(side=tk.LEFT)
        
        tk.Label(top_frame, text="Wi-Fi SSID:", bg="#2d2d2d", fg="white").pack(side=tk.LEFT, padx=5)
        self.ssid_entry = tk.Entry(top_frame, width=15)
        self.ssid_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(top_frame, text="Pass:", bg="#2d2d2d", fg="white").pack(side=tk.LEFT, padx=5)
        self.pass_entry = tk.Entry(top_frame, width=15, show="*")
        self.pass_entry.pack(side=tk.LEFT, padx=5)
        
        self.wifi_btn = tk.Button(top_frame, text="Send Wi-Fi to ESP32", command=self.send_wifi_credentials)
        self.wifi_btn.pack(side=tk.LEFT, padx=10)

        # Middle Frame: Terminal Output
        mid_frame = tk.Frame(self.root)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_area = tk.Text(mid_frame, bg="black", fg="#00ff00", font=("Consolas", 12), state=tk.NORMAL)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(mid_frame, command=self.text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=scrollbar.set)
        
        self.text_area.insert(tk.END, "Welcome to GameStick Wireless Terminal.\n")
        self.text_area.insert(tk.END, "Connect to the 'GameStick-Terminal' Wi-Fi network first, then click 'Connect Terminal'.\n\n")

        # Bottom Frame: Command Input
        bottom_frame = tk.Frame(self.root, pady=10)
        bottom_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(bottom_frame, text="Command:").pack(side=tk.LEFT)
        self.cmd_entry = tk.Entry(bottom_frame, font=("Consolas", 12))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", self.send_command)
        
        send_btn = tk.Button(bottom_frame, text="Send", command=self.send_command)
        send_btn.pack(side=tk.LEFT)

    def log(self, msg):
        self.text_area.insert(tk.END, msg + "\n")
        self.text_area.see(tk.END)

    def connect_terminal(self):
        if self.connected:
            self.log("Already connected.")
            return
            
        ip = self.ip_entry.get()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3)
        try:
            self.log(f"Attempting to connect to {ip}:{ESP32_PORT}...")
            self.sock.connect((ip, ESP32_PORT))
            self.sock.settimeout(None)
            self.connected = True
            self.log("--- CONNECTED TO GAMESTICK SERIAL CONSOLE ---")
            
            # Start background thread to listen for serial data
            threading.Thread(target=self.receive_data, daemon=True).start()
            
            # Send an enter key to wake up the prompt
            self.sock.send(b"\n")
            
        except Exception as e:
            self.log(f"Connection failed: {e}")
            self.sock = None

    def receive_data(self):
        while self.connected:
            try:
                data = self.sock.recv(1024)
                if data:
                    text = data.decode('utf-8', errors='replace')
                    self.text_area.insert(tk.END, text)
                    self.text_area.see(tk.END)
                else:
                    self.log("\n--- CONNECTION CLOSED BY ESP32 ---")
                    self.connected = False
                    break
            except Exception as e:
                self.log(f"\n--- CONNECTION LOST: {e} ---")
                self.connected = False
                break

    def send_command(self, event=None):
        if not self.connected:
            messagebox.showerror("Error", "Connect to the terminal first!")
            return
            
        cmd = self.cmd_entry.get() + "\n"
        try:
            self.sock.send(cmd.encode('utf-8'))
            self.cmd_entry.delete(0, tk.END)
        except Exception as e:
            self.log(f"Failed to send command: {e}")

    def send_wifi_credentials(self):
        ip = self.ip_entry.get()
        ssid = self.ssid_entry.get()
        pwd = self.pass_entry.get()
        
        if not ssid:
            messagebox.showerror("Error", "Please enter an SSID!")
            return
            
        data = urllib.parse.urlencode({'ssid': ssid, 'pass': pwd}).encode('ascii')
        url = f"http://{ip}/setwifi"
        
        self.log(f"Sending Wi-Fi credentials to {url}...")
        try:
            req = urllib.request.Request(url, data=data, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                res = response.read().decode('utf-8')
                self.log(f"ESP32 Response: {res}")
                messagebox.showinfo("Success", "Credentials sent! The ESP32 is now attempting to connect.")
        except Exception as e:
            self.log(f"Failed to send credentials: {e}")
            messagebox.showerror("Error", "Could not reach ESP32 HTTP Server. Make sure you are connected to the 'GameStick-Terminal' Wi-Fi network.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameStickTerminalApp(root)
    root.mainloop()