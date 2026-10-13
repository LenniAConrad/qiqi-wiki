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

    def test_short_menu_keeps_one_current_destination_for_every_page(self):
        pages = {page for page, _ in wiki_layout.NAV + wiki_layout.ATLAS}
        pages.update(topic['page'] for topic in wiki_layout.TOPICS)
        pages.update(guide['page'] for guide in build_wiki.read('guides')['guides'])
        pages.update(('changelog-wiki.html', 'mobs.html'))
        for page in pages:
            with self.subTest(page=page):
                nav = wiki_layout.nav_html(page)
                self.assertEqual(nav.count('aria-current='), 1)

    def test_catalog_search_does_not_surface_the_development_ledger(self):
        records = build_wiki.search_records()
        self.assertFalse(any(r['href'].startswith('features.html') for r in records))
        for title in ('Alder bow', 'Stone pickaxe', 'Swan', 'Flower meadow'):
            with self.subTest(title=title):
                self.assertTrue(any(r['title'] == title for r in records))


if __name__ == '__main__':
    unittest.main()
