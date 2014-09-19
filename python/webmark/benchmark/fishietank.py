from benchmark import *


class fishietank(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'FishIETank',
        'version': 'setinterval',
        'metric': metric_info['fps'],
        'path': {
            'setinterval': {
                'external': 'http://ie.microsoft.com/testdrive/Performance/FishIETank/Default.html',
                'internal': 'webbench/microsoft/testdrive/Performance/FishIETank/Default.html'
            },
            'raf': {
                'external': '',
                'internal': 'webbench/fishtank-raf/'
            }
        },
        'counts_fish': [1, 10, 20, 50, 100, 250, 500, 1000],
        'count_fish': 50,
    }

    def __init__(self, driver, case):
        if not hasattr(case, 'count_fish'):
            self.count_fish = 100
        else:
            self.count_fish = case.count_fish

        super(fishietank, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_elements_by_class_name('control')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        index = 0
        counts_fish = self.CONFIG['counts_fish']
        for i in range(len(counts_fish)):
            if str(self.count_fish) == str(counts_fish[i]):
                index = i * 2 + 2
        if (index == 0):
            warning('count_fish in FishIETank is not correct, will use 100 instead')
            index = 10

        self.e[index].click()
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        pattern = re.compile('(\d+\.?\d*) FPS')
        match = pattern.search(driver.find_element_by_id('fpsCanvas').get_attribute('title'))
        return match.group(1)
