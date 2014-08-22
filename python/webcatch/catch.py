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

################################################################################


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to bisect regression',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -g 218527 -b 226662 --benchmark cocos
  python %(prog)s -g 264037 -b 266292 --benchmark browsermark --benchmark-config '"test": "Search"'

''')
    parser.add_argument('--target-os', dest='target_os', help='target os', choices=target_os_all, default='android')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=target_arch_all, default='x86')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=target_module_all, default='content_shell')
    parser.add_argument('--benchmark', dest='benchmark', help='benchmark', required=True)
    parser.add_argument('--benchmark-config', dest='benchmark_config', help='benchmark config')
    parser.add_argument('--dir-chromium', dest='dir_chromium', help='chromium dir')
    parser.add_argument('-g', '--good-rev', dest='good_rev', type=int, help='small revision, which is good')
    parser.add_argument('-b', '--bad-rev', dest='bad_rev', type=int, help='big revision, which is bad')
    parser.add_argument('--diff', dest='diff', type=int, help='percentage gap between good and bad', default=10)
    parser.add_argument('--bigger-better', dest='bigger_better', help='bigger is better', default=True)

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global target_os, target_arch, target_module, comb_name, benchmark, dir_download

    target_os = args.target_os
    target_arch = args.target_arch
    target_module = args.target_module
    benchmark = args.benchmark
    comb_name = get_comb_name(splitter='-', target_os, target_arch, target_module)
    dir_download = dir_webcatch + '/download/' + comb_name
    ensure_dir(dir_download)

    if args.good_rev:
        rev_min = args.good_rev
    else:
        rev_min = rev_default[0]

    if args.bad_rev:
        rev_max = args.bad_rev
    else:
        rev_max = rev_default[1]

    _get_revs(rev_min, rev_max)
    if len(revs) < 2:
        error('The valid versions are not enough for bisect')

    if target_os == 'linux' and target_module == 'chrome':
        sandbox_file = '/usr/local/sbin/chrome-devel-sandbox'
        if not os.path.exists(sandbox_file):
            error('SUID Sandbox file "' + sandbox_file + '" does not exist')
        sandbox_env = os.getenv('CHROME_DEVEL_SANDBOX')
        if not sandbox_env:
            error('SUID Sandbox environmental variable does not set')


def bisect(index_good, index_bad, check_boundry=False):
    rev_good = revs[index_good]
    rev_bad = revs[index_bad]

    if check_boundry:
        if not _is_good(rev_good):
            error('Revision ' + str(rev_good) + ' should not be bad')

        if _is_good(rev_bad):
            error('Revision ' + str(rev_bad) + ' should not be good')

    if index_good + 1 == index_bad:
        rev_good_final = revs[index_good]
        rev_bad_final = revs[index_bad]

        if rev_good_final + 1 == rev_bad_final:
            info('Revision ' + str(rev_bad) + ' is the exact commit for regression')
        else:
            info('The regression is between revisions (' + str(revs[index_good]) + ',' + str(revs[index_bad]) + '], but there is no build for further investigation')

        if rev_bad_final - rev_good_final < 15:
            if args.dir_chromium:
                dir_chromium = args.dir_chromium
            else:
                dir_chromium = dir_project_webcatch_project + '/chromium-' + target_os

            dir_src = dir_chromium + '/src'
            suspect_log = dir_webcatch_log + '/suspect.log'
            rev_hash = chromium_get_rev_hash(dir_src, rev_good_final, rev_bad_final)
            revs = sorted(rev_hash.keys())
            for rev in revs:
                execute('git show ' + rev_hash[rev] + ' >>' + suspect_log, show_cmd=False)
            info('Check ' + suspect_log + ' for suspected checkins')

        else:
            info('There are too many checkins in between, please manually check the checkin info')

        exit(0)

    index_mid = (index_good + index_bad) / 2
    rev_mid = revs[index_mid]
    if _is_good(rev_mid):
        bisect(index_mid, index_bad)
    else:
        bisect(index_good, index_mid)


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


def _is_good(rev):
    global baseline

    backup_dir(dir_download)
    if not os.path.exists(str(rev) + '.apk'):
        result = execute('wget %s/%s/%s.apk' % (path_web_webcatch, comb_name, str(rev)), interactive=True)
        if result[0]:
            error('Failed to download revision %s' % str(rev))

    cmd = python_webmark + ' --target-os ' + target_os + ' --target-arch ' + target_arch + ' --target-module ' + target_module + ' --benchmark ' + benchmark
    if args.benchmark_config:
        cmd += ' --benchmark-config ' + '\'' + args.benchmark_config + '\''
    cmd += ' --target-module-path %s/%s.apk' % (dir_download, str(rev))
    result_cmd = execute(cmd, return_output=True, show_progress=True)
    if result_cmd[0]:
        error('Failed to run benchmark ' + benchmark + ' with revision ' + str(rev))

    results = _parse_result(result_cmd[1])

    result_show = 'good'
    if baseline == []:
        baseline = results
    else:
        for index, result in enumerate(results):
            if args.bigger_better and result >= baseline[index] or not args.bigger_better and result < baseline[index]:
                continue
            if abs(baseline[index] - result) * 100 / args.diff > baseline[index]:
                info('The result %s with index %s is deemed as bad' % (str(result), str(index)))
                result_show = 'bad'
                break

    info('Rev %s, %s, result [%s]' % (str(rev), result_show, ','.join([str(x) for x in results])))
    if result_show == 'good':
        return True
    else:
        return False


def _parse_result(output):
    results = []
    pattern = re.compile('Result:.*\[(.*)\]')
    match = pattern.search(output, re.MULTILINE)
    if match:
        results = [float(x) for x in match.group(1).split(',')]
    return results


if __name__ == '__main__':
    handle_option()
    setup()
    bisect(0, len(revs) - 1, check_boundry=True)
