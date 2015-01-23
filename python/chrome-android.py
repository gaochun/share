# Preparation:
# Emulator: Used for build id and verification. Download the adt, and create x86 and arm emulators (use host GPU)
# Webdriver: Used for build id and verification. pip install selenium, and download chromedriver
# Apk tool: Download it from http://connortumbleson.com/apktool/test_versions
# Download:
#    Install Chrome
#    Set its download directory as /workspace/server/chromium/android-chrome-todo/download
#    Open it with google-chrome --user-data-dir=/workspace/tool/chrome-android/arm/chrome-profile
#    Open it with google-chrome --user-data-dir=/workspace/tool/chrome-android/x86/chrome-profile
#    Install extension SwitchySharp
#    Install extension at share/python/apk-downloader
#    Login extension with: webperf0@gmail.com and 32761AAE6636D2A3(arm)/376FCD341892D871(x86) as device id.
# gms: put a folder with any name in buildid, which contains the Chrome.apk and lib

# backup:
# 1. Run this script with '--backup-ver xxx', which will backup all the versions <= xxx to the server (path_server_backup).
# 2. Ensure the backups are created at server, remove backuped folders manually.

from selenium import webdriver
import urllib2
from util import *

dir_root = ''
vers = []
ver_types = []
target_archs = []
local_ver = ''
local_ver_type = ''
local_target_arch = ''
run_act = 0

ACT_DOWNLOAD = 1 << 0
ACT_FILE = 1 << 1
ACT_DIR = 1 << 2
ACT_CHECK = 1 << 3
ACT_DISK = 1 << 4
ACT_ALL = ACT_DOWNLOAD | ACT_FILE | ACT_DIR | ACT_CHECK | ACT_DISK

cmd_common = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome'

devices_id = []


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script about chrome for android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --ver-type stable --target-arch x86
  python %(prog)s --ver 39.0.2171.54 --ver-type beta --target-arch x86 --local-setup
''')
    parser.add_argument('--run', dest='run', help='run', action='store_true')
    parser.add_argument('--run-act', dest='run_act', help='run act', type=int, default=ACT_ALL)
    parser.add_argument('--check', dest='check', help='check if there is new apk', action='store_true')
    parser.add_argument('--disk', dest='disk', help='check disk available space', action='store_true')
    parser.add_argument('--download', dest='download', help='download apk from google play', action='store_true')
    parser.add_argument('--download_type', dest='download_type', help='version type to download', default='all')
    parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
    parser.add_argument('--backup-ver', dest='backup_ver', help='backup versions less than the designated')
    parser.add_argument('--local-setup', dest='local_setup', help='setup local environment to build and debug', action='store_true')
    parser.add_argument('--local-build', dest='local_build', help='build local chromium.apk and library with symbols', action='store_true')

    parser.add_argument('--ver', dest='ver', help='version', default='all')
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='all')
    parser.add_argument('--debug', dest='debug', help='debug chromium with GDB', action='store_true')
    parser.add_argument('--analyze', dest='analyze', help='analyze test tombstone', action='store_true')
    parser.add_argument('--analyze-type', dest='analyze_type', help='type to analyze', choices=['tombstone', 'anr'], default='tombstone')
    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global vers, ver_types, target_archs, run_act
    global dir_root, log, timestamp

    (timestamp, dir_root, log) = setup_common(args, _teardown)
    dir_root = dir_project + '/chrome-android'

    if args.ver_type == 'all':
        ver_types = ['stable', 'beta']
    else:
        ver_types = args.ver_type.split(',')

    if args.target_arch == 'all':
        target_archs = ['x86', 'arm']
    else:
        target_archs = args.target_arch.split(',')

    for target_arch in target_archs:
        dir_temp = dir_server_chromium + '/android-%s-chrome/archive' % target_arch
        if not os.path.exists(dir_temp):
            os.makedirs(dir_temp)

    ensure_dir(dir_server_chrome_android_todo)
    run_act = args.run_act


def run(force=False, act=ACT_ALL):
    if not args.run and not force:
        return

    if act & ACT_DOWNLOAD:
        download(force=True)

    if act & ACT_FILE:
        _handle_todo_file()

    if act & ACT_DIR:
        _handle_todo_dir()

    if act & ACT_CHECK:
        check(force=True)

    if act & ACT_DISK:
        disk(force=True)


def download(force=False):
    if not args.download and not force:
        return

    dir_download = dir_server_chrome_android_todo + '/download'
    ensure_dir(dir_download)
    execute('rm -rf %s/*' % dir_download)

    dir_trash = dir_server_chrome_android_todo + '/trash'
    ensure_dir(dir_trash)

    # download the apk
    for target_arch in target_arch_chrome_android:
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['user-data-dir', 'ignore-certificate-errors', 'disable-default-apps'])
        options.add_argument('user-data-dir=%s' % (dir_tool + '/chrome-android/' + target_arch + '/chrome-profile'))
        driver = webdriver.Chrome(executable_path=tool_chromedriver, chrome_options=options, service_args=['--verbose', '--log-path=%s/chromedriver-%s.log' % (dir_share_ignore_log, timestamp)])

        if args.download_type == 'all' or args.download_type == 'stable':
            driver.get('https://play.google.com/store/apps/details?id=' + chromium_android_info['chrome_stable'][CHROMIUM_ANDROID_INFO_INDEX_PKG])
        time.sleep(3)
        if args.download_type == 'all' or args.download_type == 'beta':
            driver.get('https://play.google.com/store/apps/details?id=' + chromium_android_info['chrome_beta'][CHROMIUM_ANDROID_INFO_INDEX_PKG])

        finished = False
        while not finished:
            finished = True
            files = os.listdir(dir_download)
            if not files:
                finished = False
            else:
                for f in files:
                    if re.search('crdownload', f):
                        finished = False
                        break

            if not finished:
                time.sleep(3)

        driver.quit()

    execute('mv %s/* %s' % (dir_download, dir_server_chrome_android_todo_buildid), dryrun=False)


def check(force=False):
    if not args.check and not force:
        return

    info('Begin to check..')
    content = ''
    subject = ''

    # get all the combos
    url = 'http://www.hiapphere.com/app-chrome_beta'
    try:
        u = urllib2.urlopen(url)
    except BadStatusLine:
        warning('Failed to open ' + url)
        return

    html = u.read()
    pattern = re.compile('Version(\d+\.\d+\.\d+\.\d+)')
    vers_all = pattern.findall(html)
    combos_all = []
    for ver in vers_all:
        if ver_cmp(ver, '33.0.1750.132') < 0:
            continue
        for target_arch in target_arch_chrome_android:
            combos_all.append((target_arch, ver))

    # get all combos done
    combos_done = []
    for target_arch in target_arch_chrome_android:
        dirs_done = os.listdir(dir_server_chromium + '/android-%s-chrome' % target_arch)
        dirs_done += os.listdir(dir_server_chromium + '/android-%s-chrome/archive' % target_arch)
        combos_done += _get_combos(dirs_done, target_arch)

    # get all combos todo
    combos_todo = []
    for target_arch in target_arch_chrome_android:
        dirs_todo = os.listdir(dir_server_chrome_android_todo + '/%s' % target_arch)
        combos_todo += _get_combos(dirs_todo, target_arch)

    combos_new = sorted(list_diff(combos_all, list_union(combos_done, combos_todo)))

    if len(combos_new):
        subject += ' download required'
        content += 'The following combos need to be downloaded: ' + ','.join(str(i) for i in combos_new) + '<br>'
    else:
        subject += ' download clean'

    if len(combos_todo):
        subject += ' build required'
        content += 'The following combos need to be built: ' + ','.join(str(i) for i in combos_todo) + '<br>'
    else:
        subject += ' build clean'

    info(content)
    if host_name == 'wp-03':
        to = ['yang.gu@intel.com', 'zhiqiangx.yu@intel.com']
        send_mail('webperf@intel.com', to, 'Chrome for Android -' + subject, content, type='html')


def disk(force=False):
    if not args.disk and not force:
        return

    avail = get_avail_disk() / 1024 / 1024
    if avail < 200:
        to = ['yang.gu@intel.com', 'zhiqiangx.yu@intel.com']
        subject = ' Disk available space is too low (%sG)' % str(avail)
        content = ''
        send_mail('webperf@intel.com', to, 'Chrome for Android -' + subject, content, type='html')


def backup():
    if not args.backup:
        return

    for target_arch in target_arch_chrome_android:
        dirs = os.listdir(dir_server_chromium + '/android-%s-chrome' % target_arch)
        for dir_temp in dirs:
            if dir_temp == 'archive':
                continue

            info_temp = dir_temp.split('-')
            ver_temp = info_temp[0]
            ver_type_temp = info_temp[1]

            dir_chrome = 'chromium/android-%s-chrome/%s-%s' % (target_arch, ver_temp, ver_type_temp)
            execute('smbclient %s -N -c "prompt; recurse; mkdir %s;"' % (path_server_backup, dir_chrome))
            backup_dir(dir_server + '/' + dir_chrome)
            if os.path.exists('Chrome.apk'):
                backup_smb(path_server_backup, dir_chrome, 'Chrome.apk')
                backup_smb(path_server_backup, dir_chrome, 'Chromium.apk')
                backup_smb(path_server_backup, dir_chrome, 'README')
            else:
                backup_smb(path_server_backup, dir_chrome, 'Null.apk')
            restore_dir()


def backup_ver():
    if not args.backup_ver:
        return

    vers = []
    dirs = os.listdir('.')
    for dir_ver in dirs:
        if re.match('\d+\.\d+\.\d+\.\d+', dir_ver) and ver_cmp(dir_ver, args.backup_ver) <= 0:
            vers.append(dir_ver)

    vers = sorted(vers, cmp=ver_cmp)
    count_process = min(count_cpu, len(vers))
    pool = Pool(processes=count_process)
    for ver in vers:
        pool.apply_async(_backup_ver_one, (ver,))

    pool.close()
    pool.join()


def local_setup():
    if not args.local_setup:
        return

    _get_local_info()

    ensure_dir(dir_workspace)
    execute('sudo chown -R %s:%s %s' % (username, username, dir_workspace), interactive=True)
    ensure_dir(dir_project_chrome_android)
    dir_server_chrome_android_todo_apk = '%s/%s/%s-%s' % (dir_server_chrome_android_todo, local_target_arch, local_ver, local_ver_type)
    ensure_dir(dir_server_chrome_android_todo_apk)

    backup_dir(dir_server_chrome_android_todo_apk)
    execute('scp %s@%s:%s/android-%s-chrome/%s-%s/README ./' % (server_chromeforandroid[SERVERS_INDEX_USERNAME],
                                                                server_chromeforandroid[SERVERS_INDEX_HOSTNAME],
                                                                dir_server_chromium,
                                                                local_target_arch, local_ver, local_ver_type), interactive=True)
    execute('scp %s@%s:%s/android-%s-chrome/%s-%s/Chrome.apk ./' % (server_chromeforandroid[SERVERS_INDEX_USERNAME],
                                                                    server_chromeforandroid[SERVERS_INDEX_HOSTNAME],
                                                                    dir_server_chromium,
                                                                    local_target_arch, local_ver, local_ver_type), interactive=True)
    file_readme = '%s/%s/%s-%s/README' % (dir_server_chrome_android_todo, local_target_arch, local_ver, local_ver_type)
    _set_phase(file_readme, 'patch')
    restore_dir()

    backup_dir(dir_project_chrome_android)
    if os.path.exists('%s/%s' % (dir_project_chrome_android, local_ver)):
        info('The source code of chrome-%s_%s have been downloaded' % (local_ver_type, local_ver))
    else:
        execute('ssh %s@%s "cd %s; tar -zcvf - %s" | tar xzf - %s' % (server_chromeforandroid[SERVERS_INDEX_USERNAME],
                                                                      server_chromeforandroid[SERVERS_INDEX_HOSTNAME],
                                                                      dir_project_chrome_android,
                                                                      local_ver,
                                                                      local_ver), interactive=True)
    restore_dir()


def local_build():
    if not args.local_build:
        return

    _get_local_info()

    cmd = cmd_common + ' --dir-root ' + dir_root + '/' + local_ver
    cmd += ' --target-arch ' + local_target_arch
    cmd += ' --ver ' + local_ver
    cmd += ' --ver-type ' + local_ver_type
    cmd += ' --phase-end postbuild --phase-continue'
    execute(cmd, interactive=True)


def debug():
    if not args.debug:
        return

    _setup_device()
    _get_local_info()

    module_name = 'chromium_' + local_ver_type
    device_id = devices_id[0]
    dir_src = '%s/%s/src' % (dir_project_chrome_android, local_ver)
    dir_out = 'out-%s/out' % local_target_arch
    dir_symbol = '%s/%s/%s-%s' % (dir_server_chrome_android_todo, local_target_arch, local_ver, local_ver_type)

    android_install_module(device_id, dir_symbol + '/Chromium.apk', module_name)
    android_run_module(device_id, module_name)
    android_gdb_module(device_id, module_name, local_target_arch, dir_src, dir_symbol=dir_symbol, dir_out=dir_out)


def analyze():
    if not args.analyze:
        return

    _setup_device()
    lines = analyze_file(device_id=devices_id[0], type=args.analyze_type)
    dirs_symbol = []
    pattern = re.compile('libchrome\.(.*)\.so')
    for line in lines:
        match = pattern.search(line)
        if match:
            ver_part = match.group(1)
            break

    for dir_temp in [dir_server_chromium + '/android-x86-chrome', dir_server_chromium + '/android-chrome-todo/x86']:
        dirs = os.listdir(dir_temp)
        for d in dirs:
            if re.search(ver_part, d):
                dirs_symbol.append(dir_temp + '/' + d)
                break

    get_symbol(lines, dirs_symbol)


def _setup_device():
    global devices_id, devices_product, devices_type, devices_arch, devices_mode

    if devices_id:
        return

    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device()


def _get_combos(dirs_check, target_arch):
    combos = []
    pattern = re.compile('(\d+\.\d+\.\d+\.\d+)-(stable|beta)')

    for dir_check in dirs_check:
        match = pattern.search(dir_check)
        if not match:
            continue
        ver_temp = match.group(1)

        combos.append((target_arch, ver_temp))

    return combos


def _handle_todo_file():
    backup_dir(dir_server_chrome_android_todo_buildid)
    todos = os.listdir('.')
    for todo in todos:
        if os.path.isdir(todo):
            cmd = cmd_common + ' --dir-root ' + dir_server_chrome_android_todo_buildid + '/' + todo
            cmd += ' --chrome-android-apk Chrome.apk'
            cmd += ' --buildid'
            execute(cmd, interactive=True)
        elif os.path.isfile(todo):
            cmd = cmd_common + ' --dir-root ' + dir_server_chrome_android_todo_buildid
            cmd += ' --chrome-android-apk "' + todo + '"'
            cmd += ' --buildid'
            execute(cmd, interactive=True)

    restore_dir()


def _handle_todo_dir():
    backup_dir(dir_server_chrome_android_todo)
    todos = os.listdir('.')
    for todo in todos:
        if os.path.isdir(todo):
            target_arch_temp = todo
            if target_arch_temp not in target_archs:
                continue

            dirs_todo = os.listdir(dir_server_chrome_android_todo + '/' + target_arch_temp)
            for dir_todo in dirs_todo:
                info = dir_todo.split('-')
                ver_temp = info[0]
                ver_type_temp = info[1]

                cmd = cmd_common + ' --dir-root ' + dir_root + '/' + ver_temp
                cmd += ' --target-arch ' + target_arch_temp
                cmd += ' --ver ' + ver_temp
                cmd += ' --ver-type ' + ver_type_temp
                cmd += ' --phase-continue'

                execute(cmd, interactive=True)
    restore_dir()


def _get_local_info():
    global local_ver, local_ver_type, local_target_arch

    if local_ver or local_ver_type or local_target_arch:
        return

    if args.ver == 'all' or args.ver_type == 'all' or args.target_arch == 'all':
        error('Please designate chrome ver(--ver), ver_type(--ver_type) and target_arch(--target_arch)')
    else:
        local_ver = args.ver
        local_ver_type = args.ver_type
        local_target_arch = args.target_arch


def _set_phase(file_readme, phase):
    pattern = re.compile('phase=(.*)')
    for line in fileinput.input(file_readme, inplace=1):
        match = pattern.search(line)
        if match:
            line = 'phase=' + phase + '\n'
        sys.stdout.write(line)


def _backup_ver_one(ver):
    # Speed:
    # plain tar: 37min

    info('Backing up ' + ver)
    execute('tar zcf %s.tar.gz %s' % (ver, ver), show_cmd=False)
    #execute('tar cf - %s | pigz -p 32 > %s.tar.gz' % (ver, ver), show_cmd=False, dryrun=False)
    backup_smb(path_server_backup, 'chromium', '%s.tar.gz' % ver)
    info('Version %s has been backed up' % ver)


def _teardown():
    pass


if __name__ == "__main__":
    parse_arg()
    setup()
    run(act=run_act)
    check()
    download()
    backup()
    backup_ver()
    local_setup()
    local_build()
    debug()
    analyze()
    disk()
