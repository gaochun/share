#!/usr/bin/env python

# <image>
# link: http://wp-02.sh.intel.com/webmark/image
# | image               | chrome_stable (x86) | chrome_beta (x86) | others (x86, x86_64) |
# | ecs_e7_64p-20150320 | 42-99               | 42-99             | 310967-999999        |
# | ecs_e7_64p-20150105 | 38-41               | 38-41             | 297000-310966        |
# </image>

import sys
sys.path.append(sys.path[0] + '/..')
from util import *

try:
    import matplotlib.pyplot as plt
except:
    'Please install package python-matplotlib'

dir_root = ''
log = ''
timestamp = ''

devices_id = []
devices_product = []
devices_type = []
devices_arch = []
devices_mode = []

# [('ecs_e7_64p', 'x86_64', 'powersave', 600000, 'android', 'x86_64', 'content_shell')]
combs_device_module = []
# index_combs_device_module: [version0, version1,]
device_module_to_version = {}
# [('JavaScript', 'kraken', '1.1', 'ms(-)'),]
combs_case = []
COMBS_CASE_INDEX_CATEGORY = 0
COMBS_CASE_INDEX_NAME = 1
COMBS_CASE_INDEX_VERSION = 2
COMBS_CASE_INDEX_METRIC = 3
COMBS_CASE_INDEX_VALUE = 4
# (index_combs_device_module, index_combs_case): {310000: 1820.3}
device_module_case_to_perf = {}
# (index_combs_device_module, index_combs_case): {rev_min, rev_max}
device_module_case_to_analysis = {}

# [[device.product, device.arch, device.governor, device.freq, module.os, module.arch, module.name, module.version]]
combs_all = [
    # ['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86_64', 'content_shell', ['302000', '999999', 200]],
    # ['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86', 'content_shell', ['302000', '999999', 200]],
    # ['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86', 'chrome_stable', ['38', '99', 1]],
    # ['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86', 'chrome_beta', ['38', '99', 1]],
    # ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86_64', 'content_shell', ['300000', '999999', 200]],
    # ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'content_shell', ['300000', '999999', 200]],
    # ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86_64', 'chrome_shell', ['297000', '999999', 200]],
    # ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_shell', ['297000', '999999', 200]],
    # ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_stable', ['38', '99', 1]],
    # ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_beta', ['38', '99', 1]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86_64', 'chrome_shell', ['310967', '999999', 200]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_shell', ['310967', '999999', 200]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_stable', ['42', '99', 1]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_beta', ['42', '99', 1]],
]


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to run Chromium performance test',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --run
  python %(prog)s --analyze
  python %(prog)s --analyze --analyze-serialize
  python %(prog)s --analyze --analyze-serialize --analyze-filter '{"module":{"name":"content_shell","arch":"x86","version":"300000-999999"},"case":{"name":"octane"}}'
''')

    parser.add_argument('--run', dest='run', help='run chromium performance test with combs need to run', action='store_true')
    parser.add_argument('--analyze', dest='analyze', help='analyze the result', action='store_true')
    parser.add_argument('--analyze-filter', dest='analyze_filter', help='analyze filter')
    parser.add_argument('--analyze-unknown', dest='analyze_unknown', help='only show the graph with change', choices=['all', 'imp', 'reg'])
    parser.add_argument('--analyze-serialize', dest='analyze_serialize', help='Use serialized result instead of reading from server', action='store_true')
    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, log, timestamp

    (timestamp, dir_root, log) = setup_common(args, _teardown)


def run():
    if not args.run:
        return

    _setup_device()
    device_id = devices_id[0]

    for comb in combs_all:
        combs_done = []
        combs_available = []
        combs_todo = []

        combs_done = _get_combs_from_server('done', comb)
        combs_available = _get_combs_from_server('available', comb)

        for comb_available in combs_available:
            if comb_available not in combs_done:
                combs_todo.append(comb_available)

        # print combs_todo
        # for c in combs_todo:
        #     print c

        config_suites = ''
        for comb_todo in combs_todo:
            # make sure running with sufficient power
            if android_get_power_percent(device_id=device_id) < 50:
                android_ensure_screen_off(device_id=device_id)
                time.sleep(3600 * 4)
            android_ensure_screen_on(device_id=device_id)

            config_todo = '''
{
  "suites": [
    {
      "name": "Chrome for Android Performance Test",
      "description": "Chrome for Android Performance Test",
      "device": {
        "governor": "%s",
        "freq": %s,
        "arch": "%s",
        "product": "%s"
      },
      "module": {
        "name": "%s",
        "os": "%s",
        "arch": "%s",
        "version": "%s",
        "path": "auto"
      },
      "cases": [
        {"name": "kraken", "version": "1.1"},
        {"name": "octane", "version": "1.0"},
        {"name": "sunspider", "version": "1.0.2"},

        {"name": "canvas2dc10k"},
        {"name": "canvasmark", "version": "2013"},
        {"name": "fishietank", "version": "raf", "count_fish": 250},
        {"name": "fishietank", "version": "setinterval", "count_fish": 250},
        {"name": "galactic", "version": "mobile"},

        {"name": "aquarium"},
        {"name": "cubemap"},
        {"name": "toonshading"},

        {"name": "fallingleaves"},
        {"name": "postercircle"},

        {"name": "browsermark", "version": "2.0"},
        {"name": "browsermark", "version": "2.1"}
      ]
    }
  ]
}
            ''' % (comb_todo[PERF_COMBS_INDEX_DEVICE_GOVERNOR],
                   comb_todo[PERF_COMBS_INDEX_DEVICE_FREQ],
                   comb_todo[PERF_COMBS_INDEX_DEVICE_ARCH],
                   comb_todo[PERF_COMBS_INDEX_DEVICE_PRODUCT],
                   comb_todo[PERF_COMBS_INDEX_MODULE_NAME],
                   comb_todo[PERF_COMBS_INDEX_MODULE_OS],
                   comb_todo[PERF_COMBS_INDEX_MODULE_ARCH],
                   comb_todo[PERF_COMBS_INDEX_MODULE_VERSION])

            file_config_todo = dir_share_ignore_webmark + '/config_todo.json'
            fw = open(file_config_todo, 'w')
            fw.write(config_todo)
            fw.close()

            if os.path.exists(file_config_todo):
                cmd = '%s --config %s --formal' % (python_share_webmark, file_config_todo)
                execute(cmd, interactive=True)


def analyze():
    if not args.analyze:
        return

    _get_perf()
    _get_analysis()

    for index_dmc, dmc in enumerate(device_module_case_to_perf):
        index_dm = dmc[0]
        index_c = dmc[1]
        x = []
        y = []
        x_name = []
        x_imp_known = []
        y_imp_known = []
        x_imp_unknown = []
        y_imp_unknown = []
        x_reg_known = []
        y_reg_known = []
        x_reg_unknown = []
        y_reg_unknown = []
        version_min = ''
        version_max = ''

        # filter
        if args.analyze_filter:
            dmc_info = {}
            dmc_info['device'] = {}
            dmc_info['module'] = {}
            dmc_info['case'] = {}
            comb_dm = combs_device_module[index_dm]
            dmc_info['device']['product'] = comb_dm[PERF_COMBS_INDEX_DEVICE_PRODUCT]
            dmc_info['device']['arch'] = comb_dm[PERF_COMBS_INDEX_DEVICE_ARCH]
            dmc_info['device']['governor'] = comb_dm[PERF_COMBS_INDEX_DEVICE_GOVERNOR]
            dmc_info['device']['freq'] = comb_dm[PERF_COMBS_INDEX_DEVICE_FREQ]
            dmc_info['module']['os'] = comb_dm[PERF_COMBS_INDEX_MODULE_OS]
            dmc_info['module']['arch'] = comb_dm[PERF_COMBS_INDEX_MODULE_ARCH]
            dmc_info['module']['name'] = comb_dm[PERF_COMBS_INDEX_MODULE_NAME]
            comb_case = combs_case[index_c]
            dmc_info['case']['category'] = comb_case[COMBS_CASE_INDEX_CATEGORY]
            dmc_info['case']['name'] = comb_case[COMBS_CASE_INDEX_NAME]
            dmc_info['case']['version'] = comb_case[COMBS_CASE_INDEX_VERSION]
            dmc_info['case']['metric'] = comb_case[COMBS_CASE_INDEX_METRIC]

            need_filter = False
            af = json.loads(args.analyze_filter)
            for key_l1 in af:
                if need_filter:
                    break
                for key_l2 in af[key_l1]:
                    if key_l1 not in dmc_info or key_l2 not in dmc_info[key_l1]:
                        continue
                    if af[key_l1][key_l2] != dmc_info[key_l1][key_l2]:
                        need_filter = True
                        break
            if need_filter:
                continue

            if 'module' in af and 'version' in af['module']:
                af_version = af['module']['version'].split('-')
                version_min = af_version[0]
                version_max = af_version[1]

        for index_version, version in enumerate(device_module_to_version[index_dm]):
            if version_min and version_max:
                if ver_cmp(version, version_min) < 0 or ver_cmp(version, version_max) > 0:
                    continue

            x.append(index_version)
            x_name.append(version)
            value = device_module_case_to_perf[dmc][version]
            y.append(value)

            if index_version > 0:
                version_prev = device_module_to_version[index_dm][index_version - 1]
                value_prev = device_module_case_to_perf[dmc][version_prev]
                if value_prev == 0:
                    diff = 0
                else:
                    diff = round(abs(value - value_prev) / value_prev, 2) * 100
                if diff > PERF_CHANGE_PERCENT:

                    found = False
                    if dmc in device_module_case_to_analysis:
                        for analysis in device_module_case_to_analysis[dmc]:
                            version_min_anal = analysis[0]
                            version_max_anal = analysis[1]
                            if ver_cmp(version, version_min_anal) >= 0 and ver_cmp(version, version_max_anal) <= 0:
                                found = True
                                break

                    if re.search('\+', combs_case[index_c][3]) and value > value_prev or re.search('\-', combs_case[index_c][3]) and value < value_prev:
                        if found:
                            x_imp_known.append(index_version)
                            y_imp_known.append(value)
                        else:
                            x_imp_unknown.append(index_version)
                            y_imp_unknown.append(value)
                    else:
                        if found:
                            x_reg_known.append(index_version)
                            y_reg_known.append(value)
                        else:
                            x_reg_unknown.append(index_version)
                            y_reg_unknown.append(value)

        if args.analyze_unknown:
            if args.analyze_unknown == 'all' and not x_imp_unknown and not x_reg_unknown:
                continue
            elif args.analyze_unknown == 'imp' and not x_imp_unknown:
                continue
            elif args.analyze_unknown == 'reg' and not x_reg_unknown:
                continue

        fig, ax = plt.subplots()
        ax.set_title('-'.join(combs_device_module[index_dm]) + '\n' + '-'.join(combs_case[index_c]))
        ax.xaxis.grid(True)
        ax.yaxis.grid(True)
        ax.set_xlabel('Version')
        ax.set_ylabel('Value')
        ax.plot(x, y)
        ax.set_xticks(x)
        ax.set_xticklabels(x_name)
        ax.plot(x_reg_unknown, y_reg_unknown, 'ro')  # red
        ax.plot(x_imp_unknown, y_imp_unknown, 'go')  # green
        ax.plot(x_reg_known, y_reg_known, 'wo')
        ax.plot(x_imp_known, y_imp_known, 'wo')
        for xl in ax.get_xticklabels():
            xl.set_rotation(90)

        plt.show()


class Parser(HTMLParser):
    def __init__(self, pattern):
        HTMLParser.__init__(self)
        self.pattern = pattern
        self.is_a = False
        self.matched = False
        self.href = ''
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.is_a = True
            for (name, value) in attrs:
                if name == 'href':
                    self.href = value
                    break

    def handle_endtag(self, tag):
        if tag == 'a':
            self.is_a = False

    def handle_data(self, data):
        if self.is_a:
            match = re.search(self.pattern, data)
            # all the good links are continuous. Exit using an exception as close() seems not work.
            if self.matched and not match:
                pass
            if match:
                self.matched = True
                self.links.append(self.href)


def _get_perf():
    global combs_device_module, device_module_to_version, combs_case, device_module_case_to_perf

    if args.analyze_serialize and os.path.exists(path_share_ignore_chromium_perf):
        f = open(path_share_ignore_chromium_perf)
        combs_device_module = pickle.load(f)
        device_module_to_version = pickle.load(f)
        combs_case = pickle.load(f)
        device_module_case_to_perf = pickle.load(f)
        f.close()
        return

    try:
        u = urllib2.urlopen(path_web_webmark_result)
    except:
        error('Can NOT open %s' % path_web_webmark_result)
    html = u.read().decode('utf-8')
    parser = Parser('.txt')
    parser.feed(html)
    for link in parser.links:
        fields = link.replace('.txt', '').split('-')
        comb = tuple(fields[:PERF_COMBS_INDEX_MODULE_VERSION])
        if comb not in combs_device_module:
            combs_device_module.append(comb)

        index = combs_device_module.index(comb)
        if index in device_module_to_version:
            device_module_to_version[index].append(fields[-1])
        else:
            device_module_to_version[index] = [fields[-1]]

    # sort the version
    for index_comb in device_module_to_version:
        device_module_to_version[index_comb] = sorted(device_module_to_version[index_comb], cmp=ver_cmp)

    for index_combs_dm in device_module_to_version:
        vers = device_module_to_version[index_combs_dm]
        for ver in vers:
            name_file = path_web_webmark_result + '/' + '-'.join(combs_device_module[index_combs_dm]) + '-' + ver + '.txt'
            try:
                u = urllib2.urlopen(name_file)
            except:
                error('Can NOT open %s' % name_file)
            lines = u.read().decode('utf-8').split('\n')
            for line in lines:
                if re.match('"', line):
                    continue
                if re.match('^$', line):
                    continue
                fields = line.split(',')
                comb = (fields[COMBS_CASE_INDEX_CATEGORY], fields[COMBS_CASE_INDEX_NAME], fields[COMBS_CASE_INDEX_VERSION], fields[COMBS_CASE_INDEX_METRIC])
                if comb not in combs_case:
                    combs_case.append(comb)

                index_combs_case = combs_case.index(comb)
                if (index_combs_dm, index_combs_case) not in device_module_case_to_perf:
                    device_module_case_to_perf[(index_combs_dm, index_combs_case)] = {}

                device_module_case_to_perf[(index_combs_dm, index_combs_case)][ver] = float(fields[COMBS_CASE_INDEX_VALUE])

    ensure_dir(dir_share_ignore_chromium)
    ensure_file(path_share_ignore_chromium_perf)
    f = open(path_share_ignore_chromium_perf, 'w')
    f.seek(0)
    f.truncate()
    pickle.dump(combs_device_module, f)
    pickle.dump(device_module_to_version, f)
    pickle.dump(combs_case, f)
    pickle.dump(device_module_case_to_perf, f)
    f.close()


def _get_analysis():
    global analysis

    anals = []
    backup_dir('analysis')
    files = os.listdir('.')
    for f in files:
        if not f[-5:] == '.json':
            continue

        fh = open(f)
        anals += json.load(fh)
        fh.close()
    restore_dir()

    tmp_combs_case = []
    for comb in combs_case:
        tmp_combs_case.append((comb[COMBS_CASE_INDEX_NAME], comb[COMBS_CASE_INDEX_VERSION]))

    for anal in anals:
        tmp_comb_device_module = (anal['device']['product'], anal['device']['arch'], anal['device']['governor'], str(anal['device']['freq']),
                                  anal['module']['os'], anal['module']['arch'], anal['module']['name'])
        if tmp_comb_device_module not in combs_device_module:
            continue
        index_device_module = combs_device_module.index(tmp_comb_device_module)

        for case in anal['cases']:
            if 'version' not in case:
                case['version'] = 'NA'
            tmp_comb_case = (case['name'], case['version'])
            if tmp_comb_case not in tmp_combs_case:
                continue
            index_case = tmp_combs_case.index(tmp_comb_case)

            for key in case['analysis']:
                if re.search('-', key):
                    fields = key.split('-')
                    ver_min = fields[0]
                    ver_max = fields[1]
                else:
                    ver_min = key
                    ver_max = key

                if (index_device_module, index_case) not in device_module_case_to_analysis:
                    device_module_case_to_analysis[(index_device_module, index_case)] = []
                device_module_case_to_analysis[(index_device_module, index_case)].append([ver_min, ver_max])


def _get_combs_from_server(comb_type, comb):
    combs = []
    module_name = comb[PERF_COMBS_INDEX_MODULE_NAME]
    module_arch = comb[PERF_COMBS_INDEX_MODULE_ARCH]
    module_os = comb[PERF_COMBS_INDEX_MODULE_OS]

    if comb_type == 'done':
        str_regular = '%s-(\d+\.\d+\.\d+\.\d+|\d{6})' % ('-'.join(comb[PERF_COMBS_INDEX_DEVICE_PRODUCT:PERF_COMBS_INDEX_MODULE_VERSION]))
        path_server = path_web_webmark_result
    elif comb_type == 'available':
        if module_name == 'chrome_stable' or module_name == 'chrome_beta':
            str_regular = '\d+\.\d+\.\d+\.\d+\-(stable|beta)'
            path_server = '%s/%s-%s-%s' % (path_web_chrome_android, module_os, module_arch, 'chrome')
        elif module_name == 'content_shell' or module_name == 'webview_shell' or module_name == 'chrome_shell':
            str_regular = '\d{6}.apk'
            path_server = '%s/%s-%s-%s' % (path_web_webcatch, module_os, module_arch, module_name)

    try:
        u = urllib2.urlopen(path_server)
    except:
        error('Can NOT open %s' % path_server)
    html = u.read().decode('utf-8')
    lines = html.split('\n')

    matched = False
    for line in lines:
        match = re.search(str_regular, line)
        if match:
            if comb_type == 'done':
                comb_temp = match.group(0).split('-')
                combs.append(comb_temp)
            elif comb_type == 'available':
                if module_name == 'chrome_stable' or module_name == 'chrome_beta':
                    comb_module_name_temp = 'chrome_' + match.group(0).split('-')[1]
                    comb_module_version_temp = match.group(0).split('-')[0]
                elif module_name == 'content_shell' or module_name == 'webview_shell' or module_name == 'chrome_shell':
                    comb_module_name_temp = module_name
                    comb_module_version_temp = match.group(0).replace('.apk', '')

                if ver_cmp(comb_module_version_temp, comb[PERF_COMBS_INDEX_MODULE_VERSION][PERF_COMBS_INDEX_MODULE_VERSION_MIN]) >= 0 and \
                        ver_cmp(comb_module_version_temp, comb[PERF_COMBS_INDEX_MODULE_VERSION][PERF_COMBS_INDEX_MODULE_VERSION_MAX]) < 0:
                    if comb_module_name_temp == module_name and \
                            (comb[PERF_COMBS_INDEX_MODULE_VERSION][PERF_COMBS_INDEX_MODULE_VERSION_INTERVAL] == 1 or
                                int(comb_module_version_temp) % comb[PERF_COMBS_INDEX_MODULE_VERSION][PERF_COMBS_INDEX_MODULE_VERSION_INTERVAL] == 0):
                        comb_temp = list(comb)
                        comb_temp[PERF_COMBS_INDEX_MODULE_VERSION] = comb_module_version_temp
                        combs.append(comb_temp)
                        matched = True
                else:
                    if matched:
                        break
    return combs


def _setup_device():
    global devices_id, devices_product, devices_type, devices_arch, devices_mode

    if devices_id:
        return

    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device()


def _teardown():
    pass


if __name__ == '__main__':
    parse_arg()
    setup()
    run()
    analyze()
