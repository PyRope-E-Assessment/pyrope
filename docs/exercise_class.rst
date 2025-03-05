
The Exercise Class
==================

In PyRope, every exercise is modelled by a separate subclass of the
:py:class:`pyrope.Exercise` class. This subclass serves as a container to put
together variables that contain metadata and functions that implement the
different elements of an exercise.

**If you are not familiar with classes:**
Don't worry! You do not need to know about object oriented programming to
write exercises in PyRope. You only need to keep a couple of things in mind:

* In simplified terms, a class is nothing but a way to bundle variables and
  functions together.
* The variables in a class are commonly called *attributes* and its functions
  *methods*.
* Methods have an additional first parameter, called ``self`` by convention.

Unless you want to use particular exercise types such as single or multiple
choice, the :py:class:`pyrope.Exercise` class is the only class you will come
across when writing basic exercises.

**If you are familiar with classes:**
The methods of the :py:class:`pyrope.Exercise` class are not meant to be
called directly, as there is a lot of magic behind the scenes. If you intend
to access the data derived in the course of an exercise, have a look at the
:py:class:`pyrope.core.ParametrizedExercise` class.


Exercise Methods
----------------

The different actions that have to be performed when running an exercise
interactively are modeled by particular methods of the
:py:class:`pyrope.Exercise` class and will be explained in more detail below.

=======================  ======================================================
Method                   Short description
=======================  ======================================================
:py:meth:`preamble`      give some context information
:py:meth:`parameters`    generate randomised parameters
:py:meth:`problem`       construct a template with the statement of the problem
:py:meth:`the_solution`  give a unique solution
:py:meth:`a_solution`    give a solution that is not necessarily unique
:py:meth:`hints`         provide hints on how to solve the exercise
:py:meth:`scores`        score the learner's answers
:py:meth:`feedback`      provide feedback based on the learners answers
=======================  ======================================================


Exercise Attributes
-------------------

Exercise metadata is stored in attributes of the :py:class:`pyrope.Exercise`
class. The use of metadata is not mandatory, but strongly suggested.
The following is a list of recommended metadata attributes which
will be recognised by PyRope. A more verbose description of
exercise metadata attributes can be found in the example template
:py:class:`pyrope.templates.QuadraticEquation`.

===============  ===================================================================
Attribute        Meaning
===============  ===================================================================
title            short description of the exercise
subtitle         additional information
author           author with email in the form ``John Doe <john.doe@infinity.org>``
license          software license
URL              URL, where the exercise can be found
pyrope_versions  PyRope version(s) the exercise has been tested with
origin           origin from which the exercise is derived, inspired or translated
discipline       main discipline of the exercise, such as "mathematics" or "physics"
area             area of the exercise, such as "linear algebra" or "mechanics"
topics           topics the exercise covers
keywords         keywords characterising the exercise
language         natural language in which the exercise is presented
taxonomy         taxonomy according to
                 `Bloom <https://en.wikipedia.org/wiki/Bloom%27s_taxonomy>`_
===============  ===================================================================

**Commentѕ**

* There is no explicit convention for metadata names either, but if you stick
  to the naming in the table above, you facilitate easy filtering of exercise
  pools based on keywords or search patterns.
* Avoid metadata depending on context, such as a course name or the difficulty
  of the exercise.
* If used, the above attributes must be strings.
* The attributes ``author``, ``discipline``, ``area``, ``topics``, ``keywords``
  and ``taxonomy`` each can also be a tuple of strings, ordered by relevance.
* An exercise can easily be translated into other languages by replacing only
  the language specific methods, i.e. the :py:meth:`preamble`,
  :py:meth:`problem`, :py:meth:`hints` and :py:meth:`feedback` methods.
  Metadata, documentation and comments should therefore be written in English.
* Exercise definitions are actually source code. So one should give a
  software license, preferably a liberal one to make the exercise an
  `Open Educational Resource <https://en.wikipedia.org/wiki/Open_educational_resources>`_.


