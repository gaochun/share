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
/etc/apache2/ports.conf, add "Listen 8001"
sudo ln -s /workspace/server/webbench/browsermark/browsermark.conf sites-available/etc/apache2/sites-available/browsermark.conf
sudo ln -s /workspace/server/webbench/browsermark/000-default.conf sites-available/etc/apache2/sites-available/000-default.conf
</browsermark>