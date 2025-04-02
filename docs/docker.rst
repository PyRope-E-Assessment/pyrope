======
Docker
======

Instruction on how to use PyRope in Docker

Prerequisites
=============

* **Docker Desktop** installed and is running

Basic Commands
==============

Build the PyRope image
----------------------

This is currently only possible from source. The possibility to pull it from DockerHub is planned for a future release. 

.. code:: console

  docker build . -t pyrope -f <<Dockerfile>>

Replace ``<<Dockerfile>>`` with the name of the file you want to use. There are 3 different Dockerfiles available which differ in the Python version they use (3.10, 3.11 and 3.12).

Start the PyRope container
--------------------------

.. code:: console

  docker run -p 8888:8888 pyrope

Container usage
===============

* to access the Jupyter notebook, copy the link beginning with ``http://127.0.0.1:...`` from the console and open it in your browser

* use Docker Desktop GUI for stopping and (re)starting of already created container (console with the link can be found by clicking the container's name)

How to get your exercises into the container
============================================

There are 3 different ways to get your own exercises into the container:

1. Place them in the resources
------------------------------

Open the downloaded repository and create a file ``exercises.py`` in the ``pyrope`` folder. Write your exercises into this file and save it. After that, build the container with the command above.

This method is only recommended if you don't want to change your exercises frequently, because you have to rebuild your container every time which may take some minutes.

2. Bind your file when starting the container
---------------------------------------------

Open a terminal in the folder where the files with your exercises is. With this method, there is no naming convention for the file (but must be ``.py`` file). It gets copied into the container with an extra ``-v`` option when starting the container:

.. code:: console

  docker run -p 8888:8888 -v ./<<your-exercise-file>>:/pyrope/exercises.py pyrope

This is only recommended if the executing person may have access to the exercises file (because it also contains the solutions...).

3. Write a Dockerfile
---------------------

You can write a Dockerfile which uses your previously built ``pyrope`` image as base image and in a second step copies your exercise file into ``/pyrope/exercises.py``. This could look something like this:

.. code:: docker

  FROM pyrope
  COPY <<your-exercise-file>> /pyrope/exercises.py

With this method you can create your own version of PyRope with your exercises so you don't need to give your exercises file away but profit from fast container rebuild. You can also share this container with your students e. g. if you upload it to DockerHub.