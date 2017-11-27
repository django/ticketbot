# ticketbot -- The Django development helper IRC bot

This is the bot which replaces the following types of mentions with their URLs:

* `"#nnnnn"` -- Django Trac's ticket #nnnnn
* `"!nnnn"` or `"PRnnnn"` -- Pull request nnnn submitted to the django/django GitHub repo
* `"hhhhhhh"` (7 or more chars) -- Commit with ID hhhhhhh in the django/django GitHub repo

It has a registered nick in Freenode: *ticketbot*.

## Local setup

1. Create a virtualenv making sure you use the same Python version as the one specified to Heroku in `runtime.txt`:

       $ curl https://raw.githubusercontent.com/django/ticketbot/master/runtime.txt
       python-3.6.3

2. Once you've created and activated the virtualenv, install project dependencies:

       $ pip install -r requirements.txt

## Configuration

It needs the following env vars:

* `NICKSERV_PASS` -- The bot's Freenode user password
* `CHANNELS` -- A comma-separated list of channels it will auto-join to

Example, for running it locally:

    $ export NICKSERV_PASS=password
    $ export CHANNELS=#django-social,#django,#django-dev,#django-sprint,#django-core
    $ python ticketbot.py

## Tests

There are some test cases for the text matching code. You can run them with:

    $ python -m unittest tests.py
