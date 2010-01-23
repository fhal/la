
==================
Working with larry
==================

This section describes how to work with larrys.

.. contents::

All of the examples below assume that you have already imported larry:
::
    >>> from la import larry
    
More examples of what you can do with larrys are given in :ref:`reference`.    


Creating a larry
----------------

Let's begin by creating a larry (Labeled ARRaY):
::
    >>> y = larry([1, 2, 3])
    >>> y
    label_0
        0
        1
        2
    x
    array([1, 2, 3])
    
In the statement above the list is converted to a Numpy array and the labels
default to ``range(n)``, where *n* in this case is 3.

To use our own labels we pass them in when we construct a larry:
::
    >>> y = larry([[1.0, 2.0], [3.0, 4.0]], [['a', 'b'], [11, 13]])
    >>> y
    label_0
        a
        b
    label_1
        11
        13
    x
    array([[ 1.,  2.],
           [ 3.,  4.]])
           
In the example above, the first row is labeled 'a' and the second row is
labeled 'b'. The first and second columns are labeled 11 and 13, respectively.

Here is a more formal way to create a larry:
::
    >>> import numpy as np
    >>> x = np.array([[1, 2], [3, 4]])
    >>> label = [['north', 'south'], ['east', 'west']]
    
    >>> larry(x, label)
    label_0
        north
        south
    label_1
        east
        west
    x
    array([[1, 2],
           [3, 4]])

The labels, along any one axis, must be unique. Let's try to create a larry
with labels that are not unique:
::
    >>> larry([1, 2], [['a', 'a']])
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "la/la/deflarry.py", line 97, in __init__
        raise ValueError, msg % (i, value, key)
    ValueError: Elements of label not unique along axis 0. There are 2 labels named `a`.

The shape of the data array must agree with the shape of the label. Let's try
to create a larry whose data shape does not agree with the label shape:
::
    >>> larry([[1, 2], [3, 4]], [['a', 'b'], ['c']])
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "la/la/deflarry.py", line 86, in __init__
        raise ValueError, msg % i
    ValueError: Length mismatch in label and x along axis 1


Properties
----------

The shape, size, and type of a larry are the same as the underlying Numpy
array:
::
    >>> y = larry([[1.0, 2.0], [3.0, 4.0]], [['r0', 'r2'], ['c0', 'c1']])
    >>> y.shape
    (2, 2)
    >>> y.size
    4
    >>> y.ndim
    2
    >>> y.dtype
    dtype('float64') 
  
    
Missing values
--------------

NaNs in the data array (not the label) are treated as missing values:
::
    >>> import la
    >>> y = larry([1.0, la.nan, 3.0])
    >>> y.sum()
    4.0

Note that ``la.nan`` is the same as Numpy's NaN:
::
    >>> import numpy as np
    >>> la.nan is np.nan
    True

There are several larry methods that deal with missing values. See
:ref:`missing` in :ref:`reference`.      

Indexing
--------

In most cases, indexing into a larry is similar to indexing into a Numpy
array:
::
    >>> y = larry([[1.0, 2.0], [3.0, 4.0]], [['a', 'b'], [11, 13]])
    >>> y[:,0]
    label_0
        a
        b
    x
    array([ 1.,  3.])
    
Indexing by label name is only supported indirectly:
::
    >>> idx = y.labelindex('a', axis=0)
    >>> y[idx,:]
    label_0
        11
        13
    x
    array([ 1.,  2.])


Alignment
---------

Alignment is automatic when you add (or subtract, multiply, divide, logical
and, logical or) two larrys. To demonstrate, let's create two larrys that are
not aligned:
::
    >>> y1 = larry([1, 2], [['a', 'z']])
    >>> y2 = larry([1, 2], [['z', 'a']])
    
What is ``y1 + y2``?
::
    >>> y1 + y2
    label_0
        a
        z
    x
    array([3, 3])

Let's look at a more complicated example:
::
    >>> z1 = larry([1, 2], [['a', 'b']])
    >>> z2 = larry([3, 4], [['c', 'd']])

    >>> z1 + z2
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "la/la/deflarry.py", line 494, in __add__
        x, y, label = self.__align(other)
      File "la/la/deflarry.py", line 731, in __align
        raise IndexError, 'A dimension has no matching labels'
    IndexError: A dimension has no matching labels
    
Why did we get an index error when we tried to sum *z1* and *z2*? We got an
error because *z1* and *z2* have no overlap: there are no elements 'a' and 'b'
in *z2* to add to those in *z1*.

Let's make a third larry that can be added to *z1*:
::
    >>> z3 = larry([3, 4], [['b', 'c']])
    >>> z1 + z3
    label_0
        b
    x
    array([5])
    
Note that the only overlap between *z1* and *z3* is the second element of *z1*
(labeled 'b') with the first element of *z3* (also labeled 'b').

Although we cannot sum *z1* and *z2*, we can merge them:
::
    >>> z1.merge(z2)
    label_0
        a
        b
        c
        d
    x
    array([ 1.,  2.,  3.,  4.])
       
It is often convenient to pre-align larrys. To align two larrys we use the
``morph`` method:
::
    >>> y1 = larry([1, 2, 3], [['a', 'b', 'c']])
    >>> y2 = larry([6, 4, 5], [['c', 'a', 'b']])

    >>> y2.morph_like(y1)
    label_0
        a
        b
        c
    x
    array([ 4.,  5.,  6.])
    
Alternatively, when we only want to align the larry along one axis (the
example above only contain one axis):    
::    
    >>> y2.morph(y1.getlabel(axis=0), axis=0)
    label_0
        a
        b
        c
    x
    array([ 4.,  5.,  6.])
    
We can also morph an array with labels that do not yet exist ('d' and 'e' in
the following example):
::
    >>> lar.morph(['a', 'b', 'c', 'd', 'e'], axis=0)
    label_0
        a
        b
        c
        d
        e
    x
    array([  1.,   2.,   3.,  NaN,  NaN])   


Archiving
---------

The archiving of larrys is described in :ref:`archive`.


Performance
-----------


Known issues
------------




    
    
               

  

        