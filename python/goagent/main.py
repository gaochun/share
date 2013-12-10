#! N:\Python27\python.exe

import urllib2;
import re;
from optparse import OptionParser;
import os;
import commands;

debug = 0; # if or not use local 
rootDir = "e:/topic/gfw/goagent";

def getURL():
    parser = OptionParser()
    parser.add_option("-f", "--file-url", dest="fileURL", help="assign the file URL");
    (options, args) = parser.parse_args();
    
    if options.fileURL:
        url = options.fileURL;
    else:
        global debug;   
        if debug:
            file = open('download.htm')
            html = file.read();
        else:
            webURL = "https://code.google.com/p/goagent/downloads/list";
            proxy = urllib2.ProxyHandler({'https': '127.0.0.1:8087'});
            opener = urllib2.build_opener(proxy);
            urllib2.install_opener(opener);
            u = urllib2.urlopen(webURL);
            html = u.read();

        urls = re.findall(r"goagent.googlecode.com.*?7z", html, re.I)
        url = "https://" + urls[0];
    
    print "The new goagent is " + url;
    return url;    

def downloadFile(url):
    f = urllib2.urlopen(url);
    data = f.read();
    with open(rootDir + "/latest.7z", "wb") as code:
        code.write(data) 

def rmDir(pattern, dir):
    files = os.listdir(dir);
    for file in files:
        p = re.compile(pattern, re.I)
        if p.search(file) and os.path.isdir(file):
            command = "rmdir /S /Q " + file;
            os.system(command);
        
        
def useFile():
    # kill goagent process
    command = 'taskkill /F /IM  goagent.exe /T';
    os.system(command);
    
    os.chdir(rootDir);
    
    # delete latest_old
    if os.path.exists("latest_old"):
        command = "rmdir /S /Q latest_old";
        os.system(command);
        
    # rename latest as latest_old    
    if os.path.exists("latest"):    
        os.rename("latest", "latest_old");
    
    # delete goagent* directory
    rmDir("goagent", rootDir);

    # extract new one
    command = "\"\"%ProgramFiles%/winrar/winrar.exe\"\" x -ibck latest.7z";
    os.system(command);
    
    # rename new one to latest
    pattern = "goagent"
    files = os.listdir("./");
    for file in files:
        p = re.compile(pattern, re.I)
        if p.search(file) and os.path.isdir(file):
            os.rename(file, "latest");
    
    # modify proxy.ini
    path = "latest/local/proxy.ini";
    f = open(path);
    lines = f.readlines();
    f.close();
    
    f = open(path, "w");
    p = re.compile("appid", re.I);
    for line in lines:
        if p.search(line):
            f.write("appid = goagent-gyagp\n");
        else:
            f.write(line);
    f.close();

    # start the process
    os.execl(rootDir + "/latest/local/goagent.exe", "/silent")
    

if __name__ == "__main__":
    url = getURL();
    downloadFile(url);   
    useFile();
