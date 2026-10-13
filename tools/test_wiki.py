# SPDX-License-Identifier: GPL-3.0-only
"""Navigation regressions: no orphaned articles or ambiguous parent topics."""
import copy
import unittest

import build_wiki
import validate_wiki
import wiki_layout


class Topics(unittest.TestCase):
    def test_missing_or_duplicate_article_membership_is_rejected(self):
        guides = build_wiki.read('guides')['guides']
        for change in ('missing', 'duplicate'):
            topics = copy.deepcopy(wiki_layout.TOPICS)
            slug = topics[0]['guides'].pop()
            if change == 'duplicate':
                topics[0]['guides'].extend([slug, slug])
            with self.subTest(change=change), self.assertRaisesRegex(AssertionError, 'exactly one topic'):
                validate_wiki.validate_topics(topics, guides)

    def test_article_parent_wins_over_cross_links(self):
        # Getting started links installation, but its parent is Troubleshooting.
        self.assertEqual(wiki_layout.topic_for_page('guide-install-and-worlds.html')['id'], 'troubleshooting')
        # Items also links hunting; animal interaction owns the guide.
        self.assertEqual(wiki_layout.topic_for_page('guide-hunting.html')['id'], 'mobs')

    def test_unknown_related_topic_is_rejected(self):
        topics = copy.deepcopy(wiki_layout.TOPICS)
        topics[0]['related'].append('unwritten')
        with self.assertRaisesRegex(AssertionError, 'Invalid related topic'):
            validate_wiki.validate_topics(topics, build_wiki.read('guides')['guides'])


if __name__ == '__main__':
    unittest.main()
