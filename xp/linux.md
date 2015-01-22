<lamp>
https://help.ubuntu.com/community/ApacheMySQLPHP
sudo apt-get install lamp-server^
</lamp>

<apache>
* server name
echo "ServerName localhost" | sudo tee /etc/apache2/conf-available/fqdn.conf && sudo a2enconf fqdn
or
echo "ServerName localhost" | sudo tee /etc/apache2/conf-available/fqdn.conf
sudo ln -s /etc/apache2/conf-available/fqdn.conf /etc/apache2/conf-enabled/fqdn.conf

* restart
sudo service apache2 restart
or
sudo apache2ctl restart

*
sudo a2ensite browsermark
sudo a2dissite browsermark
sudo service apache2 reload
sudo a2enmod rewrite

* check port
sudo lsof -i:80

</apache>

<php5>
sudo a2enmod php5

</php5>

<mysql>
mysql:
mysql -u root
mysql -u root -p
</mysql>

<browsermark>
* install lamp
* remove webbench/browsermark/browsermark.local/configuration/production.php
* wp-02.sh.intel.com:8001/install
</browsermark>

<zsh>
* ctrl+left/right: move by word
* ctrl+w: clear previous word
</zsh>

<xp>
* add favorite to gnome shell
alacarte->add new item->search it in applications->add as favorite

* desktop file is at /usr/share/applications
* Change command line for chrome
modify /opt/google/chrome-unstable/google-chrome-unstable
--allow-file-access-from-files

* disable apport
gksu gedit /etc/default/apport
Change value of "enabled" from 1 to 0
sudo restart apport

* Qualcomm Atheros AR9462 Wireless Network Adapter
sudo modprobe -rfv ath9k
sudo modprobe -vb ath9k nohwcrypt=1 blink=1 btcoex_enable=1 enable_diversity=1
echo "blacklist acer_wmi" | sudo tee -a /etc/modprobe.d/blacklist.conf
modinfo ath9k
echo "options ath9k nohwcrypt=1 blink=1 btcoex_enable=1" | sudo tee -a /etc/modprobe.d/ath9k.conf

lspci -k |grep -A 3 -i "network"
modinfo ath9k |grep 'depend'

@ no luck with rebuild http://drvbp1.linux-foundation.org/~mcgrof/rel-html/backports/


</xp>