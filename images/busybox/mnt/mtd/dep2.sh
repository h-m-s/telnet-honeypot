#!/bin/sh


cp -f /mnt/mtd/modules/extdrv/h2gether.ko /lib/modules/2.6.24-rt1-hi3520v100/misc/

NET_CHIP_TYPE=`cat "/etc/init.d/NetChip.dat"`
if [ "$NET_CHIP_TYPE" = "1" ] ; then
	modprobe h2gether
else
	modprobe h2gether port_mode=1
fi
modprobe nfs

insmod /mnt/mtd/modules/extdrv/atp862x.ko

PCI_DEV_3520_NA=`grep -i '19e53520' /proc/bus/pci/devices`
if [ "$PCI_DEV_3520_NA" = "" ]; then
    echo "current product used one td3520 device"
    cd /mnt/mtd/modules && ./load_master -s
else
		echo "ddr times reconfig ............................................."
		himm 0x2011003c 0x25;
		#himm 0x2012003c 0x25;
		echo "ddr times end++++++++++++++++++++++"
		
		sleep 3
		
    echo "current product used multi td3520 device"
    cd /mnt/mtd/modules && ./load_pci_host.sh
fi

rm /upgrade/ -rf
rm /mnt/mtd/preupgrade.sh
rm /mnt/mtd/productcheck
telnetd &

export mac=$(cat /etc/init.d/mac.dat)
ifconfig eth0 down
ifconfig eth0 hw ether $mac
ifconfig eth0 up

ifconfig lo up
route add -net 224.0.0.0 netmask 240.0.0.0 dev eth0

mkdir /mnt/backup
mount -t yaffs2 /dev/mtdblock4 /mnt/backup
                                        
cd /mnt/mtd && ./XDVRStart.hisi ./td3520a &
