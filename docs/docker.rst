======
Docker
======

Instruction on how to use PyRope in Docker

Prerequisites
=============

* **Docker Desktop** installed and is running

Commands for creation of container
==================================

Without notebook saving
-----------------------

* building container: ``docker build . -t pyrope``

* starting container: ``docker run -p 8888:8888 pyrope``

Notebook saving via volume
--------------------------

* creating volume: ``docker volume create pyrope-notebooks``

* building container: ``docker build . -t pyrope``

* starting container: ``docker run -p 8888:8888 -v pyrope-notebooks:/work pyrope``

Container usage
===============

* to access the notebook, copy the link beginning with ``http://127.0.0.1:...`` from the console and open it in your browser

* use Docker Desktop GUI for stopping and (re)starting of already created container (console with the link can be found by clicking the container's name)