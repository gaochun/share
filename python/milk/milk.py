#! N:\Python27\python.exe
# -*- coding: utf-8 -*- 

# Usage: need to add password for gmail

import re
import urllib2
from httplib import BadStatusLine
import time
import os
import sys

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


URL = 'http://www.boots.com/en/Aptamil-Growing-up-milk-powder-900g_847056'

def get_time():
	return time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
                
def check():
    in_stock = False

    try:
        useragent = 'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Ubuntu/10.04 Chromium/6.0.472.62 Chrome/6.0.472.62 Safari/534.3)'
        request = urllib2.Request(URL)
        request.add_header('User-agent', useragent)
        u = urllib2.urlopen(request)
    except BadStatusLine:
        print "Check failed"
        return
    html = u.read()
    
    m = re.search('out of stock', html)
    
    if not m:
        in_stock = True
        send_mail()
        
    os.chdir(sys.path[0])
    f = open('history.txt', 'a')
    f.write(get_time() + ' ' + str(in_stock) + '\n')
    f.close() 

def send_mail():
    gmail_user = 'gyagp0@gmail.com'
    gmail_password = ''
    recipient = 'gyagp0@gmail.com;janetyeye@gmail.com'
    #recipient = 'gyagp0@gmail.com'
    
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = recipient
    msg['Subject'] = 'Milk Powder Arrived'
    msg.attach(MIMEText(URL))
    
    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_password)
    mailServer.sendmail(gmail_user, recipient, msg.as_string())
    mailServer.close()

def sleep(seconds):
    print 'Wait ' + str(seconds) + ' seconds and quit...'
    time.sleep(seconds)

if __name__ == "__main__":
    check()
    #sleep(5)

