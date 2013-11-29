# TODO
# run tasks in parallel
# print compilation option, times

from util import *

import time
import urllib2
from httplib import BadStatusLine

device_to_target = {}

root_dir_default = '/workspace/project/skia/'
log_dir_default = root_dir_default + 'log/'
root_dir = ''
log_dir = ''
src_dir = ''
platform_tools_dir = ''
toolchain_dir = ''
gdb_server_path = ''
gdb_client_path = ''

android_sdk_root = '/workspace/topic/skia/adt-bundle-linux-x86_64/sdk'
log_suffix = '.txt'
config = ['8888', '565', 'GPU', 'NULLGPU', 'NONRENDERING']
config_concerned = [0, 0, 1, 0, 1]
NA = 'NA'
ONLINE = 'online'
OFFLINE = 'offline'
X86 = 'x86'
INTEL_RHB = 'intel_rhb'
NEXUS4 = 'nexus_4'
UNKNOWN = 'unknown'
HOST = 'host'
SMALL_NUMBER = 0.000001
LARGE_NUMBER = 10000
REPEAT_TIMES = '20'

def avg(self):
        if len(self.sequence) < 1:
            return None
        else:
            return sum(self.sequence) / len(self.sequence)

def get_data(name, result):
    for item in result:
        if item[0] == name:
            data = map(float, item[1].split(','))
            avg = sum(data) / len(data)
            return '%.2f' %avg

    return NA

def _get_device_to_target():
    global device_to_target
    if len(device_to_target) > 0:
        return

    command = 'adb devices -l'
    device_lines = commands.getoutput(command).split('\n')
    for device_line in device_lines:
        if re.match('List of devices attached', device_line):
            continue
        elif re.match('^\s*$', device_line):
            continue

        device = device_line.split(' ')[0]
        if re.search('redhookbay|BayTrail|Baytrail', device_line):
            device_to_target[device] = (X86, ONLINE)
        elif re.search('Medfield', device_line):
            device_to_target[device] = (X86, ONLINE)
        elif re.search('mako', device_line):
            device_to_target[device] = (NEXUS4, ONLINE)
        elif re.search('Nexus_4', device_line):
            device_to_target[device] = (NEXUS4, ONLINE)
        else:
            device_to_target[device] = (UNKNOWN, ONLINE)

    device_to_target_fixup = {'32300bd273508f3b': NEXUS4}
    for device in device_to_target_fixup:
        if device_to_target.has_key(device):
            device_to_target[device] = (device_to_target_fixup[device], ONLINE)
        else:
            device_to_target[device] = (device_to_target_fixup[device], OFFLINE)

    device_to_target[HOST] = (HOST, ONLINE)

def remote_debug():
    if not args.remote_debug:
        return

    backup_dir(src_dir)
    execute('platform_tools/android/bin/android_gdb_exe ' + args.test_type + ' ' + args.run_option)
    restore_dir()

def recover():
    if not args.recover:
        return

    _get_device_to_target()

    for device in device_to_target:
        if device_to_target[device][1] == ONLINE and device_to_target[device][0] != HOST:
            execute('adb -s ' + device + ' shell start')

def _parse_format_result(dir, log_file, results):
    backup_dir(dir)
    fr = open(log_file)
    lines = fr.readlines()
    fr.close()

    for line in lines:
        # Skip blank line
        if re.match('^\s+$', line):
            continue
        # Skip title
        if re.match('Name 8888 565 GPU NULLGPU NONRENDERING', line):
            continue

        p = re.compile('\S+')
        results.append(re.findall(p, line))

    restore_dir()

def average():
    average_dir = args.average
    backup_dir(log_dir)
    total_result = []
    total_number = 0

    files = os.listdir(average_dir)
    for file in files:
        if not re.search('format', file):
            continue

        total_number += 1
        if total_number == 1:
            _parse_format_result(average_dir, file, total_result)
            continue

        temp_result = []
        _parse_format_result(average_dir, file, temp_result)

        for i in range(len(temp_result)):
            if temp_result[i][0] != total_result[i][0]:
                error('Results to calculate average do not have same format')
                quit()

            for j in range(1, len(config) + 1):
                if temp_result[i][j] == 'NA' or total_result[i][j] == 'NA':
                    total_result[i][j] = 'NA'
                    if temp_result[i][j] != total_result[i][j]:
                        error('One of result is NA, while the other is not')
                        quit()
                else:
                    total_result[i][j] = float(total_result[i][j]) + float(temp_result[i][j])

    dirs = average_dir.split('/')
    if dirs[-1] == '':
        dir_name = dirs[-2]
    else:
        dir_name = dirs[-1]
    fw = open(average_dir + '/' + dir_name + '-average' + log_suffix, 'w')
    fw.write('Name ' + ' '.join(config) + '\n')
    for r in total_result:
        s = r[0]
        for i in range(1, len(config) + 1):
            if r[i] == 'NA':
                s += ' NA'
            else:
                s += ' ' + str(r[i] / total_number)
        s += '\n'
        fw.write(s)
    fw.close()

    restore_dir()

def parse_result(dir, log_file):
    if args.test_type != 'bench':
        return

    backup_dir(dir)

    format_file = log_file.replace('origin', 'format')
    if os.path.exists(format_file):
        os.remove(format_file)

    fr = open(log_file)
    lines = fr.readlines()
    fr.close()

    fw = open(format_file, 'w')
    fw.write('Name ' + ' '.join(config) + '\n')

    line_index = 0
    matches = []
    while line_index < len(lines):
        #print lines[line_index]
        if re.search('beginning of /dev/log/main', lines[line_index]):
            break

        pattern = re.compile('(' + '|'.join(config) + '):.+?cmsecs =\s+([^ \t\n\r\f\v[a-zA-Z]*)[a-zA-Z]*\s*')
        if re.search('running bench', lines[line_index]):
            if len(matches):
                for i in range(len(config)):
                    s = s + ' ' + get_data(config[i], matches)
                fw.write(s + '\n')

            p = re.compile('running bench \[\s*\d+\s*\d+\]\s+(\S+)')
            m = re.search(p, lines[line_index])
            s = m.group(1)
            matches = []

        for m in re.findall(pattern, lines[line_index]):
            matches.append(m)
        line_index += 1

    if len(matches):
        for i in range(len(config)):
            s = s + ' ' + get_data(config[i], matches)
        fw.write(s + '\n')

    fw.close()

    restore_dir()

def download():
    if not args.download:
        return

    if args.test_type != 'bench':
        return

    backup_dir(log_dir)

    if args.download not in ['nexus10', 'nexus4']:
        error('Device to download is not supported now')
        quit()

    # Get latest build number
    url = 'http://108.170.217.252:10117/console?reload=40&repository=http://skia.googlecode.com/svn&revs=20&limit=50&category=Perf|Android'
    try:
        u = urllib2.urlopen(url)
    except BadStatusLine:
        error('Failed to visit waterfall')

    html = u.read()
    pattern = re.compile('Perf-Android-Nexus10-MaliT604-Arm7-Release&number=(\d+)')
    match = pattern.search(html)
    if match:
        build_number = match.group(1)
    else:
        error('Could not get the build number to download')
        quit

    info('Latest build number is ' + build_number)

    # Get log for specific build number
    if args.download == 'nexus10':
        link = 'Nexus10-MaliT604'
    elif args.download == 'nexus4':
        link = 'Nexus4-Adreno320'
    origin_file = link + '-Arm7-' + str(build_number) + '-bench-origin' + log_suffix

    if os.path.exists(origin_file):
        info(origin_file + ' has been downloaded')
    else:
        url = 'http://108.170.217.252:10117/builders/Perf-Android-' + link + '-Arm7-Release/builds/' + build_number + '/steps/RunBench/logs/stdio/text'
        try:
            u = urllib2.urlopen(url)
        except BadStatusLine:
            error('Failed to get results of ' + args.download + ' with build number ' + build_number)

        fw = open(origin_file, 'w')
        for line in u:
            fw.write(line)
        fw.close()

    parse_result(log_dir, origin_file)

    restore_dir()

def _item_in_list(item, list):
    for i in range(len(list)):
        if item == list[i][0]:
            return True

    return False

def compare():
    if not args.compare:
        return

    diffs = []
    for i in range(len(config)):
        diffs.append([])

    files = args.compare.split(',')

    file_number = len(files)
    base = []
    _parse_format_result(log_dir, files[0], base)

    for i in range(1, file_number):
        compared = []
        _parse_format_result(log_dir, files[i], compared)

        base_index = 0
        compared_index = 0
        while base_index < len(base) and compared_index < len(compared):
            if base[base_index][0] != compared[compared_index][0]:
                base_in_compared = _item_in_list(base[base_index][0], compared)
                compared_in_base = _item_in_list(compared[compared_index][0], base)

                if base_in_compared and compared_in_base:
                    error('Base and compared data have different order')
                    quit()

                if base_in_compared:
                    base_index += 1
                else:
                    compared_index += 1
            else:
                for j in range(1, len(config) + 1):
                    if base[base_index][j] == NA or compared[compared_index][j] == NA:
                        if base[base_index][j] == compared[compared_index][j]:
                            continue

                        diffs[j - 1].append((base[base_index][0], LARGE_NUMBER, base[base_index][j], compared[compared_index][j]))

                    else:
                        b = float(base[base_index][j])
                        if b < SMALL_NUMBER:
                            b = SMALL_NUMBER
                        c = float(compared[compared_index][j])
                        if c < SMALL_NUMBER:
                            c = SMALL_NUMBER
                        d = round((c - b) / b, 4)
                        if abs(d) < 0.05:
                            continue

                        diffs[j - 1].append((base[base_index][0], d, base[base_index][j], compared[compared_index][j]))

                base_index += 1
                compared_index += 1

    for i in range(len(config)):
        diffs[i] = sorted(diffs[i], key=lambda x: x[1], reverse=True)

    # Print the sorted diff
    for i in range(len(config)):
        if not config_concerned[i]:
            continue

        print config[i] + ' ' + '% ' + files[0] + ' ' + files[1]
        for j in range(len(diffs[i])):
            print diffs[i][j][0] + ' ' + ('%.2f' %(diffs[i][j][1] * 100)) + ' ' + diffs[i][j][2] + ' ' + diffs[i][j][3]

# According to args.device, which have to be connected, and the corresponding target is known
def run():
    if not args.run:
        return

    if not args.device:
        error('Please designate device to run with')
        quit()

    backup_dir(src_dir)

    run_devices = []
    _get_device_to_target()
    for device in args.device.split(','):
        if device == HOST:
            run_devices.append(device)
            continue

        if not device_to_target.has_key(device) or device_to_target[device][1] == OFFLINE:
            warn('Device ' + device + ' is not connected')
        elif device_to_target[device][0] == UNKNOWN:
            warn('Target for device ' + device + ' is unknown')
        else:
            run_devices.append(device)

    for device in run_devices:
        if device == HOST:
            if args.run == 'release':
                command = 'out/Release/' + args.test_type
            else:
                command = 'out/Debug/' + args.test_type

            if args.run_option:
                command = command + ' ' + args.run_option
        else:
            target = device_to_target[device][0]

            if args.run == 'release':
                configuration = ' --release'
            else:
                configuration = ''

            execute('platform_tools/android/bin/linux/adb -s ' + device +  ' shell stop')
            command = 'platform_tools/android/bin/android_run_skia' + ' ' + args.test_type + ' -d ' + target + ' -s ' + device + configuration

            if args.run_option:
                command = command + ' ' + args.run_option

        if args.test_type == 'bench':
            command += ' --config'
            for i in range(len(config_concerned)):
                if config_concerned[i] == 1:
                    command += ' ' + config[i]

        group_log_dir = log_dir
        if args.run_times > 1:
            group_log_dir = log_dir + get_datetime() + '-' + device + '-' + args.test_type + '/'
            os.mkdir(group_log_dir)

        for i in range(args.run_times):
            log_file = get_datetime() + '-' + device + '-' + args.test_type + '-origin' + log_suffix
            command = command + ' 2>&1 |tee ' + group_log_dir + log_file
            start = datetime.datetime.now()
            execute(command)
            elapsed = (datetime.datetime.now() - start)
            info('Time elapsed to run: ' + str(elapsed.seconds) + 's')
            parse_result(group_log_dir, log_file)
            time.sleep(2)

        if not args.run_nonroot and device != HOST:
            execute('platform_tools/android/bin/linux/adb -s ' + device +  ' shell start')

        if args.run_times > 1:
            average(group_log_dir)

    restore_dir()

def _ensure_in_list(item, list):
    if not item in list:
        list.append(item)

# According to targets, which are from args.target and
# args.device (guess the target, and no need to connect)
def build():
    if not args.build:
        return

    targets = []
    # Set targets according to args.target
    for target in args.target.split(','):
        if target == 'x86':
            _ensure_in_list(X86, targets)
        elif target == 's3' or target == 'nexus4':
            _ensure_in_list(NEXUS4, targets)
        elif target == 'host':
            _ensure_in_list(HOST, targets)

    # Guess targets according to args.device
    if args.device != '':
        _get_device_to_target()

        for device in args.device.split(','):
            if device_to_target.has_key(device):
                _ensure_in_list(device_to_target[device][0], targets)
            else:
                warn('Could not guess out target for device: ' + device)

    if args.build.upper() == 'DEBUG':
        build = 'Debug'
    elif args.build.upper() == 'RELEASE':
        build = 'Release'

    print '== Build Environment =='
    print 'Directory of src: ' + src_dir
    print 'Build type: ' + build
    print 'System: ' + host_os
    print 'Targets: ' + ','.join(targets)
    print '======================='

    backup_dir(src_dir)

    for target in targets:
        if target == HOST:
            cmd = 'make'
        else:
            cmd = 'platform_tools/android/bin/android_make -d ' + target

        cmd = cmd + ' -j' + ' ' + args.test_type + ' BUILDTYPE=' + build
        if args.build_verbose:
            cmd = cmd + ' V=1'
        execute(cmd)

    restore_dir()

# https://sites.google.com/site/skiadocs/developer-documentation/contributing-code/using-git
def update():
    if not args.update:
        return

    backup_dir(root_dir)
    execute('gclient sync')

    backup_dir(src_dir)
    execute('git checkout master && git svn fetch && git svn rebase')
    restore_dir()

    restore_dir()

def setup():
    global root_dir
    global src_dir
    global platform_tools_dir
    global log_dir
    global toolchain_dir
    global gdb_server_path
    global gdb_client_path

    if args.root_dir:
        root_dir = args.root_dir
    else:
        root_dir = root_dir_default

    if not os.path.exists(root_dir):
        error('You must designate root_dir')
        quit()

    if args.log_dir:
        log_dir = args.log_dir
    else:
        log_dir = log_dir_default

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    src_dir = root_dir + 'trunk/'
    platform_tools_dir = src_dir + 'platform_tools/'
    toolchain_dir = platform_tools_dir + 'android/toolchains/ndk-r8e-x86-linux_v14/'
    gdb_server_path = toolchain_dir + 'gdbserver'
    gdb_client_path = toolchain_dir + 'bin/i686-linux-android-gdb'

    os.putenv('ANDROID_SDK_ROOT', android_sdk_root)
    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')
    os.putenv('PATH', platform_tools_dir + 'android/bin/linux:' + os.getenv('PATH'))

def replace_gdb():
    if not args.replace_gdb:
        return

    # Replace gdbserver and gdb with r9
    execute('rm -f ' + gdb_server_path)
    execute('ln -s /workspace/topic/android/ndk/android-ndk-r9/prebuilt/android-x86/gdbserver/gdbserver ' + gdb_server_path)
    execute('rm -f ' + gdb_client_path)
    execute('ln -s /workspace/topic/android/ndk/android-ndk-r9/toolchains/x86-4.8/prebuilt/linux-x86_64/bin/i686-linux-android-gdb ' + gdb_client_path)

def restore_gdb():
    if not args.restore_gdb:
        return

    # Restore gdbserver and gdb with r8e
    execute('rm -f ' + gdb_server_path)
    execute('ln -s /workspace/topic/android/ndk/skia-ndk-r8e-x86-linux_v14/gdbserver ' + gdb_server_path)
    execute('rm -f ' + gdb_client_path)
    execute('ln -s /workspace/topic/android/ndk/skia-ndk-r8e-x86-linux_v14/bin/i686-linux-android-gdb ' + gdb_client_path)

def handle_option():
    global args

    parser = argparse.ArgumentParser(description = 'Script to update, build and run Skia for Android IA',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  update:
  python %(prog)s -u sync
  python %(prog)s -u 'sync --force'

  build:
  python %(prog)s -b release
  python %(prog)s -b release -t s3
  python %(prog)s -b all

  run:
  python %(prog)s -r release -d 32300bd273508f3b // s3
  python %(prog)s -r release -d 006e7e464bd64fef // nexus 4
  python %(prog)s -r release -d RHBEC245400171 // pr2
  python %(prog)s -r release --run-nonroot -d 006e7e464bd64fef --run-option '--match writer writepix_rgba_UPM'
  python %(prog)s -r release -d RHBEC245400171 --run-option '--match writer'

  parse result:
  python %(prog)s --parse-result ORIGIN

  compare results:
  python %(prog)s -c BASE,COMPARED

  download:
  python %(prog)s --download nexus10

  average:
  python %(prog)s --average DIR

  update & build & run
  python %(prog)s -b release -r release -d RHBEC245400171,006e7e464bd64fef,BayTrailTee86d4a1

  other:
  python %(prog)s --replace-gdb
  python %(prog)s --restore-gdb
  python %(prog)s --remote-debug --test-type=tests --run-option '--match WritePixels'
''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupUpdate = parser.add_argument_group('build')
    groupUpdate.add_argument('-b', '--build', dest='build', help='type to build', choices=['release', 'debug'])
    groupUpdate.add_argument('--build-verbose', dest='build_verbose', help='enable verbose mode for build (V=1)', action='store_true')

    groupUpdate = parser.add_argument_group('run')
    groupUpdate.add_argument('-r', '--run', dest='run', help='type to run', choices=['release', 'debug'])
    groupUpdate.add_argument('--run-nonroot', dest='run_nonroot', help='run without root access, which would not install skia_launcher to /system', action='store_true')
    groupUpdate.add_argument("--run-option", dest="run_option", help="option to run test", default='')
    groupUpdate.add_argument("--run-times", dest="run_times", help="times to run test", default=1, type=int)
    groupUpdate = parser.add_argument_group('parse result')
    groupUpdate.add_argument('--parse-result', dest='parse_result', help='log file to be parsed')

    groupUpdate = parser.add_argument_group('compare results')
    groupUpdate.add_argument('-c', '--compare', dest='compare', help='compare 2 formatted result files, format: BASE,COMPARED, the bigger the worse')

    groupUpdate = parser.add_argument_group('download')
    groupUpdate.add_argument('--download', dest='download', help='download result from Skia waterfall', choices=['nexus10', 'nexus4'])

    groupUpdate = parser.add_argument_group('average')
    groupUpdate.add_argument('--average', dest='average', help='calculate average of results within a directory')

    groupUpdate = parser.add_argument_group('other')
    groupUpdate.add_argument('-t', '--target', dest='target', help='target list separated by ",". Possible values are x86, s3, nexus4, host', default='')
    groupUpdate.add_argument('-d', '--device', dest='device', help='device id list separated by ",", "host" for running on host machine', default='')
    groupUpdate.add_argument('--root-dir', dest='root_dir', help='root dir')
    groupUpdate.add_argument('--log-dir', dest='log_dir', help='log dir')
    groupUpdate.add_argument('--recover', dest='recover', help='recover device from test', action='store_true')
    groupUpdate.add_argument('--test-type', dest='test_type', help='test type', choices=['tests', 'gm', 'bench'], default='bench')
    groupUpdate.add_argument('--remote-debug', dest='remote_debug', help='remote debug', action='store_true')
    groupUpdate.add_argument('--replace-gdb', dest='replace_gdb', help='replace gdb server and client', action='store_true')
    groupUpdate.add_argument('--restore-gdb', dest='restore_gdb', help='restore gdb server and client', action='store_true')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

if __name__ == "__main__":
    handle_option()
    setup()
    update()
    build()
    run()

    if args.parse_result:
        parse_result(log_dir, args.parse_result)

    compare()
    download()

    if args.average:
        average()

    recover()
    remote_debug()
    replace_gdb()
    restore_gdb()