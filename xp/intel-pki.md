
* git clone git://viggo.jf.intel.com/~roger/intel-pki.git (obselete)
* git clone git://git-amr-4.devtools.intel.com/intel_pki-intel-pki.git intel-pki

1.
./UserRAWS.py
./UserRAWS.py wlan
IDSID: ygu5
domain: CCR
Hostname: ygu5-mobl.ccr.corp.intel.com
FQDN: ygu5-mobl.ccr.corp.intel.com

2. Intel network
In network manager
TSNOfficeWLAN
TLS
Identity:
host/ygu5-mobl1.ccr.corp.intel.com
User Certificate:
/home/gyagp/.cert/machine-cert.argus.pem
CA Certificate:
/home/gyagp/.cert/intel-certchain.crt
Private Key:
/home/gyagp/.cert/priv-key-machine.pem



* vpn
yum install NetworkManager-openconnect
add in network-manager

192.55.54.27
vpn-i-ha01.intel.com
vpn-i-ha02.intel.com

PEM phrase: Iaob
username: yang.gu@intel.com


* connect China VPN
@ openconnect -c ./certificate.p12 --script /etc/vpnc/vpnc-script 192.102.204.72 --cafile ./intel-certchain.crt --key-password-from-fsid
@ via network manager
username: yang.gu@intel.com

gateway: 192.102.204.72
CA Certificate: intel-certchain.crt
User Certificate: certificate.pem
Private key: priv-key.pem
Use FSID for key passphrase



<20130527>
* git clone git://otcgit.jf.intel.com/dwoodhou/intel-pki.git
* vpn from home
./UserRAWS.py
IDSID: ygu5
domain: CCR
Rialto: CCR password
Hostname: ygu5-mobl.ccr.corp.intel.com （ygu5-mobl1.ccr.corp.intel.com）
new private-key password: Iaob****10

* run network.sh to connect to vpn

* wireless in company (optional)
./UserRAWS.py wlan
IDSID: ygu5
domain: CCR
Rialto: CCR password
Hostname: ygu5-mobl.ccr.corp.intel.com
new private-key password: Iaob****10

</20130527>

<xp>
*
network-manager-plugin: git://git.infradead.org/network-manager-openconnect.git

* network manager
sudo apt-get install NetworkManager-openconnect
add in network-manager

192.55.54.27
vpn-i-ha01.intel.com
vpn-i-ha02.intel.com

PEM phrase: Iaob
username: yang.gu@intel.com

TSNOfficeWLAN
TLS
Identity:
host/ygu5-mobl.ccr.corp.intel.com
User Certificate:
/home/gyagp/.cert/machine-cert.argus.pem (or certificate.pem?)
CA Certificate:
/home/gyagp/.cert/intel-certchain.crt
Private Key:
/home/gyagp/.cert/priv-key-machine.pem

Use FSID for key passphrase

copy wpa_supplicant.conf to /etc

* connect China VPN
@ openconnect -c ./certificate.p12 --script /etc/vpnc/vpnc-script 192.102.204.72 --cafile ./intel-certchain.crt --key-password-from-fsid
@ openconnect -c ./certificate.p12 --script /etc/vpnc/vpnc-script 192.55.54.27 --cafile ./intel-certchain.crt --key-password-from-fsid
us: 192.55.54.27
china: 192.102.204.72

* resource
https://opensource.intel.com/linux-wiki/IntelPKI?highlight=%28pki%29
network manager integration: https://opensource.intel.com/linux-wiki/LinuxAnyConnect#head-f277afa339a0a23c601e01d3302570824965e873

</xp>