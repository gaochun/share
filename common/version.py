from util import *

default_java_file = '/usr/lib/jvm/default-java'
gcc_file = '/usr/bin/gcc'

def handle_option():
    global args

    parser = argparse.ArgumentParser(description = 'Set up the version of Java',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  python %(prog)s -v 1.5
  python %(prog)s -v 1.7.0_45

''')

    parser.add_argument('-s', '--set-version', dest='set_version', help='set version')
    parser.add_argument('-g', '--get', dest='get_version', help='get version', action='store_true')
    parser.add_argument('-t', '--target', dest='target', help='target to set version with', choices=['java', 'gcc'], default='gcc')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

def setup():
    pass

def get_version():
    if not args.get_version:
        return

    if args.target == 'java':
        get_version_java()
    elif args.target == 'gcc':
        get_version_gcc()

def set_version():
    if not args.set_version:
        return

    if args.target == 'java':
        set_version_java()
    elif args.target == 'gcc':
        set_version_gcc()

def get_version_java():
    java_version_result = execute('java -version', silent=True, catch=True)
    match = re.match('java version "(.*)"', java_version_result)
    java_version = match.group(1)

    java_home_result = os.getenv('JAVA_HOME')
    if java_home_result:
        match = re.match('jdk(.*)', java_home_result)
        if match:
            java_home = match.group(1)
        else:
            error('JAVA_HOME is not expected')
    else:
        java_home = 'NULL'

    if os.path.exists(default_java_file):
        default_java_result = execute('ls -l ' + default_java_file, silent=True, catch=True)
        match = re.match('.*jdk(.*)', default_java_result)
        if match:
            default_java = match.group(1)
        else:
            error('default-java is not expected')
    else:
        default_java = 'NULL'

    #info(java_version_result)
    #if java_home_result:
    #    info(java_home_result)
    #if default_java_result:
    #    info(default_java_result)

    info('java -v: ' + java_version)
    info('JAVA_HOME: ' + java_home)
    info('default-java: ' + default_java)

def set_version_java():
    if args.set_version == '1.5':
        version = '1.5.0_22'
    elif args.set_version == '1.6':
        version = '1.6.0_45'
    elif args.set_version == '1.7':
        version = '1.7.0_45'
    else:
        version = args.set_version

    execute('sudo update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/jdk' + version + '/bin/javac 50000')
    execute('sudo update-alternatives --install /usr/bin/java java /usr/lib/jvm/jdk' + version + '/bin/java 50000')
    execute('sudo update-alternatives --install /usr/bin/javaws javaws /usr/lib/jvm/jdk' + version + '/bin/javaws 50000')
    execute('sudo update-alternatives --install /usr/bin/javap javap /usr/lib/jvm/jdk' + version + '/bin/javap 50000')
    execute('sudo update-alternatives --install /usr/bin/jar jar /usr/lib/jvm/jdk' + version + '/bin/jar 50000')
    execute('sudo update-alternatives --install /usr/bin/jarsigner jarsigner /usr/lib/jvm/jdk' + version + '/bin/jarsigner 50000')
    execute('sudo update-alternatives --config javac')
    execute('sudo update-alternatives --config java')
    execute('sudo update-alternatives --config javaws')
    execute('sudo update-alternatives --config javap')
    execute('sudo update-alternatives --config jar')
    execute('sudo update-alternatives --config jarsigner')

    execute('sudo rm -f ' + default_java_file)
    execute('sudo ln -s /usr/lib/jvm/jdk' + version + ' /usr/lib/jvm/default-java')

    get_version_java()

def get_version_gcc():
    gcc_version_result = execute('ls -l ' + gcc_file, silent=True, catch=True)
    match = re.match('.+gcc-(.+)', gcc_version_result)
    if match:
        gcc_version = match.group(1)
    else:
        error('gcc is not expected')

    info('gcc version: ' + gcc_version)

def set_version_gcc():
    version = args.set_version
    execute('sudo rm -f /usr/bin/gcc', silent=True)
    execute('sudo ln -s /usr/bin/gcc-' + version + ' /usr/bin/gcc', silent=True)
    execute('sudo rm -f /usr/bin/g++', silent=True)
    execute('sudo ln -s /usr/bin/g++-' + version + ' /usr/bin/g++', silent=True)
    execute('sudo rm -f /usr/bin/cc', silent=True)
    execute('sudo ln -s /usr/bin/gcc /usr/bin/cc', silent=True)

    get_version_gcc()

if __name__ == "__main__":
    handle_option()
    setup()
    get_version()
    set_version()