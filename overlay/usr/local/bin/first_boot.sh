#!/bin/bash

echo "========================================="
echo " GameStickArch First Boot Setup"
echo "========================================="
echo ""

# Find the SD card device (assuming /dev/mmcblk0)
DEV="/dev/mmcblk0"
if [ ! -b "$DEV" ]; then
    # Fallback to /dev/sda if mmcblk0 doesn't exist
    DEV="/dev/sda"
fi

echo "Using device: $DEV"

read -p "Enter the amount of SWAP you want in MB (e.g., 512, 1024, 2048): " SWAP_MB

if ! [[ "$SWAP_MB" =~ ^[0-9]+$ ]]; then
    echo "Invalid input. Defaulting to 512MB."
    SWAP_MB=512
fi

echo "Creating partitions..."

# We assume Partition 1 is BOOT, Partition 2 is ROOT.
# We will create Partition 3 for SWAP and Partition 4 for FAT32.

fdisk $DEV <<EOF
n
p
3

+${SWAP_MB}M
t
3
82
n
p
4


t
4
c
w
EOF

echo "Informing kernel of partition changes..."
partprobe $DEV
sleep 2

# Format partitions
if [[ "$DEV" == *"mmcblk"* ]]; then
    PART3="${DEV}p3"
    PART4="${DEV}p4"
else
    PART3="${DEV}3"
    PART4="${DEV}4"
fi

echo "Formatting SWAP on $PART3..."
mkswap $PART3
swapon $PART3

echo "Formatting FAT32 on $PART4..."
mkfs.vfat -F 32 $PART4

# Add to fstab
echo "$PART3 none swap defaults 0 0" >> /etc/fstab
echo "$PART4 /mnt/share vfat defaults,uid=1000,gid=1000,umask=022 0 0" >> /etc/fstab

mkdir -p /mnt/share
mount -a

echo "Setup complete! Removing first boot script..."
rm -f /usr/local/bin/first_boot.sh

echo "Rebooting in 3 seconds to apply changes..."
sleep 3
reboot
