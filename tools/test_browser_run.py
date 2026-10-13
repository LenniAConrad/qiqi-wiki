# SPDX-License-Identifier: GPL-3.0-only
"""A slow frame must not produce a misleadingly empty loading measurement."""
import unittest
from unittest.mock import Mock, patch

from browser_run import wait_document


class DocumentReadiness(unittest.TestCase):
    def test_waits_past_initial_blank_and_loading_target(self):
        client = Mock()
        client.script.side_effect = [
            {'url': 'about:blank', 'readyState': 'complete'},
            {'url': 'https://wiki.test/islands.html', 'readyState': 'loading'},
            {'url': 'https://wiki.test/islands.html', 'readyState': 'complete'},
        ]
        with patch('browser_run.time.sleep'):
            wait_document(client, 'https://wiki.test/islands.html')
        self.assertEqual(client.script.call_count, 3)

    def test_timeout_rejects_loading_document(self):
        client = Mock()
        client.script.return_value = {'url': 'https://wiki.test/islands.html', 'readyState': 'loading'}
        with self.assertRaisesRegex(TimeoutError, 'loading'):
            wait_document(client, 'https://wiki.test/islands.html', timeout=0)

    def test_complete_blank_document_is_not_the_requested_page(self):
        client = Mock()
        client.script.return_value = {'url': 'about:blank', 'readyState': 'complete'}
        with self.assertRaisesRegex(TimeoutError, 'about:blank'):
            wait_document(client, 'https://wiki.test/islands.html', timeout=0)


if __name__ == '__main__':
    unittest.main()
