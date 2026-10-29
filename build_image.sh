#!/bin/bash
set -e

echo "Building GameStickArch Image..."

IMG_NAME="GameStickArch.img"
IMG_SIZE="1900M" # Slightly less than 2GB to fit on 2GB cards

# Create an empty sparse image file
echo "Creating sparse image file..."
truncate -s $IMG_SIZE $IMG_NAME

# Partition the image
echo "Partitioning image..."
parted -s $IMG_NAME mktable dos
parted -s $IMG_NAME mkpart primary fat32 1MiB 100MiB
parted -s $IMG_NAME set 1 boot on
parted -s $IMG_NAME mkpart primary ext4 100MiB 100%

# Setup loop device
LOOP_DEV=$(sudo losetup -fP --show $IMG_NAME)
echo "Using loop device: $LOOP_DEV"

# Format partitions
sudo mkfs.vfat -F 32 ${LOOP_DEV}p1
sudo mkfs.ext4 -O ^has_journal ${LOOP_DEV}p2

# Mount partitions
mkdir -p mnt
sudo mount ${LOOP_DEV}p2 mnt
sudo mkdir -p mnt/boot
sudo mount ${LOOP_DEV}p1 mnt/boot

# Download Arch Linux ARM rootfs
echo "Downloading Arch Linux ARM rootfs..."
wget -q http://os.archlinuxarm.org/os/ArchLinuxARM-armv7-latest.tar.gz

# Extract rootfs
echo "Extracting rootfs (this may take a while)..."
sudo bsdtar -xpf ArchLinuxARM-armv7-latest.tar.gz -C mnt

# Copy overlay files
echo "Applying overlay..."
sudo cp -r overlay/* mnt/

# Make scripts executable
sudo chmod +x mnt/usr/local/bin/first_boot.sh
sudo chmod +x mnt/usr/local/bin/gamestick_menu.py

# Setup QEMU for chroot
sudo cp /usr/bin/qemu-arm-static mnt/usr/bin/

# Configure the system inside chroot
echo "Configuring system inside chroot..."
sudo chroot mnt /bin/bash <<EOF
# Initialize pacman keyring
pacman-key --init
pacman-key --populate archlinuxarm

# Install required packages
pacman -Sy --noconfirm dosfstools parted lynx python ppp bluez bluez-utils openssh

# Enable SSH
systemctl enable sshd

# Enable Bluetooth
systemctl enable bluetooth

# Set root password to '123'
echo "root:123" | chpasswd

# Setup fstab
echo "LABEL=ROOT / ext4 defaults,noatime 0 1" > /etc/fstab
echo "LABEL=BOOT /boot vfat defaults 0 2" >> /etc/fstab

EOF

# Cleanup
echo "Cleaning up..."
sudo rm mnt/usr/bin/qemu-arm-static
sudo umount mnt/boot
sudo umount mnt
sudo losetup -d $LOOP_DEV
rm -rf mnt ArchLinuxARM-armv7-latest.tar.gz

echo "Done! Image created: $IMG_NAME"
