# proxies are from https://irefservices.intel.com/ContentTransferService.svc/0902007c8002921c?ApiKey=7c30ff7e-1de8-4238-93e5-8b791af5d362

from util import *

LATENCY_MAX = 1000

proxies = [
    #'proxy-iind.intel.com',
    #'proxy.fm.intel.com',
    #'proxy-iil.intel.com',
    'proxy-ir.intel.com',
    #'proxy.jf.intel.com',
    #'proxy-us.intel.com',
    'proxy-mu.intel.com',
    #'proxy-png.intel.com',
    #'proxy-shz.intel.com',
    #'proxy-shm.intel.com',
]

speeds = {}


def test_speed(index):
    global speeds

    proxy = proxies[index]
    timer_start(proxy, microsecond=True)
    result = execute('timeout 3s curl --socks5 %s:1080 www.google.com' % proxy)
    timer_stop(proxy, microsecond=True)
    if result[0]:
        speeds[index] = LATENCY_MAX
    else:
        speeds[index] = timer_diff(proxy).total_seconds()


if __name__ == '__main__':
    for index in range(len(proxies)):
        test_speed(index)

    speeds = sorted(speeds.items(), key=operator.itemgetter(1))
    for pair in speeds:
        if pair[1] == LATENCY_MAX:
            break

        info('%s: %ss' % (proxies[pair[0]], pair[1]))
