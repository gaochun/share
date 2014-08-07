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
import fcntl

formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
host_os = platform.system().lower()
host_name = socket.gethostname()
username = os.getenv('USER')
number_cpu = str(multiprocessing.cpu_count() * 2)
args = argparse.Namespace()
dir_stack = []
timer = {}

chrome_android_ver_type_info = {
    'stable': ['com.android.chrome', ''],
    'beta': ['com.chrome.beta', ''],
    'example': ['com.example.chromium', 'com.google.android.apps.chrome.Main'],
    'example_stable': ['com.chromium.stable', 'com.google.android.apps.chrome.Main'],
    'example_beta': ['com.chromium.beta', 'com.google.android.apps.chrome.Main'],
}
CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG = 0
CHROME_ANDROID_VER_TYPE_INFO_INDEX_ACT = 1

target_arch_index = {'x86': 0, 'arm': 1, 'x86_64': 2, 'arm64': 3}
target_arch_strip = {
    'x86': 'i686-linux-android-strip',
    'arm': 'arm-linux-androideabi-strip',
}


def _get_real_dir(path):
    return os.path.split(os.path.realpath(path))[0]
dir_temp = _get_real_dir(__file__)
while not os.path.exists(dir_temp + '/.git'):
    dir_temp = _get_real_dir(dir_temp)
dir_share = dir_temp
dir_python = dir_share + '/python'
dir_linux = dir_share + '/linux'
dir_common = dir_share + '/common'
file_chromium = dir_python + '/chromium.py'
file_aosp = dir_python + '/aosp.py'
python_chromium = 'python ' + file_chromium
python_aosp = 'python ' + file_aosp

dir_workspace = '/workspace'
dir_server = dir_workspace + '/server'
dir_server_aosp = dir_server + '/aosp'
dir_server_chromium = dir_server + '/chromium'
chrome_android_dir_server_todo = dir_server_chromium + '/android-chrome-todo'
dir_server_log = dir_server + '/log'
dir_project = dir_workspace + '/project'
dir_project_chrome_android = dir_project + '/chrome-android'
dir_tool = dir_workspace + '/tool'

path_web = 'http://wp-03.sh.intel.com'
path_web_chromium = path_web + '/chromium'
path_server_backup = '//wp-02/backup'

dir_home = os.getenv('HOME')

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


def get_datetime(format='%Y%m%d%H%M%S'):
    return time.strftime(format, time.localtime())


def has_recent_change(path_file, interval=24*3600):
    if time.time() - os.path.getmtime(path_file) < interval:
        return True
    else:
        return False


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


# TODO: The interactive solution doesn't use subprocess now, which can not support show_progress and return_output now.
# show_command: Print command if Ture. Default to True.
# show_duration: Report duration to execute command if True. Default to False.
# show_progress: print stdout and stderr to console if True. Default to False.
# return_output: Put stdout and stderr in result if True. Default to False.
# dryrun: Do not actually run command if True. Default to False.
# abort: Quit after execution failed if True. Default to False.
# log_file: Print stderr to log file if existed. Default to ''.
# interactive: Need user's input if true. Default to False.
def execute(command, show_command=True, show_duration=False, show_progress=False, return_output=False, dryrun=False, abort=False, log_file='', interactive=False):
    if show_command:
        _cmd(command)

    if dryrun:
        return [0, '']

    start_time = datetime.datetime.now().replace(microsecond=0)

    if interactive:
        ret = os.system(command)
        result = [ret / 256, '']
    else:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while show_progress:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

        (out, err) = process.communicate()
        ret = process.returncode

        if return_output:
            result = [ret, out + err]
        else:
            result = [ret, '']

    if log_file:
        os.system('echo ' + err + ' >>' + log_file)

    end_time = datetime.datetime.now().replace(microsecond=0)
    time_diff = end_time - start_time

    if show_duration:
        info(str(time_diff) + ' was spent to execute following command: ' + command)

    if abort and result[0]:
        error('Failed to execute', error_code=result[0])

    return result


def bashify(command):
    return 'bash -c "' + command + '"'


def has_process(name):
    r = os.popen('ps auxf |grep -c ' + name)
    count = int(r.read())
    if count == 2:
        return False

    return True


def shell_source(shell_cmd, use_bash=False):
    if use_bash:
        command = bashify('. ' + shell_cmd + '; env')
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
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
    result = execute('dpkg -s ' + pkg, show_command=False)
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


def set_path(path_extra):
    path = os.getenv('PATH')
    if host_os == 'windows':
        splitter = ';'
    elif host_os == 'linux':
        splitter = ':'

    paths = [path]
    if host_os == 'linux':
        paths.extend(['/usr/bin', '/usr/sbin'])
    if path_extra:
        paths.append(path_extra)

    setenv('PATH', splitter.join(paths))


def getenv(env):
    return os.getenv(env)


def setenv(env, value):
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
    setenv('no_proxy', 'intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,127.0.0.0/8,134.134.0.0/16,172.16.0.0/20,192.168.42.0/16,10.239.*.*,ubuntu-ygu5-*,wp-*')


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
    devices_target_arch = []
    cmd = adb('devices -l', device='')
    device_lines = commands.getoutput(cmd).split('\n')
    for device_line in device_lines:
        if re.match('List of devices attached', device_line):
            continue
        elif re.match('^\s*$', device_line):
            continue

        pattern = re.compile('device:(.*)')
        match = pattern.search(device_line)
        if match:
            device_name = match.group(1)
            devices_name.append(device_name)
            device = device_line.split(' ')[0]
            if re.search('192.168.42.1', device):
                devices_type.append('baytrail')
            elif re.search('emulator', device):
                devices_type.append('generic')
            devices.append(device)

    if devices_limit:
        # This has to be reversed and deleted from end
        for index, device in reversed(list(enumerate(devices))):
            if device not in devices_limit:
                del devices[index]
                del devices_name[index]
                del devices_type[index]

    for device in devices:
        devices_target_arch.append(android_get_target_arch(device=device))

    return (devices, devices_name, devices_type, devices_target_arch)


def timer_start(tag):
    if not tag in timer:
        timer[tag] = [0, 0]
    timer[tag][0] = datetime.datetime.now().replace(microsecond=0)


def timer_end(tag):
    timer[tag][1] = datetime.datetime.now().replace(microsecond=0)


def timer_diff(tag):
    if tag in timer:
        return str(timer[tag][1] - timer[tag][0])
    else:
        return '0:00:00'


def get_caller_name():
    return inspect.stack()[1][3]


def adb(cmd, device='192.168.42.1'):
    if device == '192.168.42.1':
        device = '192.168.42.1:5555'

    if device == '':
        return 'adb ' + cmd
    else:
        return 'adb -s ' + device + ' ' + cmd


# Execute a adb shell command and know the return value
# adb shell would always return 0, so a trick has to be used here to get return value
def execute_adb_shell(cmd, device='192.168.42.1'):
    cmd_adb = adb(cmd='shell "' + cmd + ' || echo FAIL"', device=device)
    result = execute(cmd_adb, return_output=True, show_command=False)
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
def device_connected(device='192.168.42.1', mode='system'):
    if mode == 'system':
        result = execute('timeout 1s ' + adb(cmd='shell \ls', device=device))
    elif mode == 'bootloader':
        path_fastboot = dir_linux + '/fastboot'
        result = execute('timeout 1s %s -t %s getvar all' % (path_fastboot, device))

    if result[0]:
        return False
    else:
        return True


# Try to connect to device in case it's not online
def connect_device(device='192.168.42.1', mode='system'):
    if mode == 'system':
        if device_connected(device, mode):
            return True

        cmd = 'timeout 1s ' + adb(cmd='disconnect %s' % device, device='') + ' && timeout 1s ' + adb(cmd='connect %s' % device, device='')
        execute(cmd, interactive=True)
        return device_connected(device, mode)
    elif mode == 'bootloader':
        return device_connected(device, mode)


def analyze_issue(dir_aosp='/workspace/project/aosp-stable', dir_chromium='/workspace/project/chromium-android', arch='x86_64', device='192.168.42.1', type='tombstone', date=20140101):
    if device == '192.168.42.1':
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

    connect_device(device)

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
                result = execute(cmd, return_output=True, show_command=False)
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
            error(dir_repo + 'does not exist')

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
    result = execute('git show -s --pretty="format:%s" --max-count=' + str(count) + ' |grep "%s"' % title.replace('"', '\\"'), show_command=False)
    restore_dir()
    if result[0]:
        return False
    else:
        return True


def ensure_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def get_dir(path):
    return os.path.split(os.path.realpath(path))[0]


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
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        info(str(lock) + ' is already running..')
        exit(0)


def chrome_android_cleanup(device='192.168.42.1'):
    for key in chrome_android_ver_type_info:
        execute(adb('uninstall ' + chrome_android_ver_type_info[key][CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG], device=device))

    execute(adb('shell rm -rf /data/data/com.example.chromium', device=device))
    #execute(adb('shell rm -rf /data/dalvik-cache/*', device=device))


def chrome_android_get_ver_type(device='192.168.42.1'):
    ver_type = ''
    for key in chrome_android_ver_type_info:
        if execute_adb_shell(cmd='pm -l |grep ' + chrome_android_ver_type_info[key][CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG], device=device):
            ver_type = key
            break

    return ver_type


##### android related functions begin #####
def android_unlock_screen(device='192.168.42.1'):
    execute(adb(cmd='shell input keyevent 82', device=device))


def android_set_screen_lock_none(device='192.168.42.1'):
    execute_adb_shell(cmd='am start -n com.android.settings/.SecuritySettings && sleep 5 && input tap 200 150 && sleep 5 && input tap 200 100 && am force-stop com.android.settings', device=device)

def android_set_display_sleep_30mins(device='192.168.42.1'):
    execute_adb_shell(cmd='am start -n com.android.settings/.DisplaySettings && sleep 5 && input tap 200 250 && sleep 5 && input tap 500 550 && am force-stop com.android.settings', device=device)

def android_is_screen_on(device='192.168.42.1'):
    result = execute(adb(cmd='shell dumpsys power', device=device) + ' |grep mScreenOn=true')
    if result[0]:
        return False
    else:
        return True


# Just trigger once
def android_trigger_screen_on(device='192.168.42.1'):
    if not android_is_screen_on(device):
        # Bring up screen by pressing power
        execute(adb('shell input keyevent 26'), device=device)


# Make screen on when charging
def android_keep_screen_on(device='192.168.42.1'):
    execute(adb(cmd='shell svc power stayon usb', device=device))


def android_get_info(key, device='192.168.42.1'):
    cmd = adb(cmd='shell grep %s= system/build.prop' % key, device=device)
    result = execute(cmd, return_output=True, show_command=False)
    return result[1].replace(key + '=', '').rstrip('\r\n')


def android_get_target_arch(device='192.168.42.1'):
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


##### android related functions end #####


def list_union(a, b):
    return list(set(a).union(set(b)))


def list_intersect(a, b):
    return list(set(a).intersection(set(b)))


def list_diff(a, b):
    return list(set(a).difference(set(b)))


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
################################################################################


def _cmd(msg):
    print '[COMMAND] ' + msg
