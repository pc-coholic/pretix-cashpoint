Pretix Cashpoint API plugin
===========================

This is a plugin for `pretix`_. 

Upon installation, it will offer a new REST API endpoint at ``/api/v1/organizers/<organizer>/orders/<orderid>/isNowMagicallyPayed``, that will allow you to set the status of an order manually to "payed" - just like if you would have pushed to "Mark as payed" in the pretix backend.

This plugin leverages the same API-tokens that are available to the current read-only API as outlined [here](https://docs.pretix.eu/en/latest/api/fundamentals.html#obtaining-an-api-token)

As this plugin and operation is more of a doohickey and __not__ thoroughly tested, you might want to limit the activiation of the plugin to when you actually need it. As an additional precaution, you might want to limit access to the API, too.

This plugin is supposed to interact with the `de.pccoholic.pretix.cashpoint`_ android app, which facilitates marking orders as payed from mobile devices.

Production setup - pip method
-----------------------------

1. Activate - if applicable your pretix `venv`

2. ``pip install pretix-cashpoint``

3. python3 -m pretix migrate

4. python3 -m pretix rebuild

5. Restart your pretix processes: ``systemctl restart pretix-web pretix-worker``

Production setup - installation from git
----------------------------------------

Follow the instructions of the development setup. But instead of ``python setup.py develop`` in the plugin directory, run ``pip install .`` instead. ``python setup.py setup`` will not work.

Development setup
-----------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository, eg to ``local/pretix-cashpoint``.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.


License
-------

Copyright 2017 Martin Gross

Released under the terms of the Apache License 2.0


.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
.. _de.pccoholic.pretix.cashpoint: https://github.com/pc-coholic/de.pccoholic.pretix.cashpoint
