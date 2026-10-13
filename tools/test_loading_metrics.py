# SPDX-License-Identifier: GPL-3.0-only
"""A hidden HTML transfer must never look like a cheap complete mobile page."""
import unittest

from loading_metrics import body_totals


class TimingAccounting(unittest.TestCase):
    def test_redacted_mobile_document_does_not_become_a_zero_byte_page(self):
        result = body_totals([{'url': 'page.html', 'encoded': 0, 'transfer': 0}],
                             [{'url': 'style.css', 'encoded': 1200, 'transfer': 1500}])
        self.assertIsNone(result['encodedBytes'])
        self.assertIsNone(result['transferBytes'])
        self.assertEqual(result['reportedEncodedBytes'], 1200)
        self.assertEqual(result['unmeasuredBodies'], ['page.html'])
        self.assertEqual(result['requests'], 2)

    def test_a_complete_page_still_has_a_total(self):
        result = body_totals([{'url': 'page.html', 'encoded': 8000, 'transfer': 8300}],
                             [{'url': 'style.css', 'encoded': 1200, 'transfer': 1500}])
        self.assertEqual(result['encodedBytes'], 9200)
        self.assertEqual(result['transferBytes'], 9800)
        self.assertEqual(result['unmeasuredBodies'], [])

    def test_an_unreported_resource_also_prevents_a_complete_total(self):
        result = body_totals([{'url': 'page.html', 'encoded': 8000, 'transfer': 8300}],
                             [{'url': 'picture.webp', 'encoded': 0, 'transfer': 0}])
        self.assertIsNone(result['encodedBytes'])
        self.assertEqual(result['unmeasuredBodies'], ['picture.webp'])


if __name__ == '__main__':
    unittest.main()
