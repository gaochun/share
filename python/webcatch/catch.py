import urllib2
import sys
sys.path.append(sys.path[0] + '/..')
from util import *

module_os = ''
module_arch = ''
module_name = ''
case_name = ''
revs = []
baseline = []
comb_name = ''
dir_download = ''
report = {}
baseline_a = 0.0
baseline_b = 0.0
index = 0
################################################################################


def handle_option():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to bisect change',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -r 218527-226662 --case-name cocos
  python %(prog)s -r 264037-266292 --case-name browsermark --case-config '"test": "Search", "version": "2.0"'

''')
    group_device = parser.add_argument_group('device')
    group_device.add_argument('--device-id', dest='device_id', help='device id separated by comma')
    group_device.add_argument('--device-freq', dest='device_freq', type=int, help='device freq')
    group_device.add_argument('--device-governor', dest='device_governor', help='device governor')

    group_module = parser.add_argument_group('module')
    group_module.add_argument('--module-arch', dest='module_arch', help='module arch', default='x86')
    group_module.add_argument('--module-name', dest='module_name', help='module name', default='content_shell')
    group_module.add_argument('--module-os', dest='module_os', help='module os', default='android')
    group_module.add_argument('--module-path', dest='module_path', help='module path')

    group_case = parser.add_argument_group('case')
    group_case.add_argument('--case-name', dest='case_name', help='case name')
    group_case.add_argument('--case-config', dest='case_config', help='case config')

    parser.add_argument('--dir-chromium', dest='dir_chromium', help='chromium dir')
    parser.add_argument('-r', '--rev', dest='rev', help='revision from A to B')
    parser.add_argument('--diff', dest='diff', type=int, help='percentage gap between good and bad', default=5)
    parser.add_argument('--skip-install', dest='skip_install', help='skip the installation of module', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global module_os, module_arch, module_name, comb_name, case_name, dir_download, revs, baseline_a, baseline_b

    module_os = args.module_os
    module_arch = args.module_arch
    module_name = args.module_name
    case_name = args.case_name
    comb_name = get_comb_name('-', module_os, module_arch, module_name)
    dir_download = dir_share_ignore_webcatch_download + '/' + comb_name
    ensure_dir(dir_download)
    ensure_dir(dir_share_ignore_webcatch_log)

    if args.rev:
        revs_temp = [int(x) for x in args.rev.split('-')]
        rev_min = revs_temp[0]
        rev_max = revs_temp[1]
    else:
        rev_min = chromium_rev_default[0]
        rev_max = chromium_rev_default[1]

    if rev_min >= rev_max:
        error('rev_min should be smaller than rev_max')

    _get_revs(rev_min, rev_max)

    rev_a = revs[0]
    baseline_a = _run(rev_a)
    rev_b = revs[-1]
    baseline_b = _run(rev_b)
    _judge_result(rev_a, baseline_a)
    _judge_result(rev_b, baseline_b)

    _bisect(0, len(revs) - 1)

    if module_os == 'linux' and module_name == 'chrome':
        sandbox_file = '/usr/local/sbin/chrome-devel-sandbox'
        if not os.path.exists(sandbox_file):
            error('SUID Sandbox file "' + sandbox_file + '" does not exist')
        sandbox_env = os.getenv('CHROME_DEVEL_SANDBOX')
        if not sandbox_env:
            error('SUID Sandbox environmental variable does not set')


def _get_revs(rev_min, rev_max):
    global revs
    url = path_web_webcatch + '/%s-%s-%s/' % (module_os, module_arch, module_name)
    try:
        u = urllib2.urlopen(url)
    except:
        error('Failed to open ' + url)

    html = u.read()
    pattern = re.compile('href="(\d+).apk"')
    revs_temp = pattern.findall(html)
    revs = sorted([int(x) for x in revs_temp if int(x) >= rev_min and int(x) <= rev_max])
    if len(revs) < 2:
        error('The valid versions are not enough for bisect')


def _run(rev):
    backup_dir(dir_download)
    if not os.path.exists(str(rev) + '.apk'):
        result = execute('wget %s/%s/%s.apk' % (path_web_webcatch, comb_name, str(rev)), interactive=True)
        if result[0]:
            error('Failed to download revision %s' % str(rev))
    restore_dir()

    cmd = python_share_webmark
    for arg in ['device-id', 'device-governor', 'device-freq', 'module-arch', 'module-name', 'module-os', 'case-name']:
        var = arg.replace('-', '_')
        if var in args_dict and args_dict[var]:
            cmd += ' --%s %s' % (arg, args_dict[var])

    if args.case_config:
        cmd += ' --case-config ' + '\'' + args.case_config + '\''
    if not args.skip_install:
        cmd += ' --module-path %s/%s.apk' % (dir_download, str(rev))
    result_cmd = execute(cmd, return_output=True, show_progress=True)
    if result_cmd[0]:
        error('Failed to run case_name ' + case_name + ' with revision ' + str(rev))

    return _parse_result(result_cmd[1])


# return 1 if close to result of A. Otherwise, return 0.
def _judge_result(rev, result):
    global report, index

    diff_a = _get_diff(result, baseline_a)
    diff_b = _get_diff(result, baseline_b)

    if abs(diff_a) <= abs(diff_b):
        result_show = 'A'
        ret = 1
    else:
        result_show = 'B'
        ret = 0

    info('%s, %s, %s, %s, %s%%, %s%%' % (index, rev, result_show, result, diff_a, diff_b))
    report[rev] = [index, result_show, result, diff_a, diff_b]
    index = index + 1

    return ret


def _get_diff(result, baseline):
    return round((result - baseline) * 100 / baseline, 2)


def _parse_result(output):
    results = []
    pattern = re.compile('%s(.*)' % webmark_result_str)
    match = pattern.search(output, re.MULTILINE)
    if match:
        results = match.group(1).split(',')
        index = 0
        for item in webmark_format:
            if item == 'result':
                break
            index += 1
        return float(results[index])
    else:
        error('Can not get result')


def _bisect(index_small, index_big):
    global revs

    # finish the bisect
    if index_small + 1 == index_big:
        info('<history>')
        for key in sorted(report):
            print '%s, %s' % (key, report[key])

        info('</history>')

        rev_small_final = revs[index_small]
        rev_big_final = revs[index_big]

        if rev_small_final + 1 == rev_big_final:
            info('Revision ' + str(rev_big_final) + ' is the exact commit for change')
        else:
            info('The change is between revisions (' + str(revs[index_small]) + ',' + str(revs[index_big]) + '], but there is no build for further investigation')

        if rev_big_final - rev_small_final < 15:
            if args.dir_chromium:
                dir_chromium = args.dir_chromium
            else:
                dir_chromium = dir_project_webcatch_project + '/chromium-' + module_os

            dir_src = dir_chromium + '/src'
            suspect_log = dir_share_ignore_webcatch_log + '/suspect.log'
            execute('rm -f ' + suspect_log)
            rev_hash = chromium_get_rev_hash(dir_src, rev_small_final + 1, rev_big_final)
            revs = sorted(rev_hash.keys())
            backup_dir(dir_src)
            for rev in revs:
                execute('git show ' + rev_hash[rev] + ' >>' + suspect_log, show_cmd=True)
            restore_dir()
            info('Check ' + suspect_log + ' for suspected checkins')

        else:
            info('There are too many checkins in between, please manually check the checkin info')

        exit(0)

    index_mid = (index_small + index_big) / 2
    rev_mid = revs[index_mid]
    result_mid = _run(rev_mid)
    if _judge_result(rev_mid, result_mid):
        _bisect(index_mid, index_big)
    else:
        _bisect(index_small, index_mid)


if __name__ == '__main__':
    handle_option()
    setup()
