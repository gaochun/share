#!/usr/bin/env python

# Backup the modified files of a commit

import warnings
from optparse import OptionParser
import os

def main():
    parser = OptionParser()
    parser.add_option("-c", "--commit-hash", dest="commitHash", help="hash of commit");
    parser.add_option("-s", "--src-dir", dest="srcDir", help="src directory of project");
    parser.add_option("-d", "--dest-dir", dest="destDir", help="dest directory to backup");
    (options, args) = parser.parse_args();
    
    if options.srcDir is None:
        print("You need to designate src directory of project")
        exit -1
        
    if options.destDir is None:
        print("You need to designate dest directory to backup")
        exit -1
        
    os.chdir(options.srcDir)
    if options.commitHash is None:
        commitHash = os.popen("git log -1 --pretty=\"format:%H\"").readline()
    else:
        commitHash = options.commitHash
        
    files = os.popen("git show --pretty=\"format:\" --name-only " + commitHash).readlines()
    
    backupDir = options.destDir + "/" + commitHash
    if not os.path.isdir(backupDir):
        os.mkdir(backupDir)
    
    for file in files:
        file = str.strip(file)
        if file == "":
            continue
        command = "cp --parent " + file + " " + backupDir
        if os.system(command):
            print "Failed to backup " + file
            print "The command is: " + command
            
    os.system("git format-patch -1 " + commitHash)
    os.system("mv 0001* " + backupDir)
    
if __name__ == '__main__':
    main()
