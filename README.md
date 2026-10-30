# GameStickArch

A minimal, custom Arch Linux ARM system tailored for the **Gamestick Lite 4K**. It includes a text-based UI, an automated first-boot expansion script, and native support for both standard USB Wi-Fi adapters and an ESP32 modem integration!

## Features
- **Size**: ~1.9GB image.
- **Internet Connectivity Options**: 
  - Plug-and-play support for standard USB Wi-Fi adapters (managed via NetworkManager).
  - ESP32 Modem support via USB cable (`/dev/ttyUSB0`) or internal UART (`/dev/ttyS0`).
- **Text-Based GUI**: Easy-to-use menu (`gamestick_menu.py`) for connecting to WiFi and Bluetooth.
- **Text-Based Browser**: `lynx` included.
- **Auto-login**: Boots directly to root (password: `123`).
- **First Boot Setup**: Asks for Swap size, creates SWAP, and sets up a FAT32 partition for the remaining space on your SD card.

## How to Get the Image
1. Go to the **Actions** tab in this GitHub repository.
2. Click on the latest successful build.
3. Download the `GameStickArch-Image` artifact. (It will be a `.zip` containing `GameStickArch.img`).

*Alternatively, you can build it yourself on a Linux machine by running `sudo bash build_image.sh`.*

## Flashing to SD Card
1. Extract the `.zip` file to get `GameStickArch.img`.
2. Use **BalenaEtcher** or **Rufus** to flash `GameStickArch.img` to your SD card.
3. **Note on Bootloader**: Because Gamestick clones use various chips (Rockchip/Allwinner), you may need to copy the bootloader from your original SD card or compile u-boot for your specific board. The first 1MB of this image is left empty specifically for flashing a bootloader (e.g., `dd if=u-boot-sunxi-with-spl.bin of=/dev/sdX bs=1024 seek=8`).

## Connecting to the Internet

You have two options for getting internet access on your GameStick:

### Option 1: Standard USB Wi-Fi Adapter (Easiest)
1. Plug a standard USB Wi-Fi adapter (or dongle) directly into the GameStick's USB port. (Use an OTG splitter if you need to keep your controllers plugged in).
2. Type `gamestick_menu.py` and select **Setup WiFi (Standard USB Wi-Fi Adapter)**.
3. Select your network, enter the password, and you're connected natively via NetworkManager!

### Option 2: The ESP32 Modem
The ESP32 acts as a transparent SLIP/PPP modem for the Gamestick. You can connect it via **USB cable** or via **internal UART pins**.
1. Open the `ESP32_Modem` folder.
2. Open `ESP32_Modem.ino` in the Arduino IDE and flash it to **any ESP32** (e.g., DevKit V1).
3. Connect the ESP32 to the GameStick:
   - **Method A (USB Cable):** Plug the ESP32 directly into the GameStick's USB port. The system will automatically detect it on `/dev/ttyUSB0` or `/dev/ttyACM0`.
   - **Method B (Internal UART Pins):** Connect ESP32 TX to Gamestick RX (UART0), ESP32 RX to Gamestick TX (UART0), and GND to GND.
4. Open `gamestick_menu.py`, select **Setup WiFi (ESP32 Modem)**. The script will auto-detect the port, scan for networks, and establish a PPP connection over the serial link!

## Usage
1. Insert the SD card into the Gamestick and power it on.
2. On **first boot**, the script will ask how much SWAP (in MB) you want. It will then partition the rest of your SD card as a FAT32 share drive, format it, and reboot.
3. Upon reboot, it will auto-login to root.
4. Type `gamestick_menu.py` and press Enter to open the setup UI.
5. Select **Setup WiFi (ESP32 Modem)**. The Gamestick will communicate with the ESP32, scan for networks, and let you connect!
6. Once connected, you can use `lynx` to browse the web or SSH into the Gamestick using the IP assigned to the ESP32!
