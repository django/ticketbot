"""
The #django-dev ticket bot.
"""

from collections import namedtuple
import os
import re

import irc3
import requests

NICK = 'ticketbot'

ticket_re = re.compile(r'(?<!build)(?:^|\s)#(\d+)')
ticket_url = "https://code.djangoproject.com/ticket/%s"

github_sha_re = re.compile(r'(?:\s|^)([A-Fa-f0-9]{7,40})(?=\s|$)')
github_changeset_url = "https://github.com/django/django/commit/%s"
github_PR_re = re.compile(r'(?:\bPR|\B!)(\d+)\b')
github_PR_url = "https://github.com/django/django/pull/%s"


MatchSet = namedtuple('MatchSet',
                      ['tickets', 'github_changesets', 'github_PRs'])


def get_matches(message):
    """
    Given a message, return a tuple of various interesting things in it:
        * ticket ids
        * git commit ids
        * github PR ids
    """
    tickets = set(map(int, ticket_re.findall(message))).difference(
        set(range(0, 11))
    )  # #1-10 are ignored.
    github_changesets = set(github_sha_re.findall(message))
    github_PRs = set(github_PR_re.findall(message))

    return MatchSet(tickets, github_changesets, github_PRs)


def validate_sha_github(sha):
    """
    Make sure the given SHA belong to the Django tree.
    Works by making a request to the github repo.
    """
    r = requests.head(github_changeset_url % sha)
    return r.status_code == 200


def get_links(match_set, sha_validation=validate_sha_github):
    """
    Given a match_set (a tuple of matches returned by get_matches),
    return a list of links to show back to the user.

    The sha_validation argument is a callable that's used to validate
    the commit ids. Passing None skips the validation.
    """
    links = []
    for ticket in match_set.tickets:
        links.append(ticket_url % ticket)
    for PR in match_set.github_PRs:
        links.append(github_PR_url % PR)

    # validate github changeset SHA's
    for c in match_set.github_changesets:
        if sha_validation and sha_validation(c):
            links.append(github_changeset_url % c)

    return links


@irc3.plugin
class Plugin:

    def __init__(self, bot):
        self.bot = bot

    @irc3.event(irc3.rfc.PRIVMSG)
    def process_msg_or_privmsg(self, mask, event, target, data, **kw):
        """Detect special markers, reply with their respective links."""
        # We shouldn't send automatic replies to notices
        if event == 'NOTICE':
            return
        is_privmsg = target == self.bot.nick
        user = mask.nick
        matches = get_matches(data)

        # No content? Send helptext.
        if not any(matches) and (is_privmsg or data.startswith(self.bot.nick)):
            self.bot.privmsg(
                user,
                "Hi, I'm Django's ticketbot. I know how to linkify tickets "
                "like \"#12345\", github changesets like \"a00cf3d\" (minimum "
                "7 characters), and github pull requests like \"PR12345\" or \"!12345\"."
            )
            self.bot.privmsg(
                user,
                "Suggestions? Problems? Help make me better: "
                "https://github.com/django/ticketbot/"
            )
            return

        # Produce links
        links = get_links(matches)

        # Check to see if they're sending me a private message
        if is_privmsg:
            to = user
        else:
            to = target
        self.bot.privmsg(to, ' '.join(links))


def main():
    password = os.environ['NICKSERV_PASS']
    channels = os.environ['CHANNELS'].split(',')
    # instantiate a bot
    config = dict(
        nick=NICK,
        username=NICK,
        realname='Django project development helper bot',
        sasl_username=NICK,
        sasl_password=password,
        url='https://github.com/django/ticketbot',
        autojoins=channels,
        host='chat.freenode.net', port=6667, ssl=False,
        includes=[
            'irc3.plugins.core',
            'irc3.plugins.sasl',
            __name__,  # this register our Plugin
            ],
        # debug=True,
        # verbose=True,
        # raw=True,
    )
    bot = irc3.IrcBot.from_config(config)
    bot.run(forever=True)


if __name__ == '__main__':
    main()
