"""
The #django-dev ticket bot.
"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import requests

from collections import namedtuple
import os
import re
import sys

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


class TicketBot(irc.IRCClient):
    """A bot for URLifying Django tickets."""

    nickname = "ticketbot"
    password = os.environ['NICKSERV_PASS']
    channels = os.environ['CHANNELS'].split(',')

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.setNick(self.nickname)
        self.msg('NickServ', 'identify %s' % (self.password))
        for channel in self.channels:
            self.join(channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        matches = get_matches(msg)

        # No content? Send helptext.
        if msg.startswith(self.nickname) and not any(matches):
            self.msg(
                user,
                "Hi, I'm Django's ticketbot. I know how to linkify tickets "
                "like \"#12345\", github changesets like \"a00cf3d\" (minimum "
                "7 characters), subversion changesets like \"r12345\", and "
                "github pull requests like \"PR12345\" or \"!12345\"."
            )
            self.msg(
                user,
                "Suggestions? Problems? Help make me better: "
                "https://github.com/django/django-ticketbot/"
            )
            return

        # Produce links
        links = get_links(matches)

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            target = user
        else:
            target = channel
        self.msg(target, ' '.join(links))


class TicketBotFactory(protocol.ClientFactory):
    """A factory for TicketBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = TicketBot

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = TicketBotFactory()

    # connect factory to this host and port
    reactor.connectTCP("chat.freenode.net", 6667, f)

    # run bot
    reactor.run()
