#!/usr/bin/env python

from util import *
import urllib2

devices_id = []
devices_arch = []
devices_product = []

# [[device.product, device.arch, device.governor, device.freq, module.os, module.arch, module.name, module.version]]
combs_all = [
    #['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86_64', 'content_shell', ['302000', '999999', 200]],
    #['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86', 'content_shell', ['302000', '999999', 200]],
    #['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86', 'chrome_stable', ['38', '99', 1]],
    #['asus_t100_64p', 'x86_64', 'powersave', '400000', 'android', 'x86', 'chrome_beta', ['38', '99', 1]],
    #['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86_64', 'content_shell', ['300000', '999999', 200]],
    #['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'content_shell', ['300000', '999999', 200]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86_64', 'chrome_shell', ['297000', '999999', 200]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_shell', ['297000', '999999', 200]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_stable', ['38', '99', 1]],
    ['ecs_e7_64p', 'x86_64', 'powersave', '600000', 'android', 'x86', 'chrome_beta', ['38', '99', 1]],
]


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to run Chromium performance test',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --run
''')

    parser.add_argument('--run', dest='run', help='run chromium performance test with combs need to run', action='store_true')
    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global devices_id, devices_product, devices_arch

    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device()
    if len(devices_id) == 0:
        error('No device is connected')


def run():
    if not args.run:
        return

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
            if android_get_power_percent(device_id=devices_id[0]) < 50:
                time.sleep(7200)

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
                cmd = '%s --config %s --formal' % (python_webmark, file_config_todo)
                execute(cmd, interactive=True)


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


if __name__ == '__main__':
    parse_arg()
    setup()
    run()
