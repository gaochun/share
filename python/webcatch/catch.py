import urllib2
import sys
sys.path.append(sys.path[0] + '/..')
from util import *

target_os = ''
target_arch = ''
target_module = ''
benchmark = ''
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
    global args
    parser = argparse.ArgumentParser(description='Script to bisect regression',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -r 218527-226662 --benchmark cocos
  python %(prog)s -r 264037-266292 --benchmark browsermark --benchmark-config '"test": "Search", "version": "2.0"'

''')
    parser.add_argument('--target-os', dest='target_os', help='target os', choices=target_os_all, default='android')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=target_arch_all, default='x86')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=target_module_all, default='content_shell')
    parser.add_argument('--benchmark', dest='benchmark', help='benchmark', required=True)
    parser.add_argument('--benchmark-config', dest='benchmark_config', help='benchmark config')
    parser.add_argument('--dir-chromium', dest='dir_chromium', help='chromium dir')
    parser.add_argument('-r', '--rev', dest='rev', help='revision from A to B')
    parser.add_argument('--diff', dest='diff', type=int, help='percentage gap between good and bad', default=5)
    parser.add_argument('--governor', dest='governor', help='governor')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global target_os, target_arch, target_module, comb_name, benchmark, dir_download, revs, baseline_a, baseline_b

    target_os = args.target_os
    target_arch = args.target_arch
    target_module = args.target_module
    benchmark = args.benchmark
    comb_name = get_comb_name('-', target_os, target_arch, target_module)
    dir_download = dir_webcatch + '/download/' + comb_name
    ensure_dir(dir_download)
    ensure_dir(dir_webcatch_log)

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

    if target_os == 'linux' and target_module == 'chrome':
        sandbox_file = '/usr/local/sbin/chrome-devel-sandbox'
        if not os.path.exists(sandbox_file):
            error('SUID Sandbox file "' + sandbox_file + '" does not exist')
        sandbox_env = os.getenv('CHROME_DEVEL_SANDBOX')
        if not sandbox_env:
            error('SUID Sandbox environmental variable does not set')


def _get_revs(rev_min, rev_max):
    global revs
    url = path_web_webcatch + '/%s-%s-%s/' % (target_os, target_arch, target_module)
    try:
        u = urllib2.urlopen(url)
    except:
        error('Failed to open ' + url)

    html = u.read()
    pattern = re.compile('href="(\d+).apk"')
    revs_temp = pattern.findall(html)
    revs = [int(x) for x in revs_temp if int(x) >= rev_min and int(x) <= rev_max]
    if len(revs) < 2:
        error('The valid versions are not enough for bisect')


def _run(rev):
    backup_dir(dir_download)
    if not os.path.exists(str(rev) + '.apk'):
        result = execute('wget %s/%s/%s.apk' % (path_web_webcatch, comb_name, str(rev)), interactive=True)
        if result[0]:
            error('Failed to download revision %s' % str(rev))
    restore_dir()

    cmd = python_webmark + ' --target-os ' + target_os + ' --target-arch ' + target_arch + ' --target-module ' + target_module + ' --benchmark ' + benchmark
    if args.benchmark_config:
        cmd += ' --benchmark-config ' + '\'' + args.benchmark_config + '\''
    cmd += ' --target-module-path %s/%s.apk' % (dir_download, str(rev))
    result_cmd = execute(cmd, return_output=True, show_progress=True)
    if result_cmd[0]:
        error('Failed to run benchmark ' + benchmark + ' with revision ' + str(rev))

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
    pattern = re.compile('Result:.*,.*,(.*)')
    match = pattern.search(output, re.MULTILINE)
    if match:
        results = [float(x) for x in match.group(1).split(',')]
    return results[0]


def _bisect(index_small, index_big):
    global revs

    rev_small = revs[index_small]
    rev_big = revs[index_big]

    # finish the bisect
    if index_small + 1 == index_big:
        info('<history>')
        for key in sorted(report):
            print '%s, %s' % (key, report[key])

        info('</history>')

        rev_small_final = revs[index_small]
        rev_big_final = revs[index_big]

        if rev_small_final + 1 == rev_big_final:
            info('Revision ' + str(rev_small) + ' is the exact commit for regression')
        else:
            info('The regression is between revisions (' + str(revs[index_small]) + ',' + str(revs[index_big]) + '], but there is no build for further investigation')

        if rev_big_final - rev_small_final < 15:
            if args.dir_chromium:
                dir_chromium = args.dir_chromium
            else:
                dir_chromium = dir_project_webcatch_project + '/chromium-' + target_os

            dir_src = dir_chromium + '/src'
            suspect_log = dir_webcatch_log + '/suspect.log'
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
