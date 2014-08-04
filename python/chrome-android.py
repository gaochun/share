# write down how to config
# Preparation:
# pip install selenium
# create x86 and arm emulator (use host GPU)
# history in readme
# apk tool is downloaded from https://code.google.com/p/android-apktool/downloads/list
# http://connortumbleson.com/apktool/test_versions


import urllib2
from util import *

dir_root = ''
vers = []
ver_types = []
target_archs = []
pkg_name = {
    'stable': 'com.android.chrome',
    'beta': 'com.chrome.beta',
    'example': 'com.example.chromium',
}
ver_info = {
    '37.0.2062.39': ['46d1e50f-8dc1-44df-ad64-4fbb7bb7d505', 'f74a8980-294c-42a3-98b3-282b286ee0f6'],
    '36.0.1985.131': ['29bc34f3-d495-4c03-b90e-d07ae3c78345', '14fa9249-9c76-438a-a756-1bca21629e15'],
    '36.0.1985.128': ['bfa72190-1d52-47be-a7ff-4ad5e683992c', '8a5361bf-31af-4d29-93e2-145ec8e99275'],
    '36.0.1985.122': ['', '32de7f58-692c-477f-acde-6d52bda05505'],
    '36.0.1985.94': ['', 'ce2eeca6-ba35-4dd7-8964-97712a7c8969'],
    '36.0.1985.81': ['8c15751f-fe2e-4570-92e0-8f447ae99112', 'df52e853-9c96-41f6-b3b9-7d2e615c356f'],
    '36.0.1985.65':  ['757d2126-de53-4925-b2c4-9c8fe2bd3fea', 'b44048e8-d452-4535-91f2-ac85eff04175'],
    '35.0.1916.141': ['b63d76a9-a8e4-4d2a-ad91-49fe0748a184', '283288f0-3c24-4344-b47a-55088763e809'],
    '36.0.1985.49': ['f2a6afcb-d1ff-4091-9c66-53dee36e44bb', '54b722b8-e2ec-4efd-adc9-57cbf07906bb'],
    '36.0.1985.36': ['68c033b2-f7c4-405f-8c81-b2cb952d3613', '79abd906-96e0-47cf-8ba4-19d4c878c340'],
    '35.0.1916.138': ['e78542a8-1914-4d66-8254-1e56ea1cd5b5', 'b8d5fccd-5008-46cb-b277-dc767429742a'],
    '35.0.1916.122': ['870cde07-60a9-4a21-b72a-859755afaad2', '9cc8db74-d0a6-4a6f-9bf9-352164051a64'],
    '35.0.1916.117': ['08d4d390-3072-49ea-81bb-4b195b8d0507', '11af04e2-4f92-4083-90d1-56d20521ce4d'],
    '35.0.1916.99': ['37882d6c-4608-4051-82fe-9259b4c585dc', '58ccef2a-816e-41a8-9805-1994252ac132'],
    '35.0.1916.86': ['3f060e3f-15b6-4258-a153-d518e1d79151', 'd19af173-64f0-44e2-a6a7-1acef91fa83e'],
    '35.0.1916.69': ['c0ecaab6-d6dd-410b-a8c6-474d34b6991c', '7495204a-ceb1-47cf-8fff-d4974953a7f3'],
    '35.0.1916.48': ['cab313ba-8627-4d7c-b22e-4df70744c6eb', '20568323-6508-493c-89db-f6943c312d7a'],
    '35.0.1916.34': ['fed698ad-f0e9-41a9-8f85-6fe2caa89426', '117432fb-185f-4fe6-a8ba-392a16094a5b'],
    '34.0.1847.114': ['ef9f635c-379d-4300-a5b8-dc18c1f14782', 'a59c168c-e8ad-4532-9e58-5712bb0f8ed6'],
    '33.0.1750.170': ['3559af61-f333-42bb-b1f9-d0df30aa44d6', '6b9b54fc-48aa-4beb-973a-fcf61504e34e'],
    '34.0.1847.99': ['47f1b631-812d-4c32-8fb9-dbe312dc64ae', '663c3465-afe8-4abb-94d0-44656d11b313'],
    '34.0.1847.76': ['f8480155-7e4b-49dc-907a-04124848695d', 'a43bcb82-b121-41b9-a8be-60ce309171ca'],
    '33.0.1750.166': ['bc468ba0-d60e-44a7-ab8a-46a92af3eb95', '0e5b0784-1010-4ca5-9efc-2697ba93a6c8'],
    '34.0.1847.62': ['f7e92034-f602-4e2d-a483-8b5f034ab199', '2efbe11b-f0b2-4e6d-9374-b1906e68c782'],
    '34.0.1847.45': ['', 'da6688dc-d769-4a16-bdd0-230def75453d'],
    '33.0.1750.136': ['', '582969eb-6f20-4ee1-88f2-8252611c1e60'],
    '33.0.1750.132': ['b1c0cc3c-e397-4a22-83ea-c2fbde2a78dc', 'd63a51d9-67b6-4122-b838-5c375b8a8114'],
}


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script about chrome for android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --ver-type stable --target-arch x86
''')
    parser.add_argument('--ver', dest='ver', help='version', default='all')
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='all')
    parser.add_argument('--run', dest='run', help='run', action='store_true')
    parser.add_argument('--buildid', dest='buildid', help='buildid', action='store_true')
    parser.add_argument('--check', dest='check', help='check', action='store_true')
    parser.add_argument('--backup', dest='backup', help='backup', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, vers, ver_types, target_archs

    dir_root = get_symbolic_link_dir()

    if args.ver_type == 'all':
        ver_types = ['stable', 'beta']
    else:
        ver_types = args.ver_type.split(',')

    if args.target_arch == 'all':
        target_archs = ['x86', 'arm']
    else:
        target_archs = args.target_arch.split(',')


def run():
    if not args.run:
        return

    if not os.path.exists(chrome_android_dir_server_todo):
        os.makedirs(chrome_android_dir_server_todo)
        return

    cmd_common = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome'
    backup_dir(chrome_android_dir_server_todo)
    todos = os.listdir('.')
    execute('rm -rf temp')
    for todo in todos:
        if os.path.isfile(todo):
            cmd = cmd_common + ' --dir-root ' + chrome_android_dir_server_todo
            cmd += ' --chrome-android-apk ' + todo
            cmd += ' --buildid'
            execute(cmd, interactive=True)
        elif os.path.isdir(todo):
            target_arch_temp = todo
            if target_arch_temp not in target_arch_all:
                continue

            dirs_todo = os.listdir(chrome_android_dir_server_todo + '/' + target_arch_temp)
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


def check():
    if not args.check:
        return

    # get all the combos
    url = 'http://www.hiapphere.org/app-chrome_beta'
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
        if not ver_ge(ver, '33.0.1750.132'):
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
        dirs_todo = os.listdir(chrome_android_dir_server_todo + '/%s' % target_arch)
        combos_todo += _get_combos(dirs_todo, target_arch)

    combos_new = sorted(list_diff(combos_all, list_union(combos_done, combos_todo)))
    info('The following combos need to be downloaded: ' + ','.join(str(i) for i in combos_new))


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


if __name__ == "__main__":
    parse_arg()
    setup()
    run()
    check()
    backup()
