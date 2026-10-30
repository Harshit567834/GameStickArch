# GameStickArch

A minimal, custom Arch Linux ARM system tailored for the **Gamestick Lite 4K**. It includes a text-based UI, an automated first-boot expansion script, and an ESP32 modem integration for WiFi and SSH!

## Features
- **Size**: ~1.9GB image.
- **ESP32 Modem**: Use an ESP32 as a WiFi modem to provide internet access to the Gamestick.
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

## Setting up the ESP32 Modem
The ESP32 acts as a transparent SLIP/PPP modem for the Gamestick.
1. Open the `ESP32_Modem` folder.
2. Open `ESP32_Modem.ino` in the Arduino IDE.
3. Flash it to **any ESP32** (e.g., DevKit V1).
4. Connect the ESP32 to the Gamestick via UART:
   - ESP32 TX -> Gamestick RX (UART0)
   - ESP32 RX -> Gamestick TX (UART0)
   - GND -> GND

## Usage
1. Insert the SD card into the Gamestick and power it on.
2. On **first boot**, the script will ask how much SWAP (in MB) you want. It will then partition the rest of your SD card as a FAT32 share drive, format it, and reboot.
3. Upon reboot, it will auto-login to root.
4. Type `gamestick_menu.py` and press Enter to open the setup UI.
5. Select **Setup WiFi (ESP32 Modem)**. The Gamestick will communicate with the ESP32, scan for networks, and let you connect!
6. Once connected, you can use `lynx` to browse the web or SSH into the Gamestick using the IP assigned to the ESP32!
