#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import platform
import sys
import datetime
import argparse
import subprocess
import logging
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socket
import inspect
import multiprocessing
import re
import commands
import fileinput
import random
import select

reload(sys)
sys.setdefaultencoding('utf-8')

host_os = platform.system().lower()
host_name = socket.gethostname()
username = os.getenv('USER')
number_cpu = str(multiprocessing.cpu_count() * 2)
args = argparse.Namespace()
dir_stack = []
timer = {}

# servers that webcatch can build on
servers_webcatch = [
    'wp-02',
    'wp-03',
]
# main server for webcatch
server_webcatch = servers_webcatch[0]

target_arch_index = {'x86': 0, 'arm': 1, 'x86_64': 2, 'arm64': 3}
target_arch_strip = {
    'x86': 'i686-linux-android-strip',
    'arm': 'arm-linux-androideabi-strip',
}

target_os_all = ['android', 'linux']
target_arch_all = ['x86', 'arm', 'x86_64']
target_arch_chrome_android = target_arch_all[0:2]
target_arch_info = {
    'x86': ['x86'],
    'arm': ['armeabi-v7a'],
    'x86_64': ['x86_64'],
}
TARGET_ARCH_INFO_INDEX_ABI = 0

target_module_all = ['webview', 'chrome', 'content_shell', 'chrome_stable', 'chrome_beta', 'webview_shell', 'chrome_shell', 'stock_browser']


# <path>
def _get_real_dir(path):
    return os.path.split(os.path.realpath(path))[0]
dir_temp = _get_real_dir(__file__)
while not os.path.exists(dir_temp + '/.git'):
    dir_temp = _get_real_dir(dir_temp)
dir_share = dir_temp
dir_python = dir_share + '/python'
dir_webcatch = dir_python + '/webcatch'
dir_webmark = dir_python + '/webmark'
dir_linux = dir_share + '/linux'
dir_common = dir_share + '/common'
file_chromium = dir_python + '/chromium.py'
file_aosp = dir_python + '/aosp.py'
file_webmark = dir_webmark + '/webmark.py'
python_chromium = 'python ' + file_chromium
python_aosp = 'python ' + file_aosp
python_webmark = 'python ' + file_webmark

dir_workspace = '/workspace'
dir_server = dir_workspace + '/server'
dir_server_aosp = dir_server + '/aosp'
dir_server_chromium = dir_server + '/chromium'
dir_server_chrome_android_todo = dir_server_chromium + '/android-chrome-todo'
dir_server_log = dir_server + '/log'
dir_project = dir_workspace + '/project'
dir_project_chrome_android = dir_project + '/chrome-android'
dir_project_webcatch = dir_project + '/webcatch'
dir_project_webcatch_out = dir_project_webcatch + '/out'
dir_project_webcatch_project = dir_project_webcatch + '/project'
dir_project_webcatch_log = dir_project_webcatch + '/log'
dir_tool = dir_workspace + '/tool'

path_web_chrome_android = 'http://wp-03.sh.intel.com/chromium'
path_web_webcatch = 'http://wp-02.sh.intel.com/chromium'
path_server_backup = '//wp-01/backup'

dir_home = os.getenv('HOME')
# </path>

# <chromium>
chromium_rev_max = 9999999

# src/build/android/pylib/constants.py
chromium_android_info = {
    'chrome_stable': ['com.android.chrome', ''],
    'chrome_beta': ['com.chrome.beta', ''],
    'chrome_example': ['com.example.chromium', 'com.google.android.apps.chrome.Main'],
    'chrome_example_stable': ['com.chromium.stable', 'com.google.android.apps.chrome.Main'],
    'chrome_example_beta': ['com.chromium.beta', 'com.google.android.apps.chrome.Main'],
    'content_shell': ['org.chromium.content_shell_apk', ''],
    #'webview_shell': 'com.android.webview_shell_apk?',
    'stock_browser': ['com.android.browser', 'com.android.browser.BrowserActivity'],
}
CHROMIUM_ANDROID_INFO_INDEX_PKG = 0
CHROMIUM_ANDROID_INFO_INDEX_ACT = 1

# Each chromium version is: major.minor.build.patch
# major -> svn rev, git commit, build. major commit is after build commit.
# To get this, search 'The atomic number' in 'git log origin master chrome/VERSION'
chromium_majorver_info = {
    38: [278979, '85c11da0bf7aad87c0a563c7093cb52ee58e4666', 2063],
    37: [269579, '47c9991b3153128d79eac26ad0e8ecb3d7e21128', 1986],
    36: [260368, 'b1f8bdb570beade2a212e69bee1ea7340d80838e', 1917],
    35: [252136, '6d5ba2122914c53d753e5fb960a601b43cb79c60', 1848],
    34: [241271, '3824512f1312ec4260ad0b8bf372619c7168ef6b', 1751],
    33: [233137, 'eeaecf1bb1c52d4b9b56a620cc5119409d1ecb7b', 1701],
    32: [225138, '6a384c4afe48337237e3da81ccff8658755e2a02', 1652],
    31: [217377, 'c95dd877deb939ec7b064831c2d20d92e93a4775', 1600],
    30: [208581, '88367e9bf6a10b9e024ec99f12755b6f626bbe0c', 1548],
}
CHROMIUM_MAJORVER_INFO_INDEX_REV = 0

# revision range to care about
chromium_rev_default = [chromium_majorver_info[36][CHROMIUM_MAJORVER_INFO_INDEX_REV], 999999]
# </chromium>


def info(msg):
    print "[INFO] " + msg + "."


def warning(msg):
    print '[WARNING] ' + msg + '.'


def error(msg, abort=True, error_code=1):
    print "[ERROR] " + msg + "!"
    if abort:
        quit(error_code)


def cmd(msg):
    print '[COMMAND] ' + msg


# Used for debug, so that it can be cleaned up easily
def debug(msg):
    print '[DEBUG] ' + msg


def get_datetime(format='%Y%m%d%H%M%S'):
    return time.strftime(format, time.localtime())


# get seconds since 1970-01-01
def get_epoch_second():
    return int(time.time())


def has_recent_change(path_file, interval=24 * 3600):
    if get_epoch_second() - os.path.getmtime(path_file) < interval:
        return True
    else:
        return False


# TODO: The interactive solution doesn't use subprocess now, which can not support show_progress and return_output now.
# show_cmd: Print command if Ture. Default to True.
# show_duration: Report duration to execute command if True. Default to False.
# show_progress: print stdout and stderr to console if True. Default to False.
# return_output: Put stdout and stderr in result if True. Default to False.
# dryrun: Do not actually run command if True. Default to False.
# abort: Quit after execution failed if True. Default to False.
# file_log: Print stderr to log file if existed. Default to ''.
# interactive: Need user's input if true. Default to False.
def execute(command, show_cmd=True, show_duration=False, show_progress=False, return_output=False, dryrun=False, abort=False, file_log='', interactive=False):
    if show_cmd:
        cmd(command)

    if dryrun:
        return [0, '']

    start_time = datetime.datetime.now().replace(microsecond=0)

    if interactive:
        ret = os.system(command)
        result = [ret / 256, '']
    else:
        out_temp = ''
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while show_progress:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            out_temp += nextline
            sys.stdout.write(nextline)
            sys.stdout.flush()

        (out, err) = process.communicate()
        out = out_temp + out
        ret = process.returncode

        if return_output:
            result = [ret, out + err]
        else:
            result = [ret, '']

    if file_log:
        os.system('echo ' + err + ' >>' + file_log)

    end_time = datetime.datetime.now().replace(microsecond=0)
    time_diff = end_time - start_time

    if show_duration:
        info(str(time_diff) + ' was spent to execute following command: ' + command)

    if abort and result[0]:
        error('Failed to execute', error_code=result[0])

    return result


def bashify_cmd(cmd):
    return 'bash -c "' + cmd + '"'


# Patch command if it needs to run on server
def remotify_cmd(cmd, server):
    if re.match('ubuntu', server):
        username = 'gyagp'
    else:
        username = 'wp'

    return 'ssh %s@%s %s' % (username, server, cmd)


def has_process(name):
    r = os.popen('ps auxf |grep -c ' + name)
    count = int(r.read())
    if count == 2:
        return False

    return True


def shell_source(shell_cmd, use_bash=False):
    if use_bash:
        cmd = bashify_cmd('. ' + shell_cmd + '; env')
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    else:
        pipe = subprocess.Popen('. %s; env' % shell_cmd, stdout=subprocess.PIPE, shell=True)
    output = pipe.communicate()[0]
    for line in output.splitlines():
        (key, _, value) = line.partition("=")
        os.environ[key] = value


# Get the dir of symbolic link, for example: /workspace/project/chromium-android instead of /workspace/project/gyagp/share/python
def get_symbolic_link_dir():
    if sys.argv[0][0] == '/':  # Absolute path
        script_path = sys.argv[0]
    else:
        script_path = os.getcwd() + '/' + sys.argv[0]
    return os.path.split(script_path)[0]


def backup_dir(dir_new, verbose=False):
    global dir_stack
    dir_stack.append(os.getcwd())
    os.chdir(dir_new)
    if verbose:
        info('Switched to ' + dir_new)


def restore_dir(verbose=False):
    global dir_stack
    dir_old = dir_stack.pop()
    os.chdir(dir_old)
    if verbose:
        info('Switched to ' + dir_old)


def package_installed(pkg):
    result = execute('dpkg -s ' + pkg, show_cmd=False)
    if result[0]:
        return False
    else:
        return True


# To send email on Ubuntu, you may need to install smtp server, such as postfix.
# type: type of content, can be plain or html
def send_mail(sender, to, subject, content, type='plain'):
    if not package_installed('postfix'):
        warning('Email can not be sent as postfix is not installed')
        return

    # Ensure to is a list
    if isinstance(to, str):
        to = [to]

    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['To'] = ','.join(to)
    msg['Subject'] = subject
    msg.attach(MIMEText(content, type))

    try:
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(sender, to, msg.as_string())
        print msg.as_string()
        info('Email was sent successfully')
    except Exception:
        error('Failed to send mail at ' + host_name, abort=False)
    finally:
        smtp.quit()


# upload file to specified samba server
def backup_smb(server, dir_server, file_local, dryrun=False):
    result = execute('smbclient %s -N -c "prompt; recurse; cd %s; mput %s"' % (server, dir_server, file_local), interactive=True, dryrun=dryrun)
    if result[0]:
        warning('Failed to upload: ' + file_local)
    else:
        info('Succeeded to upload: ' + file_local)


def set_path(path_extra=''):
    path = os.getenv('PATH')
    if host_os == 'windows':
        splitter = ';'
    elif host_os == 'linux':
        splitter = ':'

    paths = path.split(splitter)

    if host_os == 'linux':
        paths_new = ['/usr/bin', '/usr/sbin', '/workspace/project/depot_tools']

    if path_extra:
        paths_new.extend(path_extra.split(splitter))

    for path_new in paths_new:
        if path_new not in paths:
            paths.append(path_new)

    setenv('PATH', splitter.join(paths))


def getenv(env):
    return os.getenv(env)


def setenv(env, value):
    if value:
        os.environ[env] = value


def unsetenv(env):
    if env in os.environ:
        del os.environ[env]


def set_proxy():
    if start_privoxy():
        http_proxy = '127.0.0.1:8118'
        https_proxy = '127.0.0.1:8118'
    else:
        http_proxy = 'proxy-shz.intel.com:911'
        https_proxy = 'proxy-shz.intel.com:911'
    setenv('http_proxy', http_proxy)
    setenv('https_proxy', https_proxy)
    setenv('no_proxy', '127.0.0.1,intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,127.0.0.0/8,134.134.0.0/16,172.16.0.0/20,192.168.42.0/16,10.239.*.*,ubuntu-ygu5-*,wp-*')


def start_privoxy():
    if has_process('privoxy'):
        return True

    if os.path.exists('/usr/sbin/privoxy'):
        result = execute('sudo privoxy /etc/privoxy/config')
        if result[0]:
            return False
        else:
            return True
    else:
        return False


def stop_prixoxy():
    if has_process('privoxy'):
        execute('sudo killall privoxy')


# Setup devices and their names
def setup_device(devices_limit=[]):
    devices = []
    devices_name = []
    devices_type = []
    devices_mode = []
    devices_target_arch = []
    cmd = adb('devices -l')
    device_lines = commands.getoutput(cmd).split('\n')
    cmd = 'fastboot devices -l'
    device_lines += commands.getoutput(cmd).split('\n')

    pattern_system = re.compile('device:(.*)')
    pattern_fastboot = re.compile('(\S+)\s+fastboot')
    pattern_nofastboot = re.compile('fastboot: not found')
    for device_line in device_lines:
        if re.match('List of devices attached', device_line):
            continue
        elif re.match('^\s*$', device_line):
            continue

        match = pattern_system.search(device_line)
        if match:
            device = device_line.split(' ')[0]
            devices.append(device)
            device_name = match.group(1)
            devices_name.append(device_name)
            if re.search('192.168.42.1', device):
                devices_type.append('baytrail')
            elif re.search('emulator', device):
                devices_type.append('generic')
            devices_mode.append('system')

        match = pattern_nofastboot.search(device_line)
        if match:
            continue

        match = pattern_fastboot.search(device_line)
        if match:
            device = match.group(1)
            devices.append(device)
            devices_name.append('')
            devices_type.append('')
            devices_mode.append('fastboot')

    if devices_limit:
        # This has to be reversed and deleted from end
        for index, device in reversed(list(enumerate(devices))):
            if device not in devices_limit:
                del devices[index]
                del devices_name[index]
                del devices_type[index]
                del devices_mode[index]

    for index, device in enumerate(devices):
        if devices_mode[index] == 'fastboot':
            devices_target_arch = ''
        else:
            devices_target_arch.append(android_get_target_arch(device=device))

    return (devices, devices_name, devices_type, devices_target_arch, devices_mode)


def timer_start(tag):
    if tag not in timer:
        timer[tag] = [0, 0]
    timer[tag][0] = datetime.datetime.now().replace(microsecond=0)


def timer_stop(tag):
    timer[tag][1] = datetime.datetime.now().replace(microsecond=0)


def timer_diff(tag):
    if tag in timer:
        return str(timer[tag][1] - timer[tag][0])
    else:
        return '0:00:00'


def get_caller_name():
    return inspect.stack()[1][3]


def adb(cmd, device=''):
    # some commands do not need -s option
    cmds_none = ['devices', 'connect', 'disconnect']
    if device == '':
        for cmd_none in cmds_none:
            if re.search(cmd_none, cmd):
                device = None
                break
    if device == '':
        device = '192.168.42.1:5555'

    if device is None:
        return 'adb ' + cmd
    return 'adb -s ' + device + ' ' + cmd


# Execute a adb shell command and know the return value
# adb shell would always return 0, so a trick has to be used here to get return value
def execute_adb_shell(cmd, device=''):
    cmd_adb = adb(cmd='shell "' + cmd + ' || echo FAIL"', device=device)
    result = execute(cmd_adb, return_output=True, show_cmd=False)
    if re.search('FAIL', result[1].rstrip('\n')):
        return False
    else:
        return True


def get_product(arch, device_type, date=20140101):
    if device_type == 'generic':
        product = device_type + '_' + arch
    elif device_type == 'baytrail':
        if date >= 20140624:
            product_prefix = 'asus_t100'
        else:
            product_prefix = device_type

        if arch == 'x86_64':
            product = product_prefix + '_64p'
        elif arch == 'x86':
            product = product_prefix

    return product


# device: specific device. Do not use :5555 as -t option does not accept this.
# mode: system for normal mode, bootloader for bootloader mode
def device_connected(device='', mode='system'):
    if mode == 'system':
        result = execute('timeout 1s ' + adb(cmd='shell \ls', device=device))
    elif mode == 'bootloader':
        if device == '192.168.42.1:5555':
            device = '192.168.42.1'
        if device == '192.168.42.1':
            option = '-t'
        else:
            option = '-s'
        path_fastboot = dir_linux + '/fastboot'
        result = execute('timeout 1s %s %s %s getvar all' % (path_fastboot, option, device))

    if result[0]:
        return False
    else:
        return True


# Try to connect to device in case it's not online
def connect_device(device='', mode='system'):
    if mode == 'system':
        if device_connected(device, mode):
            return True
        if device == '':
            device = '192.168.42.1:5555'
        if device == '192.168.42.1:5555':
            cmd = 'timeout 1s ' + adb(cmd='disconnect %s' % device) + ' && timeout 1s ' + adb(cmd='connect %s' % device)
            execute(cmd, interactive=True)
        return device_connected(device, mode)
    elif mode == 'bootloader':
        if device == '192.168.42.1:5555':
            device = '192.168.42.1'
        return device_connected(device, mode)


def analyze_issue(dir_aosp='/workspace/project/aosp-stable', dir_chromium='/workspace/project/chromium-android', arch='x86_64', device='', type='tombstone', date=20140101):
    if device == '' or device == '192.168.42.1:5555':
        device_type = 'baytrail'
    product = get_product(arch, device_type, date)
    if arch == 'x86_64':
        arch_str = '64'
    else:
        arch_str = ''

    dirs = [
        dir_aosp + '/out/target/product/%s/symbols/system/lib%s' % (product, arch_str),
        dir_chromium + '/src/out-%s/out/Release/lib' % arch,
    ]

    connect_device(device=device)

    count_line_max = 1000
    count_valid_max = 40

    if type == 'tombstone':
        result = execute(adb(cmd='shell \ls /data/tombstones'), return_output=True)
        files = result[1].split('\n')
        file_name = files[-2].strip()
        info('Start to analyze ' + file_name)
        execute(adb(cmd='pull /data/tombstones/' + file_name + ' /tmp/'))
        result = execute('cat /tmp/' + file_name, return_output=True)
        lines = result[1].split('\n')
    elif type == 'anr':
        execute(adb(cmd='pull /data/anr/traces.txt /tmp/'))
        result = execute('cat /tmp/traces.txt', return_output=True)
        lines = result[1].split('\n')

    pattern = re.compile('pc (.*)  .*lib(.*)\.so')
    count_line = 0
    count_valid = 0
    for line in lines:
        count_line += 1
        if count_line > count_line_max:
            break
        match = pattern.search(line)
        if match:
            print line
            name = match.group(2)
            for dir in dirs:
                path = dir + '/lib%s.so' % name
                if not os.path.exists(path):
                    continue
                cmd = dir_linux + '/x86_64-linux-android-addr2line -C -e %s -f %s' % (path, match.group(1))
                result = execute(cmd, return_output=True, show_cmd=False)
                print result[1]

                count_valid += 1
                if count_valid >= count_valid_max:
                    return

                break


# is_sylk: If true, just copy as a symbolic link
def copy_file(file_src, dir_dest, is_sylk=False):
    if not os.path.exists(file_src):
        warning(file_src + ' does not exist')
        return

    file_name = file_src.split('/')[-1]
    file_dest = dir_dest + '/' + file_name
    if os.path.islink(file_dest) and os.readlink(file_dest) == file_src:
        return

    if re.search(dir_home, dir_dest) or re.search(dir_workspace, dir_dest):
        need_sudo = False
    else:
        need_sudo = True

    file_dest_bk = file_dest + '.bk'
    if os.path.exists(file_dest) and not os.path.exists(file_dest_bk):
        cmd = 'mv ' + file_dest + ' ' + file_dest_bk
        if need_sudo:
            cmd = 'sudo ' + cmd
        execute(cmd)

    if not os.path.exists(dir_dest):
        execute('mkdir -p ' + dir_dest)

    backup_dir(dir_dest)
    if is_sylk:
        cmd = 'ln -s ' + file_src + ' .'
    else:
        cmd = 'cp -f ' + file_src + ' ' + dir_dest

    if need_sudo:
        cmd = 'sudo ' + cmd
    execute(cmd)
    restore_dir()


def apply_patch(patches, dir_patches):
    for dir_repo in patches:
        if not os.path.exists(dir_repo):
            error(dir_repo + ' does not exist')

        for patch in patches[dir_repo]:
            path_patch = dir_patches + '/' + patch
            if _patch_applied(dir_repo, path_patch):
                info('Patch ' + patch + ' was applied before, so is just skipped here')
            else:
                backup_dir(dir_repo)
                cmd = 'git am ' + path_patch
                result = execute(cmd, show_progress=True)
                restore_dir()
                if result[0]:
                    error('Fail to apply patch ' + patch)


def ensure_dir(dir, server=''):
    if server == '':
        if not os.path.exists(dir):
            os.makedirs(dir)
    else:
        result = execute(remotify_cmd('ls ' + dir, server=server), show_cmd=False)
        if result[0]:
            execute(remotify_cmd('mkdir -p ' + dir, server=server))


def get_dir(path):
    return os.path.split(os.path.realpath(path))[0]


def ensure_package(packages):
    package_list = packages.split(' ')
    for package in package_list:
        result = execute('dpkg -l ' + package, show_cmd=False)
        if result[0]:
            error('You need to install package: ' + package)


# return True if ver_a is greater or equal to ver_b
# ver is in format a.b.c.d
def ver_ge(ver_a, ver_b):
    vers_a = [int(x) for x in ver_a.split('.')]
    vers_b = [int(x) for x in ver_b.split('.')]

    index = 0
    while index < len(vers_a):
        if vers_a[index] > vers_b[index]:
            return True
        elif vers_a[index] < vers_b[index]:
            return False
        index += 1
    return True


def singleton(lock):
    import fcntl
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        info(str(lock) + ' is already running..')
        exit(0)


def chrome_android_cleanup(device=''):
    for key in chromium_android_info:
        execute(adb('uninstall ' + chromium_android_info[key][CHROMIUM_ANDROID_INFO_INDEX_PKG], device=device))

    execute(adb('shell rm -rf /data/data/com.example.chromium', device=device))
    #execute(adb('shell rm -rf /data/dalvik-cache/*', device=device))


def chrome_android_get_ver_type(device=''):
    ver_type = ''
    for key in chromium_android_info:
        if not re.match('^chrome', key):
            continue
        if execute_adb_shell(cmd='pm -l |grep ' + chromium_android_info[key][CHROMIUM_ANDROID_INFO_INDEX_PKG], device=device):
            ver_type = key
            break

    return ver_type


def list_union(a, b):
    return list(set(a).union(set(b)))


def list_intersect(a, b):
    return list(set(a).intersection(set(b)))


def list_diff(a, b):
    return list(set(a).difference(set(b)))


def get_comb_name(splitter, *subs):
    return splitter.join(subs)


def mouse_move(x, y):
    from Xlib.display import Display
    from Xlib import X
    from Xlib.ext.xtest import fake_input
    d = Display()
    fake_input(d, X.MotionNotify, x=x, y=y)
    d.flush()


def mouse_click(button=1):
    from Xlib import X
    from Xlib.display import Display
    from Xlib.ext.xtest import fake_input

    d = Display()
    fake_input(d, X.ButtonPress, button)
    d.sync()
    fake_input(d, X.ButtonRelease, button)
    d.sync()


def chromium_get_rev_max(dir_src):
    if not os.path.exists(dir_src):
        error('Chromium src dir does not exist')

    backup_dir(dir_src)
    execute('git fetch', dryrun=True)
    rev_hash = _chromium_get_rev_hash(chromium_rev_max)
    restore_dir()
    return rev_hash.keys()[0]


# get hash according to rev
def chromium_get_hash(dir_src, rev):
    if not os.path.exists(dir_src):
        error('Chromium src dir does not exist')

    backup_dir(dir_src)
    rev_hash = _chromium_get_rev_hash(rev, rev, force=False)
    if not rev_hash:
        execute('git fetch', dryrun=True)
        rev_hash = _chromium_get_rev_hash(rev, rev, force=False)
    restore_dir()

    if not rev_hash:
        return ''
    else:
        return rev_hash[rev]


# single rev: return hash for general rev, return ''  if failed to find. return rev_max for chromium_rev_max
# rev range: return valid hashes within range, return {} if failed to find.
def chromium_get_rev_hash(dir_src, rev_min, *rev_extra):
    if len(rev_extra):
        rev_max = rev_extra[0]
    else:
        rev_max = rev_min

    if rev_min > rev_max:
        return {}

    if not os.path.exists(dir_src):
        error('Chromium src dir does not exist')

    backup_dir(dir_src)
    if rev_min == chromium_rev_max:
        rev_hash = {}
    else:
        rev_hash = _chromium_get_rev_hash(rev_min, rev_max, force=False)
    if not rev_hash:
        execute('git fetch', dryrun=True)
        rev_hash = _chromium_get_rev_hash(rev_min, rev_max, force=True)
    restore_dir()

    if len(rev_extra):
        return rev_hash
    elif rev_min == chromium_rev_max:
        return rev_hash.keys()[0]
    else:
        if rev_min in rev_hash:
            return rev_hash[rev_min]
        else:
            return ''


def get_logger(name, dir_log, level=logging.DEBUG):
    ensure_dir(dir_log)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_log = logging.FileHandler(dir_log + '/' + get_datetime(format='%Y-%m-%d-%X') + '.log')
    file_log.setFormatter(formatter)
    logger.addHandler(file_log)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


# <android>
def android_unlock_screen(device=''):
    execute(adb(cmd='shell input keyevent 82', device=device))


def android_set_screen_lock_none(device=''):
    execute_adb_shell(cmd='am start -n com.android.settings/.SecuritySettings && sleep 5 && input tap 200 150 && sleep 5 && input tap 200 100 && am force-stop com.android.settings', device=device)


def android_set_display_sleep_30mins(device=''):
    execute_adb_shell(cmd='am start -n com.android.settings/.DisplaySettings && sleep 5 && input tap 200 250 && sleep 5 && input tap 500 550 && am force-stop com.android.settings', device=device)


def android_is_screen_on(device=''):
    result = execute(adb(cmd='shell dumpsys power', device=device) + ' |grep mScreenOn=true')
    if result[0]:
        return False
    else:
        return True


# Just trigger once
def android_trigger_screen_on(device=''):
    if not android_is_screen_on(device):
        # Bring up screen by pressing power
        execute(adb('shell input keyevent 26'), device=device)


# Keep screen on when charging
def android_keep_screen_on(device=''):
    execute(adb(cmd='shell svc power stayon usb', device=device))


def android_tap(x=1300, y=700, device=''):
    execute(adb(cmd='shell input tap %s %s' % (str(x), str(y)), device=device))


def android_get_info(key, device=''):
    cmd = adb(cmd='shell grep %s= system/build.prop' % key, device=device)
    result = execute(cmd, return_output=True, show_cmd=False)
    return result[1].replace(key + '=', '').rstrip('\r\n')


def android_get_target_arch(device=''):
    abi = android_get_info(key='ro.product.cpu.abi', device=device)
    target_arch = ''
    for key in target_arch_info:
        if abi == target_arch_info[key][TARGET_ARCH_INFO_INDEX_ABI]:
            target_arch = key
            break

    if target_arch == '':
        error('Could not get correct target arch for device ' + device)

    return target_arch


def android_start_emu(target_arch):
    pid = os.fork()
    if pid == 0:
        cmd = 'LD_LIBRARY_PATH=%s/adt/sdk/tools/lib %s/adt/sdk/tools/emulator64-%s -avd %s -no-audio' % (dir_tool, dir_tool, target_arch, target_arch)
        execute(cmd)
    else:
        info('Starting emulator for ' + target_arch)
        if target_arch == 'x86':
            time.sleep(20)
        else:
            time.sleep(60)
# </android>


# 13, 5 -> 15
def roundup(num, base):
    remainder = num % base
    if remainder == 0:
        return num

    return num + base - remainder


# 17, 5 -> 15
def rounddown(num, base):
    remainder = num % base
    if remainder == 0:
        return num

    return num - remainder


# <internal>
# dir_repo: repo dir
# path_patch: Full path of patch
# count: Recent commit count to check
def _patch_applied(dir_repo, path_patch, count=30):
    f = open(path_patch)
    lines = f.readlines()
    f.close()

    pattern = re.compile('Subject: \[PATCH.*\] (.*)')
    match = pattern.search(lines[3])
    title = match.group(1)
    backup_dir(dir_repo)
    result = execute('git show -s --pretty="format:%s" --max-count=' + str(count) + ' |grep "%s"' % title.replace('"', '\\"'), show_cmd=False)
    restore_dir()
    if result[0]:
        return False
    else:
        return True


# force: True so that rev_hash will return as much as possible
def _chromium_get_rev_hash(rev_min, rev_max=0, force=False):
    execute('git log origin master >git_log', show_cmd=False)
    f = open('git_log')
    lines = f.readlines()
    f.close()
    execute('rm -f git_log', show_cmd=False)

    pattern_hash = re.compile('^commit (.*)')
    pattern_rev = re.compile('^git-svn-id: .*@(.*) (.*)')
    # from r291561, use below new format
    pattern_rev2 = re.compile('Cr-Commit-Position: refs/heads/master@{#(.*)}')
    hash_temp = ''
    rev_temp = 0
    rev_hash = {}
    is_rev = False
    is_first = True
    for index, line in enumerate(lines):
        match = pattern_hash.search(line)
        if match:
            hash_temp = match.group(1)

        match = pattern_rev.search(line.lstrip())
        if match:
            if pattern_hash.search(lines[index + 2].lstrip()):
                rev_temp = int(match.group(1))
                is_rev = True

        match = pattern_rev2.search(line.lstrip())
        if match:
            if pattern_hash.search(lines[index + 2].lstrip()):
                rev_temp = int(match.group(1))
                is_rev = True

        if is_rev:
            is_rev = False
            if is_first:
                is_first = False
                if rev_min == chromium_rev_max:
                    rev_hash[rev_temp] = hash_temp
                    return rev_hash
                if rev_temp < rev_max and not force:
                    return rev_hash
            if rev_temp >= rev_min and rev_temp <= rev_max:
                rev_hash[rev_temp] = hash_temp
            elif rev_temp < rev_min:
                return rev_hash
# </internal>
