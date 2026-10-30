# GameStickArch - The Ultimate Guide

A minimal, custom Arch Linux ARM system specifically tailored for the **GameStick Lite 4K**. 

This system transforms the locked-down GameStick into a fully functional, headless (or text-GUI) Linux server with an automated first-boot SD card expansion script, out-of-the-box support for USB Wi-Fi adapters, and a custom ESP32 serial modem implementation.

---

## 1. Installation

### 1.1 Downloading the Image
1. Go to the **[Releases](https://github.com/Harshit567834/GameStickArch/releases)** tab on this GitHub repository.
2. Download the latest `GameStickArch_Release.zip` file.
3. Extract the zip file to your computer. You will find `GameStickArch.img` and a folder containing the ESP32 code.

### 1.2 Flashing to your SD Card
1. Download **[Rufus](https://rufus.ie/)** or **[BalenaEtcher](https://balena.io/etcher/)**.
2. Insert your GameStick's SD card (e.g., 64GB) into your computer.
3. Select `GameStickArch.img` and flash it to the SD card.
4. *Note on Bootloaders:* GameStick clones use various generic chips (like Rockchip or Allwinner). To ensure it boots, you may need to copy the original bootloader from your stock GameStick SD card. The first 1MB of this Arch image is deliberately left empty so you can inject a bootloader (e.g. `dd if=u-boot-sunxi-with-spl.bin of=/dev/sdX bs=1024 seek=8`).

---

## 2. Setting Up the Internet (The Chicken-and-Egg Problem)

Because the GameStick lacks a keyboard, getting it on the network to SSH into it is normally a hassle. GameStickArch provides two incredibly simple ways to connect to the internet.

### Method A: "Headless" Auto-Setup (Recommended!)
We have included a script that runs automatically on startup. You do not need a keyboard or a screen for this!

1. After flashing the SD card, leave it plugged into your PC.
2. Open the SD card's **`BOOT`** partition (it is formatted as FAT32, so Windows/Mac can read it).
3. Open the file named **`wifi.txt`** in any text editor.
4. It will look like this:
   ```ini
   # GameStickArch Headless Wi-Fi Configuration
   # TYPE can be either "USB" (for standard Wi-Fi dongles) or "ESP32" (for the custom modem)
   TYPE=USB
   SSID=YourNetworkNameHere
   PASS=YourNetworkPasswordHere
   ```
5. Change `TYPE` to either `USB` (if you are plugging in a USB Wi-Fi dongle) or `ESP32` (if you are using the custom modem trick).
6. Fill in your Wi-Fi `SSID` and `PASS`.
7. Save the file.
8. Put the SD card in the GameStick and turn it on. In the background, the OS will automatically detect `wifi.txt`, connect to your network, and you can immediately SSH into it! 
*(Note: It does not delete `wifi.txt`. It safely checks if you are already connected to prevent endless loops, so you can leave the file there forever).*

### Method B: The Interactive Menu
If you happen to have a USB keyboard plugged into the GameStick (via an OTG splitter hub):
1. Plug your GameStick into a TV.
2. The OS will automatically log you into the `root` terminal.
3. Type `gamestick_menu.py` and press Enter.
4. A beautiful text-based GUI will appear. Use your arrow keys to select your network adapter, scan for Wi-Fi networks, and type your password on-screen.

---

## 3. Hardware Connectivity Guides

### Hardware Option 1: Standard USB Wi-Fi Adapter (Easiest)
NetworkManager is pre-installed. If you have a standard Linux-compatible USB Wi-Fi dongle (like a TP-Link or generic 802.11n adapter), just plug it into the GameStick's USB port. Use the `wifi.txt` method or the `gamestick_menu.py` to connect.

### Hardware Option 2: The ESP32 Wireless Terminal
Because the GameStick's standard USB-A port might not supply 5V on first boot without device tree modifications, we can use an ESP32 as a "Wireless Serial Bridge" to get a direct, raw terminal into the GameStick!

1. Open the `ESP32_Wireless_Terminal` folder from your downloaded release.
2. Open `ESP32_Wireless_Terminal.ino` in the **Arduino IDE** and flash it to your ESP32.
3. **Hardware Connection (No Soldering!):**
   - You need a **Micro-USB OTG Y-Cable** (a cable that has a Micro-USB for the GameStick, a USB-A port for devices, and another plug for power injection).
   - Plug the OTG end into the GameStick.
   - Plug your wall power into the power-injection port (this powers the GameStick *and* the ESP32).
   - Plug the ESP32 directly into the USB-A data port using a standard Micro-USB cable.
   - *Alternative (Internal Pins):* Solder ESP32 TX to GameStick RX, ESP32 RX to GameStick TX, and power the ESP32 separately with a phone charger.
4. **Using the PC GUI:**
   - With the ESP32 powered on, look at your PC's Wi-Fi networks and connect to **`GameStick-Terminal`** (Password: `12345678`).
   - Run the Python app: `python GameStick_Console.py` (Works natively on Windows, Mac, and Linux).
   - Click **Connect Terminal**. You will instantly be dropped into a live `root@gamestick:~#` terminal. 
   - You now have full diagnostic access to the GameStick! Run `dmesg` to check hardware logs, manually configure Wi-Fi, or explore the file system without ever needing an HDMI screen or keyboard!

---

## 4. First Boot Expansion & Swap Setup

When you first power on the GameStick with this image, it does a few magic tricks automatically to maximize your SD Card space:

1. **Partitioning:** The base image is 1.9GB. The script analyzes your physical SD card (e.g. 64GB).
2. **Swap:** It prompts you asking how much RAM Swap you want (in MB). We recommend `1024` (1GB). It instantly creates this Swap partition.
3. **FAT32 Expansion:** It takes the *entire remaining space* of the SD card and formats it as a `FAT32` share drive (mounted at `/mnt/share`). This allows you to effortlessly drag and drop ROMs, files, or scripts from a Windows/Mac PC directly onto the SD card without dealing with Ext4 permissions.
4. The system automatically updates `/etc/fstab` and reboots to finalize the layout.

---

## 5. Using the System

- **SSH Access:** Because the system broadcasts its hostname, you don't even need to look up its IP address!
  - On your computer, open a terminal (or Command Prompt / PowerShell) and simply type: **`ssh root@gamestick.local`**
  - Username: `root`
  - Password: `123`
  - *(If `gamestick.local` fails to resolve on your older network, you can still find the GameStick's IP on your router and connect via `ssh root@192.168.1.50`).*
- **Text-Browser:** Type `lynx` in the terminal to browse the internet purely in text.
- **Bluetooth:** Type `gamestick_menu.py` and select **Setup Bluetooth**. This securely drops you into `bluetoothctl` so you can type `scan on` and `pair <MAC_ADDRESS>` to link your wireless controllers!