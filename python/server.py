#!/usr/bin/env python

# Server definition:
# wp-01
# build: x64 daily test, webcatch
# backup: chrome-android, webcatch archive
# web server: benchmark

# wp-02
# build: webcatch
# web server: webcatch (android-x86-content_shell, linux_x86_chrome)

# wp-03
# build: chrome-android, webcatch
# web server: aosp-stable, chrome-android

from util import *

# run with --cron
# set automatic login

interval_cron = 20  # minutes

cb_interval = {
    'update_share': 1800,
    'test_x64_all': 24 * 3600 - interval_cron * 60,
    'test_x64_aosp_build': 24 * 3600 - interval_cron * 60,
    'chrome_android': 3600,
    'daemon': 1200,
}


def parse_arg():
    global args

    parser = argparse.ArgumentParser(description='Script to control server',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --cron
''')

    parser.add_argument('--cron', dest='cron', help='cron', action='store_true')
    parser.add_argument('--start', dest='start', help='start', action='store_true')

    args = parser.parse_args()
    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    ensure_dir(dir_server_log)
    setenv('DISPLAY', ':0')


def cron():
    if not args.cron:
        return

    file_cron = '/var/spool/cron/crontabs/' + username
    result = execute('sudo cat ' + file_cron, return_output=True)
    print result[1]
    if re.search('server.py', result[1]):
        info('server.py has been added to cron jobs')
    else:
        execute('sudo cp ' + file_cron + ' /tmp/temp', interactive=True)
        execute('sudo chmod 777 /tmp/temp', interactive=True)
        execute('sudo echo "*/%s * * * * python /workspace/project/share/python/server.py --start" >> /tmp/temp' % interval_cron, interactive=True)
        execute('sudo chmod 600 /tmp/temp', interactive=True)
        execute('sudo mv /tmp/temp ' + file_cron, interactive=True)


def start():
    if not args.start:
        return

    if host_name == 'wp-01':
        _run_one('update_share')
        _run_one('test_x64_all')

    elif host_name == 'wp-02':
        _run_one('update_share')

    elif host_name == 'wp-03':
        _run_one('update_share')
        _run_one('chrome_android')

    elif host_name == 'ubuntu-ygu5-01':
        pass

    elif host_name == 'ubuntu-ygu5-02':
        _run_one('test_x64_aosp_build')


def update_share():
    backup_dir(dir_share)
    #execute('git reset --hard')
    execute('git pull')
    restore_dir()


def test_x64_all():
    return 'test-x64.py --target-arch x86_64,x86'


def test_x64_aosp_build():
    return 'test-x64.py --target-arch x86_64,x86 --phase aosp-prebuild,aosp-build --dir-aosp aosp-stable-daily'


def chrome_android():
    return 'chrome-android.py --run'


def daemon():
    if device_connected():
        android_tap()
    return ''


# If callback does not start within interval, start it
def _run_one(cb):
    file_cb = dir_server_log + '/' + cb
    if not os.path.exists(file_cb) or not has_recent_change(file_cb, interval=cb_interval[cb]):
        execute('touch ' + file_cb)
        cmd = globals()[cb]()
        if cmd != '':
            cmd = 'python ' + dir_python + '/' + cmd + ' 2>&1 >' + dir_server_log + '/' + cb + '.log'
            execute(cmd)


if __name__ == '__main__':
    _run_one('daemon')
    lock = open(os.path.realpath(__file__), 'r')
    singleton(lock)
    parse_arg()
    setup()
    cron()
    start()
