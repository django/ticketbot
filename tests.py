import unittest

import ticketbot


class MatchingTests(unittest.TestCase):
    def test_ticket_ids(self):
        for msg, expected in [
            ('Asdf #1234 asdf', [1234]),
            ('#1234 works at the beginning', [1234]),
            ('Works at the end #1234', [1234]),
            ('#1234', [1234]),
            ('You can have several: #1234 #5678', [1234, 5678]),
            ('Not inside a word#1234', []),
            ('No single digit id: #7', []),
        ]:
            matches = ticketbot.get_matches(msg)
            self.assertEqual(matches.tickets, set(expected))

    def test_commit_id(self):
        for msg, expected in [
            ('Asdf d6ded0e91b asdf', ['d6ded0e91b']),
            ('d6ded0e91b works at the beginning', ['d6ded0e91b']),
            ('Works at the end d6ded0e91b', ['d6ded0e91b']),
            ('d6ded0e91b', ['d6ded0e91b']),
            ('d6ded0e', ['d6ded0e']),
            ('d6ded0e91bcdd2a8f7a221f6a5552a33fe545359', ['d6ded0e91bcdd2a8f7a221f6a5552a33fe545359']),
            ('d6ded0', []),
            ('d6ded0e91bcdd2a8f7a221f6a5552a33fe545359a', []),
            ('You can have several: d6ded0e91b 07ffc7d605', ['d6ded0e91b', '07ffc7d605']),
            ('Not inside a wordd6ded0e91b', []),
        ]:
            matches = ticketbot.get_matches(msg)
            self.assertEqual(matches.github_changesets, set(expected))

    def test_github_PR(self):
        for msg, expected in [
            ('Asdf PR1234 asdf', ['1234']),
            ('PR1234 works at the beginning', ['1234']),
            ('Works at the end PR1234', ['1234']),
            ('PR1234', ['1234']),
            ('You can have several: PR1234 PR5678', ['1234', '5678']),
            ('Not inside a wordPR1234', []),

            ('Asdf !1234 asdf', ['1234']),
            ('!1234 works at the beginning', ['1234']),
            ('Works at the end !1234', ['1234']),
            ('!1234', ['1234']),
            ('You can have several: !1234 !5678', ['1234', '5678']),
            ('Not inside a word!1234', []),
        ]:
            matches = ticketbot.get_matches(msg)
            self.assertEqual(matches.github_PRs, set(expected))

    def test_combining(self):
        msg = '#1234 r1234 12345678 PR1234 !5678'
        matches = ticketbot.get_matches(msg)
        self.assertEqual(matches, (
            set([1234]),
            set(['12345678']),
            set(['1234', '5678']),
        ))

    def test_get_links(self):
        m = ticketbot.MatchSet([1], [2], [3])
        links = ticketbot.get_links(m, sha_validation=lambda x: True)
        self.assertEqual(len(links), 3)

    def test_get_links_empty(self):
        m = ticketbot.MatchSet([], [], [])
        links = ticketbot.get_links(m, sha_validation=lambda x: True)
        self.assertEqual(links, [])
