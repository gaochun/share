#!/usr/bin/env python

from util import *

# crontab -e
# */30 * * * * python /workspace/project/share/python/server.py

cb_interval = {
    'update_share': 1800,
    'test_x64': 24 * 3600,
}


def setup():
    ensure_dir(dir_server_log)


def update_share():
    backup_dir(dir_share)
    #execute('git reset --hard')
    execute('git pull')
    restore_dir()


def test_x64():
    execute('python ' + dir_python + '/test-x64.py --target-arch x86_64,x86')


def run():
    while True:
        cb = 'update_share'
        _run_one(cb, cb_interval[cb])

        if host_name == 'wp-01':
            cb = 'test_x64'
            _run_one(cb, cb_interval[cb])

        elif host_name == 'wp-02':
            pass

        elif host_name == 'wp-03':
            # chrome-android build
            pass

        time.sleep(1800)


# If callback does not start within interval, start it
def _run_one(cb, interval):
    file_cb = dir_server_log + '/' + cb
    if not os.path.exists(file_cb):
        execute('touch ' + file_cb)
        globals()[cb]()

    if not has_recent_change(file_cb, interval=interval):
        globals()[cb]()


if __name__ == '__main__':
    lock = open(os.path.realpath(__file__), 'r')
    singleton(lock)
    setup()
    run()
