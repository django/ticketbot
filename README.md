# Django development helper bot: ticketbot

This is the bot which replaces the following types of mentions with their URLs:

* `"#nnnnn"` -- Django Trac's ticket #nnnnn
* `"!nnnn"` or `"PRnnnn"` -- Pull request nnnn submitted to the django/django GitHub repo
* `"hhhhhhhh"` (7 or more chars) -- Commit with ID hhhhhhh in the django/django GitHub repo

It has a registered user in Freenode: `ticketbot`.

## Configuration

It needs the following env vars:

* `NICKSERV_PASS` -- The bot's Freenode user password
* `CHANNELS` -- A comma-separated list of channels it will auto-join to

Example, for running it locally:

```
$ export NICKSERV_PASS=asecret
$ export CHANNELS=#django-social,#django,#django-dev,#django-sprint,#django-core
$ python ticketbot.py
```

## Tests

There are some test cases for the text matching code. You can run them with

```
$ python -m unittest tests.py
```
