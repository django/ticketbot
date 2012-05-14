"""
The #django-dev ticket bot.
"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import requests

import os
import sys
import re

ticket_re = re.compile(r'(?<!build)(?:^|\s)#(\d+)')
ticket_url = "https://code.djangoproject.com/ticket/%s"

svn_changeset_re = re.compile(r'\br(\d+)\b')
svn_changeset_re2 = re.compile(r'(?:^|\s)\[(\d+)\]')
svn_changeset_url = "https://code.djangoproject.com/changeset/%s"

github_sha_re = re.compile(r'(?:\s|^)([A-Fa-f0-9]{7,40})(?=\s|$)')
github_changeset_url = "https://github.com/django/django/commit/%s"


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
        tickets = set(ticket_re.findall(msg)).difference(
                  set(range(0, 11)))  # #1-10 are ignored.
        svn_changesets = set(svn_changeset_re.findall(msg)).union(
                         set(svn_changeset_re2.findall(msg)))
        github_changesets = set(github_sha_re.findall(msg))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            target = user
        else:
            target = channel

        # No content? Send helptext.
        has_entities = tickets and svn_changesets and github_changesets
        if msg.startswith(self.nickname) and not has_entities:
            self.msg(user, "Hi, I'm Django's ticketbot. I know how to linkify tickets like \"#12345\", github changesets like \"a00cf3d\" (minimum 7 characters), and subversion changesets like \"r12345\" or \"[12345]\".")
            self.msg(user, "Suggestions? Problems? Help make me better: https://github.com/idangazit/django-ticketbot/")
            return

        # Produce links
        for ticket in tickets:
            self.msg(target, ticket_url % ticket)
        for changeset in svn_changesets:
            self.msg(target, svn_changeset_url % changeset)

        # validate github changeset SHA's
        for c in github_changesets:
            r = requests.head(github_changeset_url % c)
            if r.status_code == 200:
                self.msg(target, github_changeset_url % c)


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
