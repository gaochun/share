#/usr/bin/python

import os
import commands
from optparse import OptionParser
import platform
import re

# Global variables
rootDir = ''
system = platform.system()

def isSystem(name):
    if system == name:
        return True
    else:
        return False
        
def isWindows():
    if isSystem('Windows'):
        return True
    else:
        return False

def isLinux():
    if isSystem('Linux'):
        return True
    else:
        return False
        
def info(msg):
    print "[INFO] " + msg + "."

def error(msg):
    print "[ERROR] " + msg + "!"
    
def update(options):
    if not options.update:
        return()
    
    os.system('./Tools/Scripts/update-webkit --' + options.port)
    
def build(options):   
    if not options.build:
        return()
    
    if options.buildType == '':
        return()
    
    if options.buildType.upper() == "DEBUG":
        buildType = "Debug"
    elif options.buildType.upper() == "RELEASE":
        buildType = "Release"
    elif options.buildType.upper() == "ALL":
        buildType = "All"
    
    print "== Build Environment =="
    print "Directory of src: " + rootDir
    print "Build type: " + buildType
    print "Build system: Ninja"
    print "System: " + system
    print "======================="

    if buildType == "Debug" or buildType == "All":
        os.system('./Tools/Scripts/build-webkit --debug -- makeargs=-j8 --' + options.port)

    if buildType == "Release" or buildType == "All":
        os.system('./Tools/Scripts/build-webkit --release -- makeargs=-j8 --' + options.port)
    
# override format_epilog to make it format better
OptionParser.format_epilog = lambda self, formatter: self.epilog

if __name__ == "__main__":
    # System sanity check
    if not isWindows() and not isLinux():
        error('Current system is not suppported')
        quit()
        
    # Handle options
    parser = OptionParser(description='Description: Script to sync and build Chromium',
                          epilog="""
Examples:
  python webkit_build.py -u True
  python chromium_build.py -t release
""")
    parser.add_option("-p", "--port", dest="port", help="Designate the WebKit port", default='chromium')
    parser.add_option("-u", "--update", action='store_true', dest="update", help="need update", default=False)
    parser.add_option("-b", "--build", dest="build", help="need build", default=True)
    parser.add_option("-d", "--root-dir", dest="rootDir", help="assign root directory of WebKit", metavar="ROOTDIR", default='')
    parser.add_option("-t", "--build-type", dest="buildType", help="assign the build type", metavar="DEBUG|RELEASE|ALL", default='release')
    (options, args) = parser.parse_args()

    # Global variables
    if options.rootDir == '':
        if isWindows():
            rootDir = "d:/user/ygu5/project/WebKit"
        else:
            rootDir = "/workspace/project/WebKit"
    else:
        rootDir = options.rootDir

    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')
    
    if isWindows():
        path = os.getenv("PATH")
        p = re.compile('depot_tools')
        if not p.search(path):
            path = "d:\user\ygu5\project\chromium\depot_tools;" + path
            os.putenv("PATH", path)        
    
    if isWindows():
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"')
        os.putenv("GYP_MSVS_VERSION", "2010e")
        os.putenv("GYP_MSVS_OVERRIDE_PATH", "d:/user/ygu5/project/chromium/win_toolchain")
        os.putenv("WDK_DIR", "d:/user/ygu5/project/chromium/win_toolchain/WDK")
        os.putenv("DXSDK_DIR", "d:/user/ygu5/project/chromium/win_toolchain/DXSDK")
        os.putenv("WindowsSDKDir", "d:/user/ygu5/project/chromium/win_toolchain/win8sdk")
    else:
        os.putenv("GYP_DEFINES", "werror=")
        
    # Real work
    os.chdir(rootDir)
    update(options)
    build(options)
    
