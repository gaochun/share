# proxies are from https://irefservices.intel.com/ContentTransferService.svc/0902007c8002921c?ApiKey=7c30ff7e-1de8-4238-93e5-8b791af5d362

from util import *

LATENCY_MAX = 1000

proxies = [
    ['proxy-ir.intel.com', 'socks5', 1080],
    ['proxy-mu.intel.com', 'socks5', 1080],
    ['proxy-us.intel.com', 'http', 912],
    ['child-prc.intel.com', 'http', 913],

    #'proxy.mu.intel.com',  ## can not be used
    #'proxy.ir.intel.com',  # same as -ir
    #'proxy-iind.intel.com',
    #'proxy.fm.intel.com',
    #'proxy-iil.intel.com',
    #'proxy.jf.intel.com',
    #'proxy-us.intel.com',
    #'proxy-png.intel.com',
    #'proxy-shz.intel.com',
    #'proxy-shm.intel.com',

]

PROXY_INDEX_SERVER = 0
PROXY_INDEX_PROTOTOL = 1
PROXY_INDEX_PORT = 2

speeds = {}


def test_speed(index):
    global speeds

    proxy = proxies[index]
    proxy_protocol = proxy[PROXY_INDEX_PROTOTOL]
    proxy_server = proxy[PROXY_INDEX_SERVER]
    proxy_port = proxy[PROXY_INDEX_PORT]

    cmd = 'timeout 3s curl'
    cmd += ' -x %s://%s:%s' % (proxy_protocol, proxy_server, proxy_port)
    cmd += ' www.google.com'
    timer_start(proxy_server, microsecond=True)
    result = execute(cmd)
    timer_stop(proxy_server, microsecond=True)
    if result[0]:
        speeds[index] = LATENCY_MAX
    else:
        speeds[index] = timer_diff(proxy_server).total_seconds()


if __name__ == '__main__':
    for index in range(len(proxies)):
        test_speed(index)

    speeds = sorted(speeds.items(), key=operator.itemgetter(1))
    for pair in speeds:
        if pair[1] == LATENCY_MAX:
            break

        info('%s: %ss' % (proxies[pair[0]], pair[1]))
