import unittest
from util import *


class UtilTest(unittest.TestCase):
    def setUp(self):
        self.dir_src = '/workspace/project/chromium-android/src'

    def tearDown(self):
        pass

    def test_chromium_get_rev_hash(self):
        hash_tmp = chromium_get_hash(self.dir_src, 322729)
        self.assertEqual(hash_tmp, '2e9f5cad520549b6d07ab5c0493e32ec3719613a')

        hash_tmp = chromium_get_hash(self.dir_src, 322730)
        self.assertEqual(hash_tmp, 'edb297cebca3f835992cf0fb7592ecffce118a2f')

        hash_tmp = chromium_get_hash(self.dir_src, 888888)
        self.assertEqual(hash_tmp, '')

    def test_chromium_get_roll_count(self):
        rev_tmp = 297179
        chromium_get_src_info(self.dir_src, rev_tmp, rev_tmp)
        count_tmp = chromium_src_info[self.dir_src][CHROMIUM_SRC_INFO_INDEX_ROLL_INFO][rev_tmp][CHROMIUM_ROLL_INFO_INDEX_COUNT]
        self.assertEqual(count_tmp, 9)


if __name__ == '__main__':
    unittest.main()
