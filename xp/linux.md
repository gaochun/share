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

</xp>