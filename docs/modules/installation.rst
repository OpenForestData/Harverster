Installation
============

Installation page

Requiremenets
-------------

You need installed Docker and Docker-Compose to start project.

Docker
^^^^^^

- `Windows/macOS`_
- `GNU/Linux`_

`Docker Compose`_
^^^^^^^^^^^^^^^^^


Development
-----------

- Run project (GNU/Linux, macOS)::

    $ URL="localhost" docker-compose pull
    $ URL="localhost" docker-compose build
    $ URL="localhost" docker-compose up -d

- Run project (Windows)::

    $ $env:URL="localhost"; docker-compose pull
    $ $env:URL="localhost"; docker-compose build
    $ $env:URL="localhost"; docker-compose up -d

.. _Windows/macOS: https://docs.docker.com/desktop/
.. _GNU/Linux: https://docs.docker.com/engine/install/
.. _Docker Compose: https://docs.docker.com/compose/
