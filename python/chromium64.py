from util import *

root_dir = ''
webview_dir = ''
repos = []
android_target_arch = ''
chromium_target_arch = ''

patches = [
    # Patches borrowed from other groups

    # Patches by our own
    'git fetch https://aia-review.intel.com/platform/bionic refs/changes/00/3200/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/build refs/changes/25/3025/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/95/2395/2 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/26/3026/3 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/57/3357/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/94/3194/4 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/third_party/icu refs/changes/27/3027/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/third_party/openssl refs/changes/28/3028/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/v8 refs/changes/29/3029/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/frameworks/av refs/changes/92/3192/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/libnativehelper refs/changes/49/3049/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/libnativehelper refs/changes/30/3030/2 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/system/core refs/changes/03/3203/1 && git checkout FETCH_HEAD',
]

dirty_repos = [
    # Repos that possible ever patched. This list is not consistent with
    # patches, it will list all patched repos in histroy.
    'bionic',
    'build',
    'external/chromium',
    'external/chromium_org',
    'external/chromium_org/third_party/icu',
    'external/chromium_org/third_party/openssl',
    'external/chromium_org/v8',
    'frameworks/av',
    'frameworks/native',
    'libnativehelper',
    'system/core',
]

################################################################################


def _ensure_repos():
    global repos

    if len(repos) > 0:
        return

    backup_dir(webview_dir)
    r = os.popen('find -name ".git"')
    lines = r.read().split('\n')
    del lines[len(lines) - 1]
    for repo in lines:
        repo = repo.replace('./', '')
        repo = repo.replace('.git', '')
        repos.append(webview_dir + '/' + repo)

    for repo in dirty_repos:
        if not re.match('external/chromium_org', repo):
            repos.append(root_dir + '/' + repo)


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to sync, build Chromium x64',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s --sync-local
  python %(prog)s --mk64
  python %(prog)s -b --build-showcommands --build-onejob

  python %(prog)s --dep
''')
    group_sync = parser.add_argument_group('sync')
    group_sync.add_argument('-s', '--sync', dest='sync', help='sync the repo', action='store_true')
    group_sync.add_argument('--sync-local', dest='sync_local', help='only update working tree, not fetch', action='store_true')

    group_patch = parser.add_argument_group('patch')
    group_patch.add_argument('--patch', dest='patch', help='apply patches from Gerrit', action='store_true')

    group_clean = parser.add_argument_group('clean')
    group_clean.add_argument('--clean', dest='clean', help='clean patches from Gerrit', action='store_true')

    group_mk64 = parser.add_argument_group('mk64')
    group_mk64.add_argument('--mk64', dest='mk64', help='generate mk for x86_64', action='store_true')

    group_build = parser.add_argument_group('build')
    group_build.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    group_build.add_argument('--build-dep', dest='build_dep', help='build with dependencies', action='store_true')
    group_build.add_argument('--build-showcommands', dest='build_showcommands', help='build with detailed command', action='store_true')
    group_build.add_argument('--build-onejob', dest='build_onejob', help='build with one job, and stop once failure happens', action='store_true')

    group_other = parser.add_argument_group('other')
    group_other.add_argument('-r', '--repo', dest='repo', help='repo', choices=['chromium_org', 'emu', 'bridge', 'all'], default='chromium_org')
    group_other.add_argument('-d', '--root-dir', dest='root_dir', help='set root directory')
    group_other.add_argument('--dep', dest='dep', help='get dep for each module', action='store_true')
    group_other.add_argument('--git-status', dest='git_status', help='git status for repos', action='store_true')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global root_dir, webview_dir, android_target_arch, chromium_target_arch

    if not args.root_dir:
        root_dir = os.path.abspath(os.getcwd())
    else:
        root_dir = args.root_dir

    webview_dir = root_dir + '/external/chromium_org'
    os.chdir(root_dir)
    android_target_arch = 'x86_64'
    chromium_target_arch = 'x64'

    _ensure_repos()


def sync():
    if not args.sync:
        return

    command = 'repo sync -c -j16'
    if args.sync_local:
        command += ' -l'
    execute(command)


def patch():
    if not args.patch:
        return

    for patch in patches:
        pattern = re.compile('platform/(.*) (.*) &&')
        match = pattern.search(patch)
        repo = match.group(1)
        change = match.group(2)
        backup_dir(root_dir + '/' + repo)

        command = 'git fetch ssh://aia-review.intel.com/platform/' + repo + ' ' + change
        execute(command, silent=True, catch=True)
        result = execute('git show FETCH_HEAD |grep Change-Id:', catch=True, silent=True)

        pattern = re.compile('Change-Id: (.*)')
        change_id = result[1]
        match = pattern.search(change_id)
        result = execute('git log |grep ' + match.group(1), catch=True, silent=True, abort=False)
        if result[0]:
            execute('git cherry-pick FETCH_HEAD')
        else:
            info('Patch has been cherry picked, so it will be skipped: ' + patch)

        restore_dir()


def clean():
    if not args.clean:
        return

    warning('Clean is very dangerous, your local changes will be lost')
    sys.stdout.write('Are you sure to do the cleanup? [yes/no]: ')
    choice = raw_input().lower()
    if choice not in ['yes', 'y']:
        return

    for repo in dirty_repos:
        backup_dir(root_dir + '/' + repo)
        execute('git reset --hard aia/topic/64-bit/master', silent=True, catch=True)
        info(repo + ' is resetted to aia/topic/64-bit/master')
        restore_dir()


def mk64():
    if not args.mk64:
        return

    backup_dir(webview_dir)

    # Remove all the x64 mk files
    r = os.popen('find -name "*x86_64*.mk" -o -name "*x64*.mk"')
    files = r.read().split('\n')
    del files[len(files) - 1]
    for file in files:
        os.remove(file)

    # Generate raw .mk files
    command = bashify('export CHROME_ANDROID_BUILD_WEBVIEW=1 && . build/android/envsetup.sh --target-arch=' + chromium_target_arch + ' && android_gyp -Dwerror= ')
    execute(command)

    # Generate related x64 files according to raw .mk files
    file = open('GypAndroid.mk')
    lines = file.readlines()
    file.close()

    fw = open('GypAndroid.linux-' + android_target_arch + '.mk', 'w')

    # auto_x64 -> x64: target->target.linux-<android_target_arch>, host->host.linux-<android_target_arch>
    for line in lines:
        pattern = re.compile('\(LOCAL_PATH\)/(.*)')
        match = pattern.search(line)
        if match:
            auto_x64_file = match.group(1)
            x64_file = auto_x64_file.replace('target', 'target.linux-' + android_target_arch)
            x64_file = x64_file.replace('host', 'host.linux-' + android_target_arch)
            command = 'cp -f ' + auto_x64_file + ' ' + x64_file
            execute(command, True)

            line = line.replace('target', 'target.linux-' + android_target_arch)
            line = line.replace('host', 'host.linux-' + android_target_arch)
        fw.write(line)

    fw.close()

    # Check if x86 version has corresponding <target_arch> version
    # x86 -> x64: x86-><target_arch>, ia32-><target_arch>
    r = os.popen('find -name "*linux-x86.mk"')
    files = r.read().split('\n')
    del files[len(files) - 1]

    for x86_file in files:
        x64_file = x86_file.replace('x86', android_target_arch)
        x64_file = x64_file.replace('ia32', 'x64')
        if not os.path.exists(x64_file):
            print 'x64 version does not exist: ' + x86_file

    info('Number of x86 mk: ' + os.popen('find -name "*linux-x86.mk" |wc -l').read()[:-1])
    info('Number of x64 mk: ' + os.popen('find -name "*linux-' + android_target_arch + '.mk" |wc -l').read()[:-1])

    restore_dir()


def build():
    if not args.build:
        return

    backup_dir(root_dir)
    command = '. ' + root_dir + '/build/envsetup.sh && lunch emu64-eng && '

    if args.repo == 'emu':
        command += 'make emu'
    else:
        if args.build_dep:
            command += 'mmma '
        else:
            command += 'mmm '

        if args.repo == 'bridge':
            command += 'frameworks/webview'
        elif args.repo == 'chromium_org':
            command += 'external/chromium_org'

        if args.build_showcommands:
            command += ' showcommands'

    if not args.build_onejob:
        command += ' -j16 -k'

    command += ' 2>&1 |tee ' + root_dir + '/' + args.repo + '_log'

    command = bashify(command)
    execute(command, duration=True)
    restore_dir()


def git_status():
    if not args.git_status:
        return

    has_change = False
    repos_change = []

    for repo in repos:
        backup_dir(repo)
        result = execute('git status |grep modified', silent=True, catch=True, abort=False)
        if not result[0]:
            has_change = True
            repos_change.append(repo)
            #print result[1]
        restore_dir()

    if has_change:
        info('The following repos have changes: ' + ','.join(repos_change))
    else:
        info('There is no change at all')


def dep():
    if not args.dep:
        return

    backup_dir(webview_dir)
    libraries = set()

    file = open('GypAndroid.linux-' + android_target_arch + '.mk')
    lines = file.readlines()
    file.close()

    module_prev = ''
    for line in lines:
        pattern = re.compile('\(LOCAL_PATH\)/(.*)')
        match = pattern.search(line)
        if match:
            mk_file = match.group(1)

            fields = mk_file.split('/')
            module = fields[0]
            if module == 'third_party':
                module = fields[1]

            if module == 'skia':
                continue

            if module_prev != module:
                module_prev = module
                #print '[' + module + ']'

            file = open(mk_file)
            lines = file.readlines()
            file.close()

            i = 0
            while (i < len(lines)):
                if re.match('LOCAL_SHARED_LIBRARIES', lines[i]):
                    i += 1
                    while (lines[i].strip()):
                        library = lines[i].strip()
                        index = library.find('\\')
                        if index > 0:
                            library = library[0:index]
                        libraries.add(library)
                        #print library
                        i += 1
                else:
                    i += 1

    s = ''
    for library in libraries:
        if s == '':
            s = library
        else:
            s += ' ' + library
    print 'Shared libraries: ' + s

    restore_dir()


if __name__ == '__main__':
    handle_option()
    setup()
    sync()
    patch()
    clean()
    mk64()
    build()
    git_status()
    dep()
