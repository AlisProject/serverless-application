from unittest import TestCase
from time_util import TimeUtil


class TestTimeUtil(TestCase):
    def test_generate_sort_key(self):
        sort_key = TimeUtil.generate_sort_key()

        self.assertEqual(len(str(sort_key)), 16)
        self.assertTrue(type(sort_key) is int)
