#!/usr/bin/env python

# Server definition:
# wp-01
# build: x64 daily test
# backup: chrome-android, webcatch archive
# web server (8000): webcatch archive

# wp-02
# build: webcatch
# web server (80): webcatch (android-x86-content_shell, linux_x86_chrome), benchmark

# wp-03
# build: chrome-android
# web server (80): aosp-stable, chrome-android

# wp-04
# build: chromium perf
# web server (80): NA

from util import *

# run with --cron
# set automatic login

interval_cron = 20  # minutes
file_lock = dir_share_ignore_timestamp + '/server'

# unit is second
cb_interval = {
    'update_share': 1800,
    'webcatch_build': 600,

    # default value when no interval is designated
    'default': 24 * 3600 - interval_cron * 60,
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
    add_argument_common(parser)

    args = parser.parse_args()
    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, log, timestamp

    (timestamp, dir_root, log) = setup_common(args, _teardown)
    args.trace = True

    if os.path.exists(file_lock) and has_recent_change(file_lock, interval=24 * 3600):
        info('Server is running')
        exit(0)
    execute('touch ' + file_lock)
    setenv('DISPLAY', ':0')


def cron():
    if not args.cron:
        return

    file_cron = '/var/spool/cron/crontabs/' + username
    result = execute('sudo cat ' + file_cron, return_output=True)

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
        #_run_one('test_x64_all')
        _run_one('test_x64_chromium')

    elif host_name == 'wp-02':
        _run_one('update_share')
        _run_one('update_webbench')
        _run_one('webcatch_build')

    elif host_name == 'wp-03':
        _run_one('update_share')
        _run_one('chrome_android')

    elif host_name == 'wp-04':
        _run_one('update_share')
        _run_one('chromium_perf')

    elif host_name == 'ubuntu-ygu5-01':
        pass

    elif host_name == 'ubuntu-ygu5-02':
        #_run_one('test_x64_aosp_build')
        pass

    elif host_name == 'lorpheux':
        #_run_one('test_x64_chromium')
        pass


def update_share():
    _update_repo(dir_share)


def update_webbench():
    _update_repo(dir_server_webbench)


def test_x64_all():
    return 'test-x64.py --target-arch x86_64,x86'


def test_x64_chromium():
    return 'test-x64.py --target-arch x86_64,x86 --phase chromium-x64'


def test_x64_aosp_build():
    return 'test-x64.py --target-arch x86_64,x86 --phase aosp-prebuild,aosp-build --dir-aosp aosp-stable-daily'


def chromium_perf():
    return 'chromium-perf.py --run'


def chrome_android():
    return 'chrome-android.py --run'


def webcatch_build():
    return 'webcatch/build.py --target-os android --target-arch x86,x86_64 --target-module chrome_shell,webview_shell --rev 297098-999999 --build'


# If callback does not start within interval, start it
def _run_one(cb):
    file_cb = dir_share_ignore_timestamp + '/' + cb
    if cb in cb_interval:
        interval = cb_interval[cb]
    else:
        interval = cb_interval['default']

    if not os.path.exists(file_cb) or not has_recent_change(file_cb, interval=interval):
        execute('touch ' + file_cb)
        cmd = globals()[cb]()
        if cmd:
            cmd = 'python ' + dir_share_python + '/' + cmd
            cmd = suffix_cmd(cmd, args, log)
            execute(cmd, interactive=True)


def _update_repo(dir_repo):
    backup_dir(dir_repo)
    #execute('git reset --hard')
    execute('git pull')
    restore_dir()


def _teardown():
    execute('rm -f %s' % file_lock)


if __name__ == '__main__':
    parse_arg()
    setup()
    cron()
    start()
