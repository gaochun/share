from benchmark import *


class canvas2dc10k(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'canvas2dc10k',
        'metric': metric_info['fps'],
        'path': {
            'external': '',
            'internal': 'webbench/canvas2d-c10k/'
        },
    }

    def __init__(self, driver, case):
        super(canvas2dc10k, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_element_by_id('fps')
        if self.e.text:
            return True
        else:
            return False

    def act0(self, driver):
        time.sleep(5)
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        return self.e.text.split()[2]
