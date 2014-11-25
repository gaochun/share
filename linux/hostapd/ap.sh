#!/bin/sh

# Usage:
# sudo apt-get install hostapd dnsmasq
# cp dnsmasq.conf /etc
# cp hostapd.conf /etc/hostapd
# uncomment net.ipv4.ip_forward=1 in /etc/sysctl.conf
# sudo ./ap.sh

killall hostapd
hostname=$(hostname)

if [ $hostname = "wp-01" ] ; then
    EXTERNAL=eth1
elif [ $hostname = "ubuntu-ygu5-01" ] ; then
    EXTERNAL=eth2
fi

nmcli nm wifi off
rfkill unblock wlan
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t nat -A POSTROUTING -s 192.168.0.0/8 -o $EXTERNAL -j MASQUERADE
iptables -A FORWARD -s 192.168.0.0/8 -o $EXTERNAL -j ACCEPT
iptables -A FORWARD -d 192.168.0.0/8 -m conntrack --ctstate ESTABLISHED,RELATED -i $EXTERNAL -j ACCEPT

ifconfig wlan0 192.168.0.1
hostapd -B /etc/hostapd/hostapd.conf
/etc/init.d/dnsmasq restart
# dnsmasq would modify /etc/resolv.conf
echo "nameserver 10.248.2.5 \nnameserver 10.239.27.228 \nnameserver 172.17.6.9" >> /etc/resolv.conf