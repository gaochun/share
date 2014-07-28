# Usage:
# sudo apt-get install hostapd dnsmasq
# cp dnsmasq.conf /etc
# cp hostapd.conf /etc/hostapd
# sudo ./ap.sh

# To stop the ap
# killall hostapd

nmcli nm wifi off
rfkill unblock wlan

iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t nat -A POSTROUTING -s 192.168.0.0/8 -o eth0 -j MASQUERADE
iptables -A FORWARD -s 192.168.0.0/8 -o eth0 -j ACCEPT
iptables -A FORWARD -d 192.168.0.0/8 -m conntrack --ctstate ESTABLISHED,RELATED -i eth0 -j ACCEPT

killall hostapd
ifconfig wlan0 192.168.0.1
hostapd -B /etc/hostapd/hostapd.conf
/etc/init.d/dnsmasq restart
# dnsmasq would modify /etc/resolv.conf
echo "nameserver 10.248.2.5 \nnameserver 10.239.27.228 \nnameserver 172.17.6.9" >> /etc/resolv.conf