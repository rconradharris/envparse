========
envparse
========

If you use Heroku and/or subscribe to the tenets of the
`12 Factor App <http://www.12factor.net/>`_
you'll be using a lot of environment variable-based configuration in your app.
``os.environ`` is a great choice to start off with but over time you'll find
yourself duplicating quite a bit of code around handling raw environment
variables.

``envparse`` aims to eliminate this duplicated, often inconsistent parsing
code and instead provide a single, easy-to-use wrapper that handles:

* Casting environment variables to a type::

    MAIL_ENABLED=1

    mail_enabled = env('MAIL_ENABLED', cast=bool)
    if mail_enabled:
        send_mail(...)

* Specifying defaults::

    max_rows = env('MAX_ROWS', cast=int, default=100)
    rows = query(limit=max_rows)

* Proxying values, useful in Heroku for wiring up the environment
  variables they provide to the ones that your app actually uses::

    MAILGUN_SMTP_LOGIN=foo          # Heroku provides this with add-on
    SMTP_LOGIN={MAILGUN_SMTP_LOGIN} # App uses proxied variable

    smtp_login = env('SMTP_LOGIN')
    assert smtp_login == 'foo'

Now if you switch to using Mandrill as an email provider, instead of having to
modify your app, you can simply make a configuration change::

    SMTP_LOGIN={MANDRILL_UESRNAME}

* Define a schema so you can only need to provide the type and defaults once::

    MAIL_ENABLED=0
    SMTP_LOGIN=bar

    # Bind schema to Env object to get schema-based lookups
    env = Env(MAIL_ENABLED=bool, SMTP_LOGIN=(str, 'foo'))
    assert env('MAIL_ENABLED') is False
    assert env('SMTP_LOGIN') == 'bar'

    ...later in the code...

    if env('MAIL_ENABLED'):
        send_email(...)
