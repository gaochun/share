from util import *


def parse_arg():
    global args
    parser = argparse.ArgumentParser(description='Script to upgrade system',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
Examples:
  python %(prog)s
  python %(prog)s -t basic
  python %(prog)s -t system
''')
    parser.add_argument('-t', '--type', dest='type', help='type to upgrade', choices=['basic', 'system'])
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    set_proxy()
    execute('echo \'Acquire::http::proxy "http://127.0.0.1:8118";\' >apt.conf', show_cmd=False)
    execute('sudo mv apt.conf /etc/apt/', show_cmd=False)
    execute('echo \'deb https://dl.google.com/linux/chrome/deb/ stable main\' >google.list', show_cmd=False)
    execute('sudo mv google.list /etc/apt/sources.list.d/', show_cmd=False)


def upgrade():
    if args.type == 'basic':
        execute('sudo apt-get update && sudo apt-get -y dist-upgrade', interactive=True)
    elif args.type == 'system':
        execute('sudo update-manager -d', interactive=True)


if __name__ == "__main__":
    parse_arg()
    setup()
    upgrade()
