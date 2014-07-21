#!/usr/bin/env python

from util import *

# crontab -e
# */30 * * * * python /workspace/project/share/python/server.py

cb_interval = {
    'update_share': 1800,
    'test_x64_all': 24 * 3600,
    'test_x64_aosp_build': 24 * 3600,
}


def setup():
    ensure_dir(dir_server_log)


def update_share():
    backup_dir(dir_share)
    #execute('git reset --hard')
    execute('git pull')
    restore_dir()


def test_x64_all():
    execute('python ' + dir_python + '/test-x64.py --target-arch x86_64,x86')


def test_x64_aosp_build():
    execute('python ' + dir_python + '/test-x64.py --target-arch x86_64,x86 --phase aosp-prebuild,aosp-build --dir-aosp aosp-stable-daily', interactive=True)


def run():
    if host_name == 'wp-01':
        _run_one('update_share')
        _run_one('test_x64_all')

    elif host_name == 'wp-02':
        _run_one('update_share')

    elif host_name == 'wp-03':
        _run_one('update_share')
        # chrome-android build

    elif host_name == 'ubuntu-ygu5-02':
        _run_one('test_x64_aosp_build')


# If callback does not start within interval, start it
def _run_one(cb):
    file_cb = dir_server_log + '/' + cb
    if not os.path.exists(file_cb) or not has_recent_change(file_cb, interval=cb_interval[cb]):
        execute('touch ' + file_cb)
        globals()[cb]()


if __name__ == '__main__':
    lock = open(os.path.realpath(__file__), 'r')
    singleton(lock)
    setup()
    run()
