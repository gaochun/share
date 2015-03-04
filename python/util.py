#!/usr/bin/env python
# -*- coding: utf-8 -*-

# xp
# LD_LIBRARY_PATH=/workspace/tool/adt/sdk/tools/lib /workspace/tool/adt/sdk/tools/emulator64-x86 -avd x86 -gpu on -no-audio

# format: import, globals, functions
# globals: misc, path, chromium
# functions: misc, file, android, chromium, internal

# <import>
import argparse
import atexit
import codecs
import collections
import commands
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import fileinput
import hashlib
from HTMLParser import HTMLParser
from httplib import BadStatusLine
import inspect
import json
import logging
import multiprocessing
from multiprocessing import Pool
import operator
import os
import pickle
import platform
import random
import re
import select
import smtplib
import socket
import subprocess
import sys
import threading
import time
import urllib2
# </import>

# <globals>
## <misc>
reload(sys)
sys.setdefaultencoding('utf-8')

log = ''
host_os = platform.system().lower()
host_name = socket.gethostname()
username = os.getenv('USER')
count_cpu = multiprocessing.cpu_count()
count_cpu_build = count_cpu * 2
args = argparse.Namespace()
dir_stack = []
log_stack = []
timer = {}

# webmark
webmark_format = ['category', 'name', 'version', 'metric', 'result']
webmark_result_str = 'Result: '

machines = [
    ['wp-01', 'wp', '', 'sh.intel.com'],
    ['wp-02', 'wp', '', 'sh.intel.com'],
    ['wp-03', 'wp', '', 'sh.intel.com'],
    ['wp-04', 'wp', '', 'sh.intel.com'],
    ['ubuntu-ygu5-01', 'gyagp', '', 'sh.intel.com'],
    ['ubuntu-ygu5-02', 'gyagp', '', 'sh.intel.com'],
]
MACHINES_INDEX_HOSTNAME = 0
MACHINES_INDEX_USERNAME = 1
MACHINES_INDEX_PASSWORD = 2
MACHINES_INDEX_DOMAIN = 3

# machines that webcatch can build on
servers_webcatch = [
    machines[1],
    machines[2],
]
# main server for webcatch
server_webcatch = machines[1]

# main server for chromeforandroid
server_chromeforandroid = machines[2]

target_arch_index = {'x86': 0, 'arm': 1, 'x86_64': 2, 'arm64': 3}
target_arch_strip = {
    'x86': 'i686-linux-android-strip',
    'x86_64': 'i686-linux-android-strip',
    'arm': 'arm-linux-androideabi-strip',
    'arm64': 'aarch64-linux-android-strip',
}

target_os_all = ['android', 'linux']
target_arch_all = ['x86', 'arm', 'x86_64', 'arm64']
target_arch_chrome_android = target_arch_all[0:2]
target_arch_info = {
    'x86': ['x86'],
    'arm': ['armeabi-v7a'],
    'x86_64': ['x86_64'],
    'arm64': ['arm64'],
}
TARGET_ARCH_INFO_INDEX_ABI = 0

target_module_all = ['webview', 'chrome', 'content_shell', 'chrome_stable', 'chrome_beta', 'webview_shell', 'chrome_shell', 'stock_browser']

# /sys/devices/system/cpu/cpu0/cpufreq
device_product_info = {
    'asus_t100': {
        'governors': ['performance', 'powersave'],
        'governor': 'powersave',
        'freqs': [],
        'freq_min': 400000,
        'freq_max': 1400000,
        'count_cpu': 4,
        'scaling_driver': 'intel_pstate',
        'count_cstate': 7,
    },
    # ZTE Geek
    'V975': {
        'governors': ['ondemand', 'userspace', 'interactive', 'performance'],
        'governor': 'interactive',
        'freqs': [2000000, 1866000, 1600000, 1333000, 933000, 800000],
        'freq_min': 800000,
        'freq_max': 2000000,
        'count_cpu': 4,
        'scaling_driver': 'sfi-cpufreq',
        'count_cstate': 7,
    },
    'cruise7': {
        'governors': ['performance', 'powersave'],
        'governor': 'powersave',
        'freqs': [],
        'freq_min': 600000,
        'freq_max': 2200000,
        'count_cpu': 4,
        'scaling_driver': 'intel_pstate',
        'count_cstate': 6,
    },
    'surftab': {
        'governors': ['performance', 'powersave'],
        'governor': 'powersave',
        'freqs': [],
        'freq_min': 600000,
        'freq_max': 1832600,
        'count_cpu': 4,
        'scaling_driver': 'intel_pstate',
        'count_cstate': 6,
    },
}
device_product_info['asus_t100_64p'] = device_product_info['asus_t100']
device_product_info['ecs_e7'] = device_product_info['cruise7']
device_product_info['ecs_e7_64p'] = device_product_info['cruise7']
device_product_info['cruise8'] = device_product_info['cruise7']
## </misc>


## <path>
dir_home = os.getenv('HOME')
dir_workspace = '/workspace'

# <server>
path_server_backup = '//wp-01.sh.intel.com/backup'
path_server_webmark = '//wp-02.sh.intel.com/webmark'
# </server>

# <web>
path_web_benchmark = 'http://wp-02.sh.intel.com'
path_web_webbench = path_web_benchmark + '/webbench'
path_web_webcatch = path_web_benchmark + '/chromium'
path_web_webmark = path_web_benchmark + '/webmark'
path_web_webmark_result = path_web_webmark + '/result'
path_web_chrome_android = 'http://wp-03.sh.intel.com/chromium'
# </web>

# <project> dir_project_xxx
dir_project = dir_workspace + '/project'
dir_project_chrome_android = dir_project + '/chrome-android'
dir_project_webcatch = dir_project + '/webcatch'
dir_project_webcatch_out = dir_project_webcatch + '/out'
dir_project_webcatch_project = dir_project_webcatch + '/project'
dir_project_webcatch_log = dir_project_webcatch + '/log'
# </project>

# <server> dir_server_xxx
dir_server = dir_workspace + '/server'
dir_server_aosp = dir_server + '/aosp'
dir_server_chromium = dir_server + '/chromium'
dir_server_webbench = dir_server + '/webbench'
dir_server_chrome_android_todo = dir_server_chromium + '/android-chrome-todo'
dir_server_chrome_android_todo_buildid = dir_server_chrome_android_todo + '/buildid'
# </server>

# <tool> dir_tool_xxx
dir_tool = dir_workspace + '/tool'
# </tool>


# <share> dir_share_xxx
def _get_real_dir(path):
    return os.path.split(os.path.realpath(path))[0]
dir_temp = _get_real_dir(__file__)
while not os.path.exists(dir_temp + '/.git'):
    dir_temp = _get_real_dir(dir_temp)
dir_share = dir_temp

dir_share_ignore = dir_share + '/ignore'
dir_share_ignore_log = dir_share_ignore + '/log'
dir_share_ignore_timestamp = dir_share_ignore + '/timestamp'
dir_share_ignore_backup = dir_share_ignore + '/backup'
dir_share_ignore_webmark = dir_share_ignore + '/webmark'
dir_share_ignore_webmark_download = dir_share_ignore_webmark + '/download'
dir_share_ignore_webmark_log = dir_share_ignore_webmark + '/log'
dir_share_ignore_webmark_result = dir_share_ignore_webmark + '/result'
dir_share_ignore_webcatch = dir_share_ignore + '/webcatch'
dir_share_ignore_webcatch_download = dir_share_ignore_webcatch + '/download'
dir_share_ignore_webcatch_log = dir_share_ignore_webcatch + '/log'
dir_share_ignore_webcatch_pause = dir_share_ignore_webcatch + '/pause'
dir_share_ignore_chromium = dir_share_ignore + '/chromium'
path_share_ignore_chromium_perf = dir_share_ignore_chromium + '/perf'

dir_share_python = dir_share + '/python'
dir_share_python_webcatch = dir_share_python + '/webcatch'
dir_share_python_webcatch_log = dir_share_python_webcatch + '/log'
dir_share_python_webmark = dir_share_python + '/webmark'
dir_share_python_chromium = dir_share_python + '/chromium'
python_share_webmark = 'python ' + dir_share_python_webmark + '/webmark.py'
python_share_chromium = 'python ' + dir_share_python + '/chromium.py'
python_share_aosp = 'python ' + dir_share_python + '/aosp.py'

dir_share_linux = dir_share + '/linux'
dir_share_linux_config = dir_share_linux + '/config'
dir_share_linux_tool = dir_share_linux + '/tool'
path_share_fastboot = dir_share_linux_tool + '/fastboot'
path_share_chromedriver = dir_share_linux_tool + '/chromedriver/chromedriver-2.12'
path_share_apktool = dir_share_linux_tool + '/apktool/apktool_2.0.0rc3.jar'

dir_share_common = dir_share + '/common'
# </share>
## </path>

## <chromium>
chromium_rev_max = 9999999

# src/build/android/pylib/constants.py
chromium_android_info = {
    'chrome_stable': ['', 'com.android.chrome', '.Main', True],
    'chrome_beta': ['', 'com.chrome.beta', '.Main', True],
    'stock_browser': ['', 'com.android.browser', '.BrowserActivity', True],
    'content_shell': ['ContentShell', 'org.chromium.content_shell_apk', '.ContentShellActivity', True],
    'chrome_shell': ['ChromeShell', 'org.chromium.chrome.shell', '.ChromeShellActivity', True],
    'webview_shell': ['AndroidWebView', 'org.chromium.android_webview.shell', '.AwShellActivity', False],

    # self defined
    ## after the change of package name and AndroidManifest.xml
    'chromium_stable': ['', 'com.android.chromium', 'com.google.android.apps.chrome.Main', False],
    'chromium_beta': ['', 'com.chromium.beta', 'com.google.android.apps.chrome.Main', False],
    'chromium2_stable': ['', 'com.android.chrome', 'com.google.android.apps.chrome.Main', True],
    'chromium2_beta': ['', 'com.chrome.beta', 'com.google.android.apps.chrome.Main', True],
    ## before the change of package name and AndroidManifest.xml
    'chrome_example': ['', 'com.example.chromium', 'com.google.android.apps.chrome.Main', False],
    ## old builds before transition, including some M33 builds
    'chrome_example_stable': ['', 'com.chromium.stable', 'com.google.android.apps.chrome.Main', False],
    'chrome_example_beta': ['', 'com.chromium.beta', 'com.google.android.apps.chrome.Main', False],
}
CHROMIUM_ANDROID_INFO_INDEX_APK = 0
CHROMIUM_ANDROID_INFO_INDEX_PKG = 1
CHROMIUM_ANDROID_INFO_INDEX_ACT = 2
CHROMIUM_ANDROID_INFO_INDEX_ISKNOWN = 3

# Each chromium version is: major.minor.build.patch
# major -> svn rev, git commit, build. major commit is after build commit.
# To get this, search 'The atomic number' in 'git log origin master chrome/VERSION'
chromium_majorver_info = {
    43: [317497, 'b4b0dad750fcdaefea8f034ab83df7ba588701d4', 2312],
    42: [310967, '2eb44014970b8aa0333940a9f88ebd83edb497ac', 2273],
    41: [303373, 'e9c657d834d5946b9cb09a47fd087970a3b1d91a', 2215],
    40: [297098, '86e466451cdca1e32a912df33838d9eec0dadcd7', 2172],
    39: [290085, '292f233e2a09f983aa93134c50ff3eb0cb438c28', 2126],
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

# combs used by webmark.py and chromium-perf.py follow below index rule:
# ['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86_64', 'content_shell', ['302000', '999999', 200]]
PERF_COMBS_INDEX_DEVICE_PRODUCT = 0
PERF_COMBS_INDEX_DEVICE_ARCH = 1
PERF_COMBS_INDEX_DEVICE_GOVERNOR = 2
PERF_COMBS_INDEX_DEVICE_FREQ = 3
PERF_COMBS_INDEX_MODULE_OS = 4
PERF_COMBS_INDEX_MODULE_ARCH = 5
PERF_COMBS_INDEX_MODULE_NAME = 6
PERF_COMBS_INDEX_MODULE_VERSION = 7
PERF_COMBS_INDEX_MODULE_VERSION_MIN = 0
PERF_COMBS_INDEX_MODULE_VERSION_MAX = 1
PERF_COMBS_INDEX_MODULE_VERSION_INTERVAL = 2

PERF_CHANGE_PERCENT = 5  # means regression or improvement
## </chromium>
# </globals>


# <functions>
## <misc>
def info(msg):
    _msg(msg)


def warning(msg):
    _msg(msg, show_trace=True)


def cmd(msg):
    _msg(msg)


# Used for debug, so that it can be cleaned up easily
def debug(msg):
    _msg(msg)


def trace(msg):
    _msg(msg)


def error(msg, abort=True, error_code=1):
    _msg(msg, show_trace=True)
    if abort:
        quit(error_code)


def trace_func(frame, event, arg, indent=[0]):
    path_file = frame.f_code.co_filename
    name_func = frame.f_code.co_name
    name_file = path_file.split('/')[-1]
    if path_file[:4] != '/usr' and path_file != '<string>':
        if event == 'call':
            indent[0] += 2
            trace('-' * indent[0] + '> call %s:%s' % (name_file, name_func))
        elif event == 'return':
            trace('<' + '-' * indent[0] + ' exit %s:%s' % (name_file, name_func))
            indent[0] -= 2
    return trace_func


def hasvalue(obj, member):
    if not hasattr(obj, member):
        return False

    if getattr(obj, member) == '':
        return False

    return True


def get_datetime(format='%Y%m%d%H%M%S'):
    return time.strftime(format, time.localtime())


# get seconds since 1970-01-01
def get_epoch_second():
    return int(time.time())


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
    if file_log:
        command = 'bash -o pipefail -c "%s 2>&1 | tee -a %s; (exit ${PIPESTATUS})"' % (command, file_log)

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

    end_time = datetime.datetime.now().replace(microsecond=0)
    time_diff = end_time - start_time

    if show_duration:
        info(str(time_diff) + ' was spent to execute following command: ' + command)

    if abort and result[0]:
        error('Failed to execute', error_code=result[0])

    return result


def bashify_cmd(cmd):
    return 'bash -o pipefail -c "' + cmd + '"'


def suffix_cmd(cmd, args, log):
    if args.trace:
        cmd += ' --trace'
    if log:
        cmd += ' --log ' + log
    return cmd


# Patch command if it needs to run on server
def remotify_cmd(cmd, server):
    if re.match('ubuntu', server):
        username = 'gyagp'
    else:
        username = 'wp'

    return 'ssh %s@%s %s' % (username, server, cmd)


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


def pause_resume(seconds=5):
    info('You have ' + str(seconds) + ' seconds to type "enter" to pause')
    i, o, e = select.select([sys.stdin], [], [], seconds)
    if i:
        info('Please type "r" to resume')
        while True:
            input = raw_input()
            if input == 'r':
                break


def apply_patch(patches, dir_patches):
    if not os.path.exists(dir_patches):
        return

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


def get_logger(tag, dir_log, datetime='', level=logging.DEBUG):
    ensure_dir(dir_log)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(tag)
    logger.setLevel(level)

    if datetime:
        dt = datetime
    else:
        dt = get_datetime()
    file_log = logging.FileHandler(dir_log + '/' + dt + '.log')
    file_log.setFormatter(formatter)
    logger.addHandler(file_log)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def backup_log(log_new, verbose=False):
    global log_stack, log
    log_stack.append(log)
    log = log_new

    if verbose:
        info('Switched to new log file ' + log)


def restore_log(verbose=False):
    global log_stack, log
    log_old = log_stack.pop()
    log = log_old
    if verbose:
        info('Switched to old log file ' + log)


def has_process(name):
    r = os.popen('ps auxf |grep -c ' + name)
    count = int(r.read())
    if count == 2:
        return False

    return True


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
        info('Email was sent successfully')
    except Exception:
        error('Failed to send mail at ' + host_name, abort=False)
    finally:
        smtp.quit()


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


def timer_start(tag, microsecond=False):
    if tag not in timer:
        timer[tag] = [0, 0]
    if microsecond:
        timer[tag][0] = datetime.datetime.now()
    else:
        timer[tag][0] = datetime.datetime.now().replace(microsecond=0)


def timer_stop(tag, microsecond=False):
    if microsecond:
        timer[tag][1] = datetime.datetime.now()
    else:
        timer[tag][1] = datetime.datetime.now().replace(microsecond=0)


def timer_diff(tag):
    if tag in timer:
        return timer[tag][1] - timer[tag][0]
    else:
        return datetime.timedelta(0)


def get_caller_name():
    return inspect.stack()[1][3]


def ensure_package(packages):
    package_list = packages.split(' ')
    for package in package_list:
        result = execute('dpkg -l ' + package, show_cmd=False)
        if result[0]:
            error('You need to install package: ' + package)


# ver is in format a.b.c.d
# return 1 if ver_a > ver_b
# return 0 if ver_a == ver_b
# return -1 if ver_a < ver_b
def ver_cmp(ver_a, ver_b):
    vers_a = [int(x) for x in ver_a.split('.')]
    vers_b = [int(x) for x in ver_b.split('.')]

    # make sure two lists have same length and add 0s for short one.
    len_a = len(vers_a)
    len_b = len(vers_b)
    len_max = max(len_a, len_b)
    len_diff = abs(len_a - len_b)
    vers_diff = []
    for i in range(len_diff):
        vers_diff.append(0)
    if len_a < len_b:
        vers_a.extend(vers_diff)
    elif len_b < len_a:
        vers_b.extend(vers_diff)

    index = 0
    while index < len_max:
        if vers_a[index] > vers_b[index]:
            return 1
        elif vers_a[index] < vers_b[index]:
            return -1
        index += 1
    return 0


def singleton(lock):
    import fcntl
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        info(str(lock) + ' is already running..')
        exit(0)


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


def setup_common(args, teardown):
    atexit.register(teardown)

    if args.trace:
        sys.settrace(trace_func)

    if args.time_fixed:
        timestamp = get_datetime(format='%Y%m%d')
    else:
        timestamp = get_datetime()

    if args.dir_root:
        dir_root = args.dir_root
    elif os.path.islink(sys.argv[0]):
        dir_root = get_symbolic_link_dir()
    else:
        dir_root = os.path.abspath(os.getcwd())

    ensure_dir(dir_root)
    ensure_dir(dir_share_ignore_log)
    ensure_dir(dir_share_ignore_timestamp)

    if args.log:
        log = args.log
    else:
        category = sys.path[0].split('/')[-1]
        if category in ['webmark', 'webcatch', 'chrome-android']:
            log = eval('dir_share_ignore_%s_log' % category) + '/' + timestamp + '.log'
        else:
            name_script = sys.argv[0].split('/')[-1].replace('.py', '')
            log = dir_share_ignore_log + '/' + name_script + '-' + timestamp + '.log'
    info('Log file: ' + log)
    backup_log(log, verbose=False)

    set_path(args.path_extra)
    set_proxy()
    os.chdir(dir_root)

    return (timestamp, dir_root, log)


def add_argument_common(parser):
    parser.add_argument('--dir-root', dest='dir_root', help='set root directory')
    parser.add_argument('--log', dest='log', help='log')
    parser.add_argument('--path-extra', dest='path_extra', help='extra path for execution, such as path for depot_tools')
    parser.add_argument('--time-fixed', dest='time_fixed', help='fix the time for test sake. We may run multiple tests and results are in same dir', action='store_true')
    parser.add_argument('--trace', dest='trace', help='trace', action='store_true')


# Get available disk size for a specific path
def get_avail_disk(path='/workspace'):
    output = execute('df ' + path, return_output=True)
    device, size, used, avail, percent, mountpoint = output[1].split('\n')[1].split()
    return int(avail)


def confirm(msg):
    sys.stdout.write(msg + ' [yes/no]: ')
    choice = raw_input().lower()
    if choice in ['yes', 'y']:
        return True
    else:
        return False


def set_interval(interval, function, *args, **kwargs):
    stop_event = threading.Event()

    def loop():
        while not stop_event.wait(interval):
            function(*args, **kwargs)

    t = threading.Thread(target=loop)
    t.daemon = True
    t.start()
    return stop_event
## </misc>


## <file>
def backup_files(files_backup, dir_backup, dir_src):
    path_backup = dir_share_ignore_backup + '/' + dir_backup
    ensure_dir(path_backup)
    backup_dir(path_backup)
    info('Begin to backup to ' + path_backup)
    for dir_dest in files_backup:
        ensure_dir(dir_dest)

        if isinstance(files_backup[dir_dest], str):
            files_src = [files_backup[dir_dest]]
        else:
            files_src = files_backup[dir_dest]

        for file_src in files_src:
            if file_src[0] == '/':
                path_src = file_src
            else:
                path_src = dir_src + '/' + file_src

            if not os.path.exists(path_src):
                warning(path_src + ' could not be found')
            else:
                execute('cp -rf ' + path_src + ' ' + dir_dest)
    restore_dir()

    backup_dir(dir_share_ignore_backup)
    execute('tar zcf %s.tar.gz %s' % (dir_backup, dir_backup))
    restore_dir()


# Get the dir of symbolic link, for example: /workspace/project/chromium-android instead of /workspace/project/gyagp/share/python
def get_symbolic_link_dir():
    if sys.argv[0][0] == '/':  # Absolute path
        script_path = sys.argv[0]
    else:
        script_path = os.getcwd() + '/' + sys.argv[0]
    return os.path.split(script_path)[0]


def backup_dir(dir_new, verbose=False):
    global dir_stack
    dir_old = os.getcwd()
    dir_stack.append(dir_old)
    os.chdir(dir_new)
    if verbose:
        info('Switched from %s to %s' % (dir_old, dir_new))


def restore_dir(verbose=False):
    global dir_stack
    dir_old = dir_stack.pop()
    os.chdir(dir_old)
    if verbose:
        info('Switched to ' + dir_old)


# is_sylk: If true, just copy as a symbolic link
# dir_xxx means directory
# name_xxx means file name
# path_xxx means full path of file
def copy_file(dir_src, name_src, dir_dest, name_dest='', is_sylk=False):
    if not os.path.exists(dir_dest):
        return

    if not name_dest:
        name_dest = name_src
    path_dest = dir_dest + '/' + name_dest

    # hack the name_src to support machine specific config
    # For example, wp-01-hostapd.conf
    if os.path.exists(dir_src + '/' + host_name + '-' + name_src):
        name_src = host_name + '-' + name_src
    path_src = dir_src + '/' + name_src
    if not os.path.exists(path_src):
        warning(path_src + ' does not exist')
        return

    if is_sylk and os.path.islink(path_dest) and os.readlink(path_dest) == path_src:
        return

    if re.search(dir_home, dir_dest) or re.search(dir_workspace, dir_dest):
        need_sudo = False
    else:
        need_sudo = True

    if os.path.islink(path_dest) or os.path.exists(path_dest):
        path_dest_bk = path_dest + '.bk'
        if not os.path.exists(path_dest_bk) and not os.path.islink(path_dest_bk):
            cmd = 'mv ' + path_dest + ' ' + path_dest_bk
        else:
            cmd = 'rm ' + path_dest
        if need_sudo:
            cmd = 'sudo ' + cmd
        execute(cmd, show_cmd=True)

    if is_sylk:
        cmd = 'ln -s ' + path_src + ' ' + path_dest
    else:
        cmd = 'cp -f ' + path_src + ' ' + path_dest

    if need_sudo:
        cmd = 'sudo ' + cmd
    execute(cmd, show_cmd=True)


def get_md5(path_file):
    info('Calculating md5 of %s' % path_file)
    return hashlib.md5(open(path_file, 'rb').read()).hexdigest()


def is_same_file(src, dest):
    if not os.path.exists(src) or not os.path.exists(dest):
        return False

    md5_src = get_md5(src)
    md5_dest = get_md5(dest)
    if md5_src != md5_dest:
        return False
    else:
        info('%s and %s have same md5' % (src, dest))

    return True


def has_recent_change(path_file, interval=24 * 3600):
    if get_epoch_second() - os.path.getmtime(path_file) < interval:
        return True
    else:
        return False


# upload file to specified samba server
def backup_smb(server, dir_server, file_local, dryrun=False):
    result = execute('smbclient %s -N -c "prompt; recurse; cd %s; mput %s"' % (server, dir_server, file_local), interactive=True, dryrun=dryrun)
    if result[0]:
        warning('Failed to upload: ' + file_local)
    else:
        info('Succeeded to upload: ' + file_local)


def ensure_dir(dir_check, server=''):
    if server == '':
        if not os.path.exists(dir_check):
            os.makedirs(dir_check)
    else:
        result = execute(remotify_cmd('ls ' + dir_check, server=server), show_cmd=False)
        if result[0]:
            execute(remotify_cmd('mkdir -p ' + dir_check, server=server))


def ensure_nodir(dir_check, server=''):
    if server == '':
        if os.path.exists(dir_check):
            execute('rm -rf %s' % dir_check)
    else:
        result = execute(remotify_cmd('ls ' + dir_check, server=server), show_cmd=False)
        if result[0] == 0:
            execute(remotify_cmd('rm -rf ' + dir_check, server=server))


def ensure_file(path_file):
    if not os.path.exists(path_file):
        execute('touch ' + path_file, show_cmd=True)


def get_dir(path):
    return os.path.split(os.path.realpath(path))[0]

## </file>


## <android>
def adb(cmd, device_id=''):
    # some commands do not need -s option
    cmds_none = ['devices', 'connect', 'disconnect']
    if device_id == '':
        for cmd_none in cmds_none:
            if re.search(cmd_none, cmd):
                device_id = None
                break
    if device_id == '':
        device_id = '192.168.42.1:5555'

    if device_id is None:
        return 'adb ' + cmd
    return 'adb -s ' + device_id + ' ' + cmd


# Execute a adb shell command and know the return value
# adb shell would always return 0, so a trick has to be used here to get return value
def execute_adb_shell(cmd, device_id='', su=False, abort=False, show_cmd=False):
    cmd_adb = 'shell'
    if su:
        cmd_adb += ' su -c'
    cmd_adb += ' "' + cmd + ' || echo FAIL"'
    cmd_adb = adb(cmd=cmd_adb, device_id=device_id)
    result = execute(cmd_adb, return_output=True, show_cmd=show_cmd)
    if re.search('FAIL', result[1].rstrip('\n')):
        if abort:
            error('Failed to execute ' + cmd_adb)
        return False
    else:
        return True


def get_product(repo_type, device_arch, device_type, product_brand, product_name):
    if device_type == 'generic':
        return 'aosp_' + device_arch

    if repo_type == 'upstream':
        return 'aosp_' + device_type
    elif repo_type == 'irdal':
        product = 'cohol'
    elif repo_type in ['stable', 'gminl', 'gminl64']:
        product = '%s_%s' % (product_brand, product_name)
    elif repo_type == 'stable-old':
        if device_type == 'baytrail':
            product = '%s_%s' % (product_brand, product_name)

    if device_arch == 'x86_64':
        if repo_type != 'irdal':
            product += '_64p'

    return product


# device_id: specific device. Do not use :5555 as -t option does not accept this.
# mode: system for normal mode, bootloader for bootloader mode
def device_connected(device_id='', mode='system'):
    if mode == 'system':
        result = execute('timeout 1s ' + adb(cmd='shell \ls', device_id=device_id))
    elif mode == 'bootloader':
        if device_id == '192.168.42.1:5555':
            device_id = '192.168.42.1'
        if device_id == '192.168.42.1':
            option = '-t'
        else:
            option = '-s'
        path_fastboot = path_share_fastboot
        result = execute('timeout 1s %s %s %s getvar all' % (path_fastboot, option, device_id))

    if result[0]:
        return False
    else:
        return True


# Try to connect to device in case it's not online
def connect_device(device_id='', mode='system'):
    if mode == 'system':
        if device_connected(device_id, mode):
            return True
        if device_id == '':
            device_id = '192.168.42.1:5555'
        if device_id == '192.168.42.1:5555':
            cmd = 'timeout 1s ' + adb(cmd='disconnect %s' % device_id) + ' && timeout 1s ' + adb(cmd='connect %s' % device_id)
            execute(cmd, interactive=True)
        return device_connected(device_id, mode)
    elif mode == 'bootloader':
        if device_id == '192.168.42.1:5555':
            device_id = '192.168.42.1'
        return device_connected(device_id, mode)


def analyze_file(device_id='', type='tombstone'):
    connect_device(device_id=device_id)

    if type == 'tombstone':
        result = execute(adb(cmd='shell \ls /data/tombstones', device_id=device_id), return_output=True)
        files = result[1].split('\n')
        file_name = files[-2].strip()
        execute(adb(cmd='pull /data/tombstones/' + file_name + ' /tmp/', device_id=device_id))
        result = execute('cat /tmp/' + file_name, return_output=True)
        info('Get tombstone file as /tmp/%s' % file_name)
        lines = result[1].split('\n')
    elif type == 'anr':
        execute(adb(cmd='pull /data/anr/traces.txt /tmp/', device_id=device_id))
        result = execute('cat /tmp/traces.txt', return_output=True)
        info('Get anr file as /tmp/traces.txt')
        lines = result[1].split('\n')

    return lines


def analyze_issue(dir_aosp='/workspace/project/aosp-stable', dir_chromium='/workspace/project/chromium-android', device_id='',
                  type='tombstone', repo_type=None, device_type=None, product_brand=None, product_name=None):
    if device_id == '' or device_id == '192.168.42.1:5555':
        device_type = 'baytrail'
    target_arch = android_get_target_arch(device_id=device_id)
    product = get_product(repo_type, target_arch, device_type, product_brand, product_name)
    if target_arch == 'x86_64':
        target_arch_str = '64'
    else:
        target_arch_str = ''

    dirs_symbol = [
        dir_aosp + '/out/target/product/%s/symbols/system/lib%s' % (product, target_arch_str),
        dir_chromium + '/src/out-%s/out/Release/lib' % target_arch,
    ]

    get_symbol(analyze_file(device_id=device_id, type=type), dirs_symbol)


def get_symbol(lines, dirs_symbol):
    if not dirs_symbol:
        error('No symbol file is designated')

    count_line_max = 1000
    count_valid_max = 40

    pattern = re.compile('pc (.*)  .*/libchrome(.*)\.so')
    count_line = 0
    count_valid = 0
    for line in lines:
        count_line += 1
        if count_line > count_line_max:
            break
        match = pattern.search(line)
        if match:
            name = match.group(2)
            for dir_symbol in dirs_symbol:
                path = dir_symbol + '/libchrome%s.so' % name
                if not os.path.exists(path):
                    continue
                cmd = dir_share_linux_tool + '/x86_64-linux-android-addr2line -C -e %s -f %s' % (path, match.group(1))
                result = execute(cmd, return_output=True, show_cmd=False)
                print line
                print result[1]

                count_valid += 1
                if count_valid >= count_valid_max:
                    return

                break


# [device_id, device_product, device_type, device_mode, device_target_arch]
# device_id: used to connect to it
# device_product: from product:xxx
# device_type: baytrail, generic
# device_mode: system, fastboot
# device_target_arch: x86, arm, etc.

# Example:
# T100: xxx, asus_t100, baytrail, system, x86
# V975: xxx, V975, clovertrail, system, x86
# Emulator: xxx, generic, arm

# device_model: AOSP_on_Intel_Platform, ZTE_V975. This is unused.
# device_product: get from device:xxx, asus_t100, redhookbay. This is unused.
def setup_device(devices_id_limit=[]):
    if not devices_id_limit:
        devices_id_limit_list = []
    elif isinstance(devices_id_limit, str):
        devices_id_limit_list = devices_id_limit.split(',')
    elif isinstance(devices_id_limit, list):
        devices_id_limit_list = devices_id_limit

    devices_id = []
    devices_product = []
    devices_type = []
    devices_mode = []
    devices_arch = []
    cmd = adb('devices -l')
    device_lines = commands.getoutput(cmd).split('\n')
    cmd = 'fastboot devices -l'
    device_lines += commands.getoutput(cmd).split('\n')

    pattern_fastboot = re.compile('(\S+)\s+fastboot')
    pattern_nofastboot = re.compile('fastboot: not found')
    pattern_product = re.compile('product:(.*)')
    for device_line in device_lines:
        if re.match('List of devices attached', device_line):
            continue
        elif re.match('^\s*$', device_line):
            continue
        elif re.search('offline', device_line):
            continue
        elif not re.search('device', device_line) and not re.search('fastboot', device_line):
            continue

        match = pattern_nofastboot.search(device_line)
        if match:
            continue

        match = pattern_fastboot.search(device_line)
        if match:
            device_id = match.group(1)
            devices_id.append(device_id)
            result = execute('fastboot -s %s getvar product' % device_id, return_output=True, show_cmd=False)
            match = re.search('product: (.*)', result[1])
            device_product = match.group(1)
            devices_product.append(device_product)
            devices_type.append(device_product)
            devices_mode.append('fastboot')
            continue

        # may contain more than one space
        items = device_line.split()
        for item in items:
            match = pattern_product.search(item)
            if match:
                device_product = match.group(1)
                devices_product.append(device_product)
                break

        device_id = items[0]
        devices_id.append(device_id)
        if re.search('asus_t100', device_product) or re.search('cruise7', device_product):
            devices_type.append('baytrail')
        elif re.search('V975', device_product):
            devices_type.append('clovertrail')
        elif re.search('sdk', device_product):
            devices_type.append('generic')
        else:
            devices_type.append('baytrail')
        devices_mode.append('system')

    # filter out unnecessary
    if devices_id_limit_list:
        # This has to be reversed and deleted from end
        for index, device_id in reversed(list(enumerate(devices_id))):
            if device_id not in devices_id_limit_list:
                del devices_id[index]
                del devices_product[index]
                del devices_type[index]
                del devices_mode[index]

    # set up mode
    for index, device_id in enumerate(devices_id):
        if devices_mode[index] == 'fastboot':
            devices_arch.append('')
        else:
            devices_arch.append(android_get_target_arch(device_id=device_id))

    return (devices_id, devices_product, devices_type, devices_arch, devices_mode)


def android_input_keyevent(key, device_id=''):
    execute(adb(cmd='shell input keyevent %s' % str(key), device_id=device_id))


def android_press_power(device_id=''):
    android_input_keyevent(26, device_id=device_id)


def android_unlock_screen(device_id=''):
    android_input_keyevent(82, device_id=device_id)


def android_set_screen_lock_none(device_id=''):
    ver = android_get_ver(device_id=device_id)
    if ver_cmp(ver, '5.0') >= 0:
        info('Andorid Lollipop does not support to set screen lock to none')
    else:
        execute_adb_shell(cmd='am start -n com.android.settings/.SecuritySettings && sleep 5 && input tap 200 150 && sleep 5 && input tap 200 100 && am force-stop com.android.settings', device_id=device_id)


def android_set_display_sleep_30mins(device_id=''):
    ver = android_get_ver(device_id=device_id)
    if ver_cmp(ver, '5.0') >= 0:
        execute_adb_shell(cmd='am start -n com.android.settings/.DisplaySettings && sleep 2 && input tap 200 400 && sleep 2 && input tap 500 800 && am force-stop com.android.settings', device_id=device_id)
    else:
        execute_adb_shell(cmd='am start -n com.android.settings/.DisplaySettings && sleep 5 && input tap 200 250 && sleep 5 && input tap 500 550 && am force-stop com.android.settings', device_id=device_id)


def android_is_screen_on(device_id=''):
    ver = android_get_ver(device_id=device_id)
    if ver_cmp(ver, '5.0') >= 0:
        result = execute(adb(cmd='shell dumpsys power', device_id=device_id) + ' |grep "Display Power: state=ON"')
    else:
        result = execute(adb(cmd='shell dumpsys power', device_id=device_id) + ' |grep "mScreenOn=true"')
    if result[0]:
        return False
    else:
        return True


def android_ensure_screen_on(device_id=''):
    if not android_is_screen_on(device_id=device_id):
        android_press_power(device_id=device_id)


def android_ensure_screen_off(device_id=''):
    if android_is_screen_on(device_id=device_id):
        android_press_power(device_id=device_id)


# Keep screen on when charging
def android_keep_screen_on(device_id=''):
    execute(adb(cmd='shell svc power stayon usb', device_id=device_id))


def android_tap(x=1300, y=700, device_id=''):
    execute(adb(cmd='shell input tap %s %s' % (str(x), str(y)), device_id=device_id))


def android_get_info(key, device_id=''):
    cmd = adb(cmd='shell grep %s= system/build.prop' % key, device_id=device_id)
    result = execute(cmd, return_output=True, show_cmd=False)
    return result[1].replace(key + '=', '').rstrip('\r\n')


def android_get_power_percent(device_id=''):
    cmd = adb(cmd='shell dumpsys power | grep mBatteryLevel=', device_id=device_id)
    result = execute(cmd, return_output=True, show_cmd=False)
    return int(result[1].replace('mBatteryLevel=', '').rstrip('\r\n').strip(' '))


def android_get_ver(device_id=''):
    return android_get_info('ro.build.version.release', device_id=device_id)


def android_get_target_arch(device_id=''):
    abi = android_get_info(key='ro.product.cpu.abi', device_id=device_id)
    target_arch = ''
    for key in target_arch_info:
        if abi == target_arch_info[key][TARGET_ARCH_INFO_INDEX_ABI]:
            target_arch = key
            break

    if target_arch == '':
        error('Could not get correct target arch for device ' + device_id)

    return target_arch


def android_get_free_memory(device_id=''):
    cmd = adb(cmd='shell cat /proc/meminfo | grep MemAvail', device_id=device_id)
    result = execute(cmd, return_output=True, show_cmd=False)
    m = re.search('(\d+)', result[1])
    return int(m.group(1))


def android_start_emu(target_arch):
    pid = os.fork()
    if pid == 0:
        cmd = 'LD_LIBRARY_PATH=%s/adt/sdk/tools/lib %s/adt/sdk/tools/emulator64-%s -gpu on -avd %s -no-audio' % (dir_tool, dir_tool, target_arch, target_arch)
        execute(cmd)
    else:
        info('Starting emulator for ' + target_arch)
        if target_arch == 'x86':
            time.sleep(30)
        else:
            time.sleep(100)


def android_kill_emu(target_arch):
    emu = 'emulator64-%s' % target_arch
    if has_process(emu):
        execute('killall %s' % emu)


def android_get_memory(pkg):
    pass
    #dumpsys meminfo |grep org.chromium.content_shell_apk:sandbo


def android_config_device(device_id, device_product, default, governor='', freq=0):
    count_cpu = device_product_info[device_product]['count_cpu']
    freq_min = device_product_info[device_product]['freq_min']
    freq_max = device_product_info[device_product]['freq_max']
    governor_default = device_product_info[device_product]['governor']
    count_cstate = device_product_info[device_product]['count_cstate']
    if not governor and freq:
        governor = 'powersave'
    if governor == 'performance':
        freq = freq_max
    if not default and (freq < freq_min or freq > freq_max):
        error('The frequency is not in range')

    cmds = []
    for i in range(count_cpu):
        if default:
            cmds.append('echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_governor' % (governor_default, str(i)))
            #cmds.append('echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_setspeed' % ('<unsupported>', str(i)))
            cmds.append('echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_min_freq' % (freq_min, str(i)))
            cmds.append('echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_max_freq' % (freq_max, str(i)))
            for j in range(1, count_cstate):
                cmds.append('echo "0" > /sys/devices/system/cpu/cpu%s/cpuidle/state%s/disable' % (str(i), str(j)))
        else:
            #peeknpoke s w 0 670 0
            cmds.append('echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_governor' % (governor, str(i)))
            #cmds.append('echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_setspeed' % (freq, str(i)))

            # special handle to avoid error during setting if freq < freq_min_old or freq > freq_max_old
            cmd_min = 'echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_min_freq' % (freq, str(i))
            cmd_max = 'echo %s > /sys/devices/system/cpu/cpu%s/cpufreq/scaling_max_freq' % (freq, str(i))
            result = execute(adb(cmd='shell cat /sys/devices/system/cpu/cpu%s/cpufreq/scaling_min_freq' % str(i), device_id=device_id), return_output=True, show_cmd=False)
            freq_min_old = int(result[1])
            if freq < freq_min_old:
                cmds.append(cmd_min)
                cmds.append(cmd_max)
            else:
                cmds.append(cmd_max)
                cmds.append(cmd_min)

            # fix to C0
            for j in range(1, count_cstate):
                cmds.append('echo "1" > /sys/devices/system/cpu/cpu%s/cpuidle/state%s/disable' % (str(i), str(j)))

    su = False
    if device_product == 'V975':
        su = True
    for cmd in cmds:
        execute_adb_shell(cmd=cmd, su=su, device_id=device_id, abort=True)

    if default:
        info('Set governor and freq to default')
    else:
        info('Set governor to %s and freq to %s' % (governor, freq))


def android_enter_dnx(device_id):
    execute('timeout 6s ' + adb(cmd='reboot dnx', device_id=device_id))
    # because dnx mode is basic, assume entering dnx mode will succeed anytime
    sleep_sec = 5
    info('Sleeping %s seconds' % str(sleep_sec))
    time.sleep(sleep_sec)


def android_enter_fastboot(device_id):
    execute('timeout 5s ' + adb(cmd='reboot fastboot', device_id=device_id))
    sleep_sec = 3
    is_connected = False
    for i in range(0, 60):
        if not connect_device(mode='bootloader', device_id=device_id):
            info('Sleeping %s seconds' % str(sleep_sec))
            time.sleep(sleep_sec)
            continue
        else:
            is_connected = True
            break

    if not is_connected:
        error('Can not connect to device in bootloader')


def android_ensure_root(device_id):
    execute(adb(cmd='root', device_id=device_id))
    if connect_device(device_id=device_id, mode='system'):
        execute(adb(cmd='remount', device_id=device_id))
    else:
        error('Can not connect to device')


def android_install_module(device_id, module_path, module_name=''):
    chrome_android_cleanup(device_id=device_id, module_name=module_name)
    execute(adb('install -r %s' % module_path, device_id=device_id))


def android_run_module(device_id, module_name, url=''):
    if not module_name:
        error('Module name must be designated')
    cmd = 'am start -n %s/%s' % (chromium_android_info[module_name][CHROMIUM_ANDROID_INFO_INDEX_PKG],
                                 chromium_android_info[module_name][CHROMIUM_ANDROID_INFO_INDEX_ACT])
    if url:
        cmd += ' -d %s' % url
    execute_adb_shell(cmd, device_id=device_id)


def android_gdb_module(device_id, module_name, target_arch, dir_src, dir_symbol='', build_type='release', dir_out='', verbose=False):
    android_ensure_root(device_id)
    backup_dir(dir_src + '/build/android')
    cmd = ''
    if dir_out:
        cmd += ' CHROMIUM_OUT_DIR=%s' % dir_out
    if dir_symbol:
        cmd += ' SYMBOL_DIR=%s' % dir_symbol

    if re.match('chromium', module_name) or re.match('chrome_example', module_name):
        cmd += ' ./adb_gdb --package-name=%s' % chromium_android_info[module_name][CHROMIUM_ANDROID_INFO_INDEX_PKG]
    else:
        if re.match('webview_shell', module_name):
            cmd += ' ./adb_gdb_android_%s' % module_name
        else:
            cmd += ' ./adb_gdb_%s' % module_name

    if target_arch:
        cmd += ' --target-arch=%s' % target_arch

    if verbose:
        cmd += ' --verbose'

    cmd += ' --%s' % build_type
    cmd += ' --force'
    execute(cmd, interactive=True)
    restore_dir()
## </android>


## <chromium>
# need_fetch: True to get latest rev from upstream. False to get local latest rev.
def chromium_get_rev_max(dir_src, need_fetch=True):
    if not os.path.exists(dir_src):
        error('Chromium src dir %s does not exist' % dir_src)

    backup_dir(dir_src)
    if need_fetch:
        execute('git fetch', dryrun=False)
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
        execute('git fetch', dryrun=False)
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
        execute('git fetch', dryrun=False)
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


def get_capabilities(device_id, target_module, use_running_app=False, args=[]):
    capabilities = {}
    capabilities['chromeOptions'] = {}
    capabilities['chromeOptions']['androidDeviceSerial'] = device_id
    capabilities['chromeOptions']['androidPackage'] = chromium_android_info[target_module][CHROMIUM_ANDROID_INFO_INDEX_PKG]
    capabilities['chromeOptions']['androidUseRunningApp'] = use_running_app
    capabilities['chromeOptions']['args'] = args

    if not chromium_android_info[target_module][CHROMIUM_ANDROID_INFO_INDEX_ISKNOWN]:
        capabilities['chromeOptions']['androidActivity'] = chromium_android_info[target_module][CHROMIUM_ANDROID_INFO_INDEX_ACT]

    return capabilities


def chrome_android_cleanup(device_id='', module_name=''):
    for key in chromium_android_info:
        if not module_name or module_name == key:
            execute(adb('uninstall ' + chromium_android_info[key][CHROMIUM_ANDROID_INFO_INDEX_PKG], device_id=device_id))

    execute(adb('shell rm -rf /data/app-lib/com.android.chrome-1', device_id=device_id))
    #execute(adb('shell rm -rf /data/data/com.example.chromium', device_id=device_id))
    #execute(adb('shell rm -rf /data/dalvik-cache/*', device_id=device_id))


def chrome_android_get_ver_type(device_id=''):
    ver_type = ''
    for key in chromium_android_info:
        if not re.match('^chrom', key):
            continue
        # skip chromium2 as it's a fake to chrome
        if re.match('^chromium2', key):
            continue
        if execute_adb_shell(cmd='pm -l |grep ' + chromium_android_info[key][CHROMIUM_ANDROID_INFO_INDEX_PKG], device_id=device_id):
            ver_type = key
            break

    return ver_type
## </chromium>


## <internal>
def _surpress_warning():
    fileinput
    random


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
    result = execute('git log origin master', show_cmd=False, return_output=True)
    lines = result[1].split('\n')

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


def _msg(msg, show_trace=False):
    m = inspect.stack()[1][3].upper()
    if show_trace:
        m += ', File "%s", Line: %s, Function %s' % inspect.stack()[2][1:4]
    m = '[' + m + '] ' + msg
    # This is legal usage of print
    print m
    execute('echo "%s" >>"%s"' % (m, log), show_cmd=False)


## </internal>
# </functions>
