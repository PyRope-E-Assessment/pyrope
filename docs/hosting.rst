Hosting
=====

The ``serve`` command starts a lightweight web server to browse and run a quiz made of multiple PyRope exercises.

Usage
-----

.. code-block:: console

    python -m pyrope serve mypool.py [--webdir=/path/to/webdir]

Access
~~~~~~

By default, the server is reachable at:

``http://localhost:8000``

Stop the server with ``Ctrl+C`` in the terminal.

Arguments
~~~~~~~~~

``mypool.py``
    Python file containing exactly **one** ``Quiz`` object.  
    This quiz will be displayed in the web interface.

Options
~~~~~~~

``--webdir PATH``
    Path to a folder containing the web interface files: ``index.html`` and a ``static/`` folder.  
    Copy the default from ``pyrope/web`` if you want a starting point to make custom changes.

Quiz Parameters
---------------

Each ``Quiz`` is a recursive object of Exercises or subsequent Quizzes, and may define the following attributes:

``title`` : *string*  
    Name of the quiz.

``select`` : *int*, default ``0``  
    Number of items to select randomly per quiz run.  
    If nonzero, all items must have the same maximal score to ensure the overall score does not depend on selection.  
    If ``0``, all items are included.

``shuffle`` : *bool*, default ``False``  
    Whether to shuffle the chosen items or keep their defined order.

``navigation`` : ``'free'`` or ``'sequential'``, default ``'free'``  
    ``free`` = items accessible in any order.  
    ``sequential`` = next item unlocked only after the previous is submitted.

``weights`` : *dict*, optional  
    Mapping from item index to weight for score calculation.


Public Hosting
--------------

When you run ``serve``, PyRope starts two components:

* **FastAPI (web interface)** - serves ``index.html``, which displays the quiz structure and navigation.
* **Voila (exercise runner)** - renders each exercise in the quiz as an individual notebook.

Each exercise is embedded in the main ``index.html`` page via an iframe.

The frontend uses:

* **Local testing** → iframe URL: ``localhost:8866``
* **Public hosting** → iframe URL: ``/voila/``

For public hosting, make both services available at these locations:

.. code-block:: nginx

    location / { proxy_pass http://127.0.0.1:8000; }
    location /voila/ { proxy_pass http://127.0.0.1:8866/; }
