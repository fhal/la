"Labeled array class"

import datetime
from copy import deepcopy

import numpy as np
   
from la.util.scipy import (nanmean, nanmedian, nanstd)
from la.util.misc import flattenlabel, isscalar, fromlists, list2index
from la.afunc import (group_ranking, group_mean, group_median, covMissing,
                      fillforward_partially, quantile, ranking, lastrank,
                      movingsum_forward, lastrank_decay, movingrank,
                      movingsum, shuffle, nans)


class larry(object):
    "Labeled array"

    def __init__(self, x, label=None):
        """
        Meet larry, he's a labeled array.
        
        Parameters
        ----------
        x : numpy array_like
            Data, NaN are treated as missing data.
        label : {list of lists, None}, optional
            A list with labels for each dimension of x. If x is 2d, for
            example, then label should be a list that contains two lists, one
            for the row labels and one for the column labels. If x is 1d label
            should be a list that contain one list of names. If label is None
            (default) integers will be used to label the the row, columns,
            etc.
            
        Raises
        ------
        ValueError
            If x cannot be converted to a numpy array, or if the number of
            elements in label does not match the dimensions of x, or if the
            elements in label are not unique along each dimension, or if the
            elements of label are not lists.
            
        Examples
        --------
        The labels default to range(n):
        
        >>> larry([6, 7, 8])
        label_0
            0
            1
            2
        x
        array([6, 7, 8])

        A more formal way to make a larry:

        >>> import numpy as np
        >>> x = np.array([1,2,3])
        >>> label = [['one', 'two', 'three']]
        >>> larry(x, label)
        label_0
            one
            two
            three
        x
        array([1, 2, 3])    

        """
        if type(x) is not np.ndarray:
            # The if statement above is faster than asarray. When you add two
            # larrys, for example, it will use __init__ to create the result,
            # so any improvement in speed is good. That's why this entire
            # block of code is not replaced with x = np.asarray(x)
            try:
                x = np.asarray(x)
            except:
                raise ValueError, "x must be array_like."    
        if label is None:
            label = [range(z) for z in x.shape]
        if x.ndim != len(label):
            ValueError, 'Exactly one label per dimension needed'
        for i, l in enumerate(label):
            nlabel = len(l)
            if x.shape[i] != nlabel:
                msg = 'Length mismatch in label and x along axis %d'
                raise ValueError, msg % i
            if len(frozenset(l)) != nlabel:
                # We have duplicates in the label, give an example
                count = {}
                for li in l:
                    count[li] = count.get(li, 0) + 1
                for key, value in count.iteritems():
                    if value > 1:
                        break 
                msg = "Elements of label not unique along axis %d. "
                msg += "There are %d labels named `%s`."          
                raise ValueError, msg % (i, value, key)
            if type(l) is not list:
                raise ValueError, 'label must be a list of lists'
        self.x = x
        self.label = label

    # Unary functions --------------------------------------------------------  

    def log(self):
        """
        Element by element base e logarithm.
        
        Returns
        -------
        out : larry
            Returns a copy with log of x values.
        
        Examples
        --------
        >>> y = larry([1, 2, 3])
        >>> y.log()
        label_0
            0
            1
            2
        x
        array([ 0.        ,  0.69314718,  1.09861229])
        >>>
        
        """
        x = np.log(self.x)
        label = self.copylabel()
        return larry(x, label) 

    def exp(self):
        """
        Element by element exponential.
        
        Returns
        -------
        out : larry
            Returns a copy with exp of x values.

        Examples
        --------            
        >>> y = larry([1, 2, 3])
        >>> y.exp()
        label_0
            0
            1
            2
        x
        array([  2.71828183,   7.3890561 ,  20.08553692])            
                
        """
        x = np.exp(self.x)
        label = self.copylabel()
        return larry(x, label)
        
    def sqrt(self):
        """
        Element by element square root.
        
        Returns
        -------
        out : larry
            Returns a copy with square root of x values.

        Examples
        --------            
        >>> y = larry([1, 4, 9])
        >>> y.sqrt()
        label_0
            0
            1
            2
        x
        array([ 1.,  2.,  3.])
                
        """
        x = np.sqrt(self.x)
        label = self.copylabel()
        return larry(x, label)

    def sign(self):
        """
        Element by element sign of the element.
        
        Returns -1 if x < 0; 0 if x == 0, and 1 if x > 0.
        
        Returns
        -------
        out : larry
            Returns a copy with the sign of the values.
            
        Examples
        --------
        >>> y = larry([-1, 2, -3, 4])
        >>> y.sign()
        label_0
            0
            1
            2
            3
        x
        array([-1,  1, -1,  1])
                
        """
        x = np.sign(self.x)
        label = self.copylabel()
        return larry(x, label)
        
    def power(self, q):               
        """
        Element by element x**q.
                
        Parameters
        ----------
        q : scalar
            The power to raise to.
        
        Returns
        -------
        out : larry
            Returns a copy with x values to the qth power.

        Examples
        --------
        >>> y = larry([1, 2, 3])
        >>> y.power(2)
        label_0
            0
            1
            2
        x
        array([1, 4, 9])
                
        """
        x = np.power(self.x, q)
        label = self.copylabel()
        return larry(x, label)
        
    def __pow__(self, q):
        """
        Element by element x**q.
                
        Parameters
        ----------
        q : scalar
            The power to raise to.
        
        Returns
        -------
        out : larry
            Returns a copy with x values to the qth power.
                
        """
        return self.power(q)           
        
    def cumsum(self, axis): 
        """
        Cumulative sum, ignoring NaNs.
        
        Parameters
        ----------
        axis : int
            axis to cumsum along, no default. None is not allowed.
            
        Returns
        -------
        out : larry
            Returns a copy with cumsum along axis.  
            
        Raises
        ------
        AssertionError
            If axis is None.
            
        Examples
        --------
        >>> y = larry([1, 2, 3])
        >>> y.cumsum(axis=0)
        label_0
            0
            1
            2
        x
        array([1, 3, 6])                        
                        
        """
        assert axis is not None, 'axis cannot be None'
        y = self.copy()
        y[np.isnan(y.x)] = 0
        y.x.cumsum(axis, out=y.x)
        return y        

    def cumprod(self, axis): 
        """
        Cumulative product, ignoring NaNs.
        
        Parameters
        ----------
        axis : int
            axis to find the cumulative product along, no default. None is
            not allowed.
            
        Returns
        -------
        out : larry
            Returns a copy with cumprod along axis.  
            
        Raises
        ------
        AssertionError
            If axis is None.
            
        Examples
        --------
        >>> y = larry([1, 2, 3])
        >>> y.cumprod(axis=0)
        label_0
            0
            1
            2
        x
        array([1, 2, 6])                       
                        
        """
        assert axis is not None, 'axis cannot be None'
        y = self.copy()
        y[np.isnan(y.x)] = 1
        y.x.cumprod(axis, out=y.x)
        return y

    def clip(self, lo, hi):
        """
        Clip x values.

        Parameters
        ----------
        lo : scalar
            All data values less than `lo` are set to `lo`.
        hi : scalar    
            All data values greater than `hi` are set to `hi`.
                        
        Returns
        -------
        out : larry
            Returns a copy with x values clipped.       
            
        Raises
        ------
        AssertionError
            If `lo` is greater than `hi`.
            
        Examples
        --------
        >>> y = larry([1, 2, 3, 4])
        >>> y.clip(2, 3)
        label_0
            0
            1
            2
            3
        x
        array([2, 2, 3, 3])                    
        
        """
        assert lo <= hi, 'lo should be less than or equal to hi'
        y = self.copy()
        y.x.clip(lo, hi, y.x)
        return y
        
    def __neg__(self):
        "Return a copy with each element multiplied by minus 1."
        y = self.copy()
        y.x *= -1
        return y
    
    def __pos__(self):
        "Return a copy with each element multiplied by 1."
        return self.copy()
        
    def abs(self):
        """
        Absolute value of x.
        
        Returns
        -------
        out : larry
            Returns a copy with the absolute values of the x data.

        Examples
        --------
        >>> y = larry([-1, 2, -3, 4])
        >>> y.abs()
        label_0
            0
            1
            2
            3
        x
        array([1, 2, 3, 4])
       
        """
        y = self.copy()
        np.absolute(y.x, y.x)
        return y
        
    def __abs__(self):
        """
        Absolute value of x.
        
        Returns
        -------
        out : larry
            Returns a copy with the absolute values of the x data.
       
        """    
        return self.abs()
        
    def isnan(self):
        """
        Returns a bool larry with NaNs replaced by True, non-NaNs False.

        Returns
        -------
        out : larry
            Returns a copy with NaNs replaced by True, non-NaNs False.
        
        Examples
        --------
        >>> import la
        >>> y = larry([-la.inf, 1.0, la.nan, la.inf])
        >>> y.isnan()
        label_0
            0
            1
            2
            3
        x
        array([False, False,  True, False], dtype=bool)

        """
        label = self.copylabel()
        x = np.isnan(self.x)
        return type(self)(x, label)                             

    def isfinite(self):
        """
        Returns a bool larry with NaNs and Inf replaced by True, others False.

        Returns
        -------
        out : larry
            Returns a copy with NaNs and Inf replaced by True, others False.

        Examples
        --------        
        >>> import la
        >>> y = larry([-la.inf, 1.0, la.nan, la.inf])
        >>> y.isfinite()
        label_0
            0
            1
            2
            3
        x
        array([False,  True, False, False], dtype=bool)
        
        """    
        label = self.copylabel()
        x = np.isfinite(self.x)
        return type(self)(x, label)
        
    def isinf(self):
        """Returns a bool larry with -Inf and Inf replaced by True, others False.

        Returns
        -------
        out : larry
            Returns a copy with -Inf and Inf replaced by True, others False.
        
        Examples
        --------
        >>> import la
        >>> y = larry([-la.inf, 1.0, la.nan, la.inf])
        >>> y.isinf()
        label_0
            0
            1
            2
            3
        x
        array([ True, False, False,  True], dtype=bool)
        
        """    
        label = self.copylabel()
        x = np.isinf(self.x)
        return type(self)(x, label)                        
        
    # Binary Functions ------------------------------------------------------- 
    
    # We need this to take care of radd and rsub when a matrix is on the left-
    # hand side. Without it, the matrix object will use broadcasting, treating
    # larry objects as scalars.
    __array_priority__ = 10                      
        
    def __add__(self, other):
        """Sum a larry with another larry, Numpy array, or scalar.
        
        Examples
        --------
        >>> larry([1.0, 2.0]) + larry([2.0, 3.0])
        label_0
            0
            1
        x
        array([ 3.,  5.])        
        
        >>> y1 = larry([1,2], [['a', 'b']])
        >>> y2 = larry([1,2], [['b', 'c']])
        >>> y1 + y2
        label_0
            b
        x
        array([3])        
        
        """
        if isinstance(other, larry):
            if self.label == other.label:
            	x = self.x + other.x
                label = self.copylabel()
                return larry(x, label)                        
            else:       
                x, y, label = self.__align(other)
                x = x + y
                return type(self)(x, label)
        if np.isscalar(other) or isinstance(other, np.ndarray):
            x = self.x + other
            label = self.copylabel()
            return larry(x, label)                 
        raise TypeError, 'Input must be scalar, array, or larry.' 
    
    __radd__ = __add__
    
    def __sub__(self, other):
        """
        Subtract a larry from another larry, Numpy array, or scalar.
        
        Examples
        --------
        >>> larry([1.0, 2.0]) - larry([2.0, 3.0])
        label_0
            0
            1
        x
        array([-1., -1.])        
        
        >>> y1 = larry([1,2], [['a', 'b']])
        >>> y2 = larry([1,2], [['b', 'c']])
        >>> y1 - y2
        label_0
            b
        x
        array([1])        
        """   
        if isinstance(other, larry):
            if self.label == other.label:
            	x = self.x - other.x
                label = self.copylabel()
                return larry(x, label)                          
            else:          
                x, y, label = self.__align(other)        
                x = x - y
                return type(self)(x, label)
        if np.isscalar(other) or isinstance(other, np.ndarray):
            x = self.x - other
            label = self.copylabel()
            return larry(x, label)       
        raise TypeError, 'Input must be scalar, array, or larry.'
        
    def __rsub__(self, other):
        "Right subtract a larry with a another larry, Numpy array, or scalar."
        return -self.__sub__(other)       

    def __div__(self, other):
        """Divide a larry with a another larry, Numpy array, or scalar.
        
        Examples
        -------- 
        
        >>> larry([1.0, 2.0]) / larry([2.0, 3.0])
        label_0
            0
            1
        x
        array([ 0.5       ,  0.66666667])        
        
        >>> y1 = larry([1,2], [['a', 'b']])
        >>> y2 = larry([1,2], [['b', 'c']])
        >>> y1 / y2
        label_0
            b
        x
        array([2])        
               
        """    
        if isinstance(other, larry):
            if self.label == other.label:
            	x = self.x / other.x
                label = self.copylabel()
                return larry(x, label)                          
            else:          
                x, y, label = self.__align(other)        
                x = x / y
                return type(self)(x, label)
        if np.isscalar(other) or isinstance(other, np.ndarray):
            x = self.x / other
            label = self.copylabel()
            return larry(x, label)        
        raise TypeError, 'Input must be scalar, array, or larry.'
        
    def __rdiv__(self, other):
        "Right divide a larry with a another larry, Numpy array, or scalar."                   
        if isinstance(other, larry):
            msg = 'I could not come up with a problem that used this code '
            msg += 'so I removed it. Send me your example and I will fix.'
            raise RuntimeError, msg                   
        if np.isscalar(other) or isinstance(other, np.ndarray):
            y = self.copy()
            y.x = other / y.x
            return y           
        raise TypeError, 'Input must be scalar, array, or larry.'
        
    def __mul__(self, other): 
        """
        Multiply a larry with a another larry, Numpy array, or scalar.
        
        Examples
        --------
        >>> larry([1.0, 2.0]) * larry([2.0, 3.0])
        label_0
            0
            1
        x
        array([ 2.,  6.])        
         
        >>> y1 = larry([1,2], [['a', 'b']])
        >>> y2 = larry([1,2], [['b', 'c']])
        >>> y1 * y2
        label_0
            b
        x
        array([2])        
                
        """      
        if isinstance(other, larry):
            if self.label == other.label:
            	x = self.x * other.x
                label = self.copylabel()
                return larry(x, label)                          
            else:           
                x, y, label = self.__align(other)
                x = x * y
                return type(self)(x, label)
        if np.isscalar(other) or isinstance(other, np.ndarray):
            x = self.x * other
            label = self.copylabel()
            return larry(x, label)   
        raise TypeError, 'Input must be scalar, array, or larry.'

    __rmul__ = __mul__

    def __and__(self, other):
        """Logical and a larry with a another larry, Numpy array, or scalar.
        
        Notes
        -----
        Numpy defines & as bitwise_and; here & is defined as
        numpy.logical_and.
        
        Examples
        --------
        >>> (larry([1.0, 2.0]) > 1) & (larry([2.0, 3.0]) > 1)
        label_0
            0
            1
        x
        array([False,  True], dtype=bool)        
        
        >>> y1 = larry([1,2], [['a', 'b']])
        >>> y2 = larry([1,2], [['b', 'c']])
        >>> (y1 > 0) & (y2 > 0)
        label_0
            b
        x
        array([ True], dtype=bool)                 
        
        """    
        if isinstance(other, larry):
            if self.label == other.label:
            	x = np.logical_and(self.x, other.x)
                label = self.copylabel()
                return larry(x, label)                      
            else:          
               x, y, label = self.__align(other)
               x = np.logical_and(x, y)
               return type(self)(x, label)
        if np.isscalar(other) or isinstance(other, np.ndarray):            
            x = np.logical_and(self.x, other)
            label = self.copylabel()
            return larry(x, label)
        raise TypeError, 'Input must be scalar, array, or larry.'

    __rand__ = __and__

    def __or__(self, other):
        """
        Logical or a larry with a another larry, Numpy array, or scalar.
        
        Notes
        -----
        Numpy defines | as bitwise_or; here & is defined as
        numpy.logical_or.

        Examples
        --------
        >>> (larry([1.0, 2.0]) > 1) | (larry([2.0, 3.0]) > 1)
        label_0
            0
            1
        x
        array([ True,  True], dtype=bool)        
        
        >>> y1 = larry([1,2], [['a', 'b']])
        >>> y2 = larry([1,2], [['b', 'c']])
        >>> (y1 > 0) | (y2 > 0)
        label_0
            b
        x
        array([ True], dtype=bool)
                        
        """     
        if isinstance(other, larry):
            if self.label == other.label:
            	x = np.logical_or(self.x, other.x)
                label = self.copylabel()
                return larry(x, label)                      
            else:          
               x, y, label = self.__align(other)
               x = np.logical_or(x, y)
               return type(self)(x, label)
        if np.isscalar(other) or isinstance(other, np.ndarray):            
            x = np.logical_or(self.x, other)
            label = self.copylabel()
            return larry(x, label)
        raise TypeError, 'Input must be scalar, array, or larry.'

    __ror__ = __or__

    def __align(self, other):
        "Align larrys for binary operations."
        if self.ndim != other.ndim:
            msg = 'Binary operation on two larrys with different dimension'
            raise IndexError, msg
        idxs = []
        idxo = []
        label = []
        shape = []
        for ls, lo in zip(self.copylabel(), other.label):
            if ls == lo:
                lab = ls
                ids = range(len(lab))
                ido = ids
            else:
                lab = list(frozenset(ls) & frozenset(lo))
                if len(lab) == 0:
                    raise IndexError, 'A dimension has no matching labels'
                lab.sort()
                ids = map(ls.index, lab)
                ido = map(lo.index, lab)
            label.append(lab)
            idxs.append(ids)
            idxo.append(ido)
            shape.append(len(lab))
        shape = tuple(shape)
        x = np.zeros(shape, dtype=self.x.dtype)
        x += self.x[np.ix_(*idxs)]
        y = other.x[np.ix_(*idxo)]
        return x, y, label
                  
    # Reduce functions -------------------------------------------------------   
        
    def sum(self, axis=None):
        """
        Sum of values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to sum along or sum over all (None, default).
            
        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.
            
        Examples
        --------
        >>> from la import nan 
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.sum()
        9.0
        >>> y.sum(axis=0)
        label_0
            0
            1
        x
        array([ 3.,  6.])
                    
        """
        return self.__reduce(axis, np.nansum)    

    def prod(self, axis=None):
        """
        Product of values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the product along or find the product over a
            all axes (None, default).
            
        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.
            
        Examples
        --------
        >>> from la import nan        
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.prod()
        24.0
        >>> y.prod(axis=0)
        label_0
            0
            1
        x
        array([ 3.,  8.])
             
        """
        y = self.nan_replace(1)
        return y.__reduce(axis, np.prod) 

    def mean(self, axis=None):
        """
        Mean of values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the mean along (integer) or the global mean (None,
            default).

        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.

        Examples
        --------
        >>> from la import nan
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.mean()
        3.0
        >>> y.mean(axis=0)
        label_0
            0
            1
        x
        array([ 3.,  3.])       
                    
        """
        return self.__reduce(axis, nanmean) 

    def median(self, axis=None):
        """
        Median of values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the median along (0 or 1) or the global median (None,
            default).
            
        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.

        Examples
        --------
        >>> from la import nan
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.median()
        3.0
        >>> y.median(axis=0)
        label_0
            0
            1
        x
        array([ 3.,  3.])
                    
        """
        return self.__reduce(axis, nanmedian) 
            
    def std(self, axis=None):
        """
        Standard deviation of values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the standard deviation along (integer) or the global
            standard deviation (None, default).

        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.

        Examples
        -------- 
        >>> from la import nan 
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.std()
        0.81649658092772603
        >>> y.std(axis=0)
        label_0
            0
            1
        x
        array([ 0.,  1.])  
                         
        """
        return self.__reduce(axis, nanstd)  
        
    def var(self, axis=None):
        """
        Variance of values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the variance along (integer) or the global variance
            (None, default).

        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.

        Examples
        -------- 
        >>> from la import nan
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.var()
        0.66666666666666663
        >>> y.var(axis=0)
        label_0
            0
            1
        x
        array([ 0.,  1.])
                    
        """
        y = self.__reduce(axis, nanstd)
        if np.isscalar(y):
            y *= y 
        else:       
            np.multiply(y.x, y.x, y.x)
        return y                 
                            
    def max(self, axis=None):
        """
        Maximum values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the max along (integer) or the global max (None,
            default).
            
        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.

        Examples
        -------- 
        >>> from la import nan
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.max()
        4.0
        >>> y.max(axis=0)
        label_0
            0
            1
        x
        array([ 3.,  4.])
                    
        """            
        return self.__reduce(axis, np.nanmax)             
           
    def min(self, axis=None):
        """
        Minimum values along axis, ignoring NaNs.

        Parameters
        ----------
        axis : {None, integer}, optional
            Axis to find the min along (integer) or the global min (None,
            default).
            
        Returns
        -------
        d : {larry, scalar}
            When axis is an integer a larry is returned. When axis is None
            (default) a scalar is returned (assuming larry contains scalars).
            
        Raises
        ------
        ValueError
            If axis is not an integer or None.

        Examples
        -------- 
        >>> from la import nan
        >>> y = larry([[nan, 2], [3,  4]])
        >>> y.min()
        2.0
        >>> y.min(axis=0)
        label_0
            0
            1
        x
        array([ 3.,  2.])
                    
        """
        return self.__reduce(axis, np.nanmin)  

    def __reduce(self, axis, op):
        if np.isscalar(axis):
            x = op(self.x, axis)
            if np.isscalar(x):
                return x
            else:    
                label = self.copylabel()
                label.pop(axis)
                return type(self)(x, label)      
        elif axis is None:
            return op(self.x, axis)
        else:
            raise ValueError, 'axis should be an integer or None'
        
    def any(self, axis=None):
        """
        True if any element along specified axis is True; False otherwise.

        Parameters
        ----------
        axis : {int, None}, optional
            The axis over which to reduce the truth. By default (axis=None)
            the larry is flattened before the truth is found. 
        
        Returns
        -------
        out : {larry, True, False}
            If `axis` is None then returns True if any data element of the
            larry (not including the label) is True; False otherwise. If
            `axis` is an integer then a bool larry is returned.
            
        Notes
        -----
        As in Numpy, NaN is True since it is not equal to 0.    

        Examples
        -------- 
        >>> y = larry([[1, 2], [3,  4]]) < 2
        >>> y
        label_0
            0
            1
        label_1
            0
            1
        x
        array([[ True, False],
               [False, False]], dtype=bool)
        >>> y.any()
        True
        >>> y.any(axis=1)
        label_0
            0
            1
        x
        array([ True, False], dtype=bool)
        
        """
        if axis is None:
            return self.x.any()
        else:
            return self.__reduce(axis, np.any)
        
    def all(self, axis=None):
        """
        True if all elements along specified axis are True; False otherwise.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis over which to reduce the truth. By default (axis=None)
            the larry is flattened before the truth is found.      
        
        Returns
        -------
        out : {larry, True, False}
            If `axis` is None then returns True if all data elements of the
            larry (not including the label) are True; False otherwise. If
            `axis` is an integer then a bool larry is returned.
            
        Notes
        -----
        As in Numpy, NaN is True since it is not equal to 0.                    

        Examples
        -------- 
        >>> y = larry([[1, 2], [3,  4]]) > 1
        >>> y
        label_0
            0
            1
        label_1
            0
            1
        x
        array([[False,  True],
               [ True,  True]], dtype=bool)
        >>> y.all()
        False
        >>> y.all(axis=0)
        label_0
            0
            1
        x
        array([False,  True], dtype=bool)
        
        """
        if axis is None:
            return self.x.all()
        else:
            return self.__reduce(axis, np.all)                                         
        
    # Comparision ------------------------------------------------------------                                              
        
    def __eq__(self, other):
        "Element by element equality (==) comparison."
        return self.__compare(other, '==')                   

    def __ne__(self, other):
        "Element by element inequality (!=) comparison."
        return self.__compare(other, '!=')                       

    def __lt__(self, other):
        "Element by element 'less than' (<) comparison."    
        return self.__compare(other, '<')  

    def __gt__(self, other):
        "Element by element 'greater than' (>) comparison."    
        return self.__compare(other, '>') 

    def __le__(self, other):
        "Element by element 'less than or equal to' (<=) comparison."    
        return self.__compare(other, '<=') 

    def __ge__(self, other):
        "Element by element 'greater than or equal to' (>=) comparison."     
        return self.__compare(other, '>=') 

    def __compare(self, other, op):         
        if np.isscalar(other) or isinstance(other, np.ndarray):
            y = self.copy()
            if op == '==':
                y.x = y.x == other
            elif op == '!=':
                y.x = y.x != other
            elif op == '<':
                y.x = y.x < other           
            elif op == '>':
                y.x = y.x > other           
            elif op == '<=':
                y.x = y.x <= other           
            elif op == '>=':
                y.x = y.x >= other           
            else:
                raise ValueError, 'Unknown comparison operator'
            return y                                                             
        elif isinstance(other, larry):
            x, y, label = self.__align(other)
            if op == '==':
                x = x == y
            elif op == '!=':
                x = x != y
            elif op == '<':
                x = x < y
            elif op == '>':
                x = x > y            
            elif op == '<=':
                x = x <= y            
            elif op == '>=':
                x = x >= y                              
            else:
                raise ValueError, 'Unknown comparison operator'              
            return type(self)(x, label)
        else:
            raise TypeError, 'Input must be scalar, numpy array, or larry.'

    # Get and set ------------------------------------------------------------
    
    def __getitem__(self, index):
        """Index into a larry.
        
        Examples
        --------
        >>> y = larry([[1, 2], [3,  4]])
        >>> y[0,0]
        1
        >>> y[0,:]
        label_0
            0
            1
        x
        array([1, 2])
        >>> y[:,1:]
        label_0
            0
            1
        label_1
            1
        x
        array([[2],
               [4]])
        
        """
        typidx = type(index)
        if isscalar(index):
            index = int(index)                
            if index >= self.shape[0]:
                raise IndexError, 'index out of range'
            label = self.label[1:]
            x = self.x[index]                     
        elif typidx is tuple:
            label = []
            for i in xrange(self.ndim):
                if i < len(index):
                    idx = index[i]
                    typ = type(idx)
                    if isscalar(idx):
                        if idx >= self.shape[i]:
                            raise IndexError, 'index out of range'
                        lab = None
                    elif typ is list or typ is tuple:
                        try:
                            lab = [self.label[i][z] for z in idx]
                        except IndexError:
                            raise IndexError, 'index out of range' 
                        lab = list(lab)                              
                    elif typ is np.ndarray:
                        if idx.dtype.type == np.bool_:
                            try:
                                lab = [self.label[i][j] for j, z in enumerate(idx) if z]
                            except IndexError:
                                raise IndexError, 'index out of range'                            
                        else:
                            try:
                                lab = [self.label[i][z] for z in idx]
                            except IndexError:
                                raise IndexError, 'index out of range' 
                        lab = list(lab)                          
                    elif typ is slice:
                        lab = self.label[i][idx]
                    else:
                        msg = 'I do not recognize the way you are indexing'
                        raise IndexError, msg                       
                else:
                    lab = self.label[i]
                if lab:     
                    label.append(lab)              
            x = self.x[index]
        elif typidx is slice:
            label = list(self.label)
            label[0] = label[0][index]
            x = self.x[index]
        elif typidx is list:
            label = list(self.label)
            label[0] = [label[0][int(i)] for i in index]
            x = self.x[index]                              
        else:        
            msg = 'Only slice, integer, and seq (list, tuple, 1d array)'
            msg = msg + ' indexing supported'
            raise IndexError, msg        
        if np.isscalar(x):
            return x                                
        return larry(x, label)
        
    def __setitem__(self, index, value):
        """
        Assign values to a subset of a larry using indexing to select subset.
        
        Examples
        --------
        Let's set all elements of a larry with values less then 3 to zero:
                
        >>> import numpy as np
        >>> x = np.array([[1, 2], [3, 4]])
        >>> label = [['a', 'b'], [8, 10]]
        >>> y = larry(x, label)
        >>> y[y < 3] = 0
        >>> y
        label_0
            a
            b
        label_1
            8
            10
        x
        array([[0, 0],
               [3, 4]])
        
        """
        if isinstance(index, larry):
            if self.label == index.label:
                self.x[index.x] = value
            else:
                # Could use morph to do this, if every row and column of self
                # is in index, but I think it is better to raise an IndexError
                msg = 'Indexing with a larry that is not aligned'
                raise IndexError, msg    
        else:
            self.x[index] = value
            
    def set(self, label, value):
        """
        Set one x element given a list of label names.
        
        Give one label name (not label index) for each dimension.
        
        Parameters
        ----------
        label : {list, tuple}
            List or tuple of one label name for each dimension. For example,
            for row label 'a' and column label 7: ('a', 7).
        value : Float, string, etc.
            Value to place in the single cell specified by label.
            
        Returns
        -------
        None
        
        Raises
        ------
        ValueError
            If the length of label is not equal to the number of dimensions of
            larry.        
        
        Examples
        --------
        >>> y = larry([[1, 2], [3, 4]], [['r0', 'r1'], ['c0', 'c1']])
        >>> y.set(['r0', 'c1'], 99)
        >>> y
        label_0
            r0
            r1
        label_1
            c0
            c1
        x
        array([[ 1, 99],
               [ 3,  4]])
        
        """
        if len(label) != self.ndim:
            raise ValueError, 'Must have exactly one label per dimension'
        index = []
        for i in xrange(self.ndim):
            index.append(self.labelindex(label[i], axis=i))    
        self.x[tuple(index)] = value        

    def get(self, label):
        """
        Get one x element given a list of label names.
        
        Give one label name (not label index) for each dimension.
        
        Parameters
        ----------
        label : {list, tuple}
            List or tuple of one label name for each dimension. For example,
            for row label 'a' and column label 7: ('a', 7).
            
        Returns
        -------
        out : scalar, string, etc.
            Value of the single cell specified by label.
        
        Raises
        ------
        ValueError
            If the length of label is not equal to the number of dimensions of
            larry.        

        Examples
        --------
        >>> y = larry([[1, 2], [3, 4]], [['r0', 'r1'], ['c0', 'c1']])
        >>> y.get(['r0', 'c1'])
        2
        
        """    
        if len(label) != self.ndim:
            raise ValueError, 'Must have exactly one label per dimension'
        index = []
        for i in xrange(self.ndim):
            index.append(self.labelindex(label[i], axis=i))    
        return self.x[tuple(index)]
                
    def getx(self, copy=True):
        """
        Return a copy of the x data or a reference to it.
        
        Parameters
        ----------
        copy : {True, False}, optional
            Return a copy (True, default) of the x values or a reference
            (False) to it.
            
        Returns
        -------
        out : array
            Copy or reference of x array.

        Examples
        --------
        >>> y = larry([0, 1, 2])
        >>> x = y.getx()
        >>> (x == y.x).all()
        True
        >>> x is y.x
        False
        >>> x = y.getx(copy=False)
        >>> x is y.x
        True
               
        """
        if copy:
            return self.x.copy()
        else:
            return self.x
            
    @property
    def A(self):
        """
        Return a reference to the underlying Numpy array.
        
        Examples
        --------
        >>> y = larry([1, 2, 3])
        >>> y.A
        array([1, 2, 3])
        >>> type(y.A)
        <type 'numpy.ndarray'>        
        
        """
        return self.x            
                    
    def getlabel(self, axis, copy=True):
        """
        Return a copy of the label or a reference to it.
        
        Parameters
        ----------
        axis : int
            The `axis` identifies the label you wish to get.         
        copy : {True, False}, optional
            Return a copy (True, default) of the label or a reference (False)
            to it.
            
        Returns
        -------
        out : list
            Copy or reference of the label.

        Examples
        --------
        Get a copy of the label:
        
        >>> y = larry([[1, 2], [3, 4]], [['r0', 'r1'], ['c0', 'c1']])
        >>> y.getlabel(axis=0)
        ['r0', 'r1']
        >>> y.getlabel(axis=1)
        ['c0', 'c1']
        
        The difference between a copy and a reference to the label:
        
        >>> label = y.getlabel(0)
        >>> label == y.label[0]
        True
        >>> label is y.label[0]
        False
        >>> label = y.getlabel(0, copy=False)
        >>> label is y.label[0]
        True        
               
        """
        if axis >= self.ndim:
            raise IndexError, 'axis out of range'
        label = self.label[axis]    
        if copy:
            label =  list(label)
        return label            
            
    def pull(self, name, axis):
        """
        Pull out the values for a given label name along a specified axis.
        
        A view is returned and the dimension is reduced by one.
        
        Parameters
        ----------
        name : scalar, string, etc.
            Label name.
        axis : integer
            The axis the label name is in.
            
        Returns
        -------
        out : {view of larry, scalar}
            A view of the larry with the dimension reduced by one is returned
            unless the larry is alread 1d, then a scalar is returned.
            
        Raises
        ------
        ValueError
            If the axis is None.
            
        Examples
        --------
        >>> y = larry([[1, 2], [3, 4]], [['r0', 'r1'], ['c0', 'c1']])
        >>> y.pull('r0', axis=0)
        label_0
            c0
            c1
        x
        array([1, 2])

        >>> import numpy as np
        >>> x = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
        >>> label = [['experiment1', 'experient2'], ['r0', 'r1'], ['c0', 'c1']]
        >>> y = larry(x, label)
        >>> y.pull('experiment1', axis=0)
        label_0
            r0
            r1
        label_1
            c0
            c1
        x
        array([[1, 2],
               [3, 4]])
                        
        """
        if axis is None:
            raise ValueError, 'axis cannot be None'
        label = [z for i, z in enumerate(self.label) if i != axis]    
        idx = self.labelindex(name, axis)
        index = [slice(None)] * self.ndim 
        index[axis] = idx
        x = self.x[index]
        if x.shape == (1,):
            return x[0]
        return type(self)(x, label)            
        
    def fill(self, fill_value):
        """
        Inplace filling of data array with specified value.
        
        Parameters
        ----------
        fill_value : {scalar, string, etc}
            Value to replace every element of the data array.
            
        Returns
        -------
        out : None
        
        Examples
        --------
        >>> y = larry([0, 1])
        >>> y.fill(9)
        >>> y
        label_0
            0
            1
        x
        array([9, 9])        
                
        """
        self.x.fill(fill_value)
        
    def keep_label(self, op, value, axis):
        """
        Keep labels (and corresponding values) that satisfy conditon.
        
        Keep labels that satify:
        
                            label[`axis`] `op` `value`,
                       
        where `op` can be '==', '>', '<', '>=', '<=', '!=', 'in', 'not in'.               
        
        Parameters
        ----------
        op : string
            Operation to perform. `op` can be '==', '>', '<', '>=', '<=',
            '!=', 'in', 'not in'.
        value : anything that can be compared to labels
            Usually the same type as the labels. So if the labels are integers
            then value is an integer.
        axis : integer
            axis over which to test condiction.
        
        Returns
        -------
        out : larry
            Returns a copy with only the labels and corresponding values that
            satisfy the specified condition.
            
        Raises
        ------
        ValueError
            If `op` is unknown or if `axis` is None.
        IndexError
            If `axis` is out of range.
            
        Examples
        --------
        >>> y = larry([1, 2, 3, 4], [['a', 'b', 'c', 'd']])
        >>> y.keep_label('<', 'c', axis=0)
        label_0
            a
            b
        x
        array([1, 2])                    

        """
        ops = ('==', '>', '<', '>=', '<=', '!=', 'in', 'not in')
        if op not in ops:
            raise ValueError, 'Unknown op'
        if axis is None:
            raise ValueError, 'axis cannot be None'    
        if axis >= self.ndim:
            raise IndexError, 'axis is out of range'   
        y = self.copy()
        cmd = '[(idx, z) for idx, z in enumerate(y.label[axis]) if z '
        cmd = cmd + op + ' value]'  
        idxlabel = eval(cmd)
        idx, label = zip(*idxlabel)
        y.label[axis] = list(label)
        index = [slice(None,None,None)] * self.ndim
        index[axis] = list(idx)
        y.x = y.x[index]
        return y
        
    def keep_x(self, op, value, vacuum=True):
        """
        Keep labels (and corresponding values) that satisfy conditon.
        
        Set x values that do not satify the condition to NaN. Then, if
        vacuum is True, rows and columns with all NaNs will be removed. If
        vacuum is True, larry must be 2d. 
        
        Note that when vacuum is True, all rows and columns with all NaNs
        (even if they already had all NaNs in the row or column before this
        function was called) will be removed.
        
        The op can be '==', '>', '<', '>=', '<=', '!=', 'in', 'not in'.
        
        Parameters
        ----------
        op : string
            Operation to perform. op can be '==', '>', '<', '>=', '<=', '!=',
            'in', 'not in'.
        value : anything that can be compared to labels
            Usually the same type as the labels. So if the labels are integers
            then value is an integer.
        vacuum : {True, False}, optional
            Vacuum larry after conditionally setting data values to NaN. False
            is the default.
        
        Returns
        -------
        out : larry
            Returns a copy with only the labels and corresponding values that
            satisfy the specified condition.
            
        Raises
        ------
        ValueError
            If op is unknown or if axis is None.
        IndexError
            If axis is out of range.        

        """
        if (vacuum == True) and (self.ndim != 2):
            raise ValueError, 'When vacuum is True, larry must be 2d'
        ops = ('==', '>', '<', '>=', '<=', '!=', 'in', 'not in')
        if op not in ops:
            raise ValueError, 'Unknown op'   
        y = self.copy()
        idx = eval('y.x ' + op + 'value')
        y.x[~idx] = np.nan
        if vacuum:
            y = y.vacuum()
        return y         
                    
    # label operations -------------------------------------------------------
        
    def maxlabel(self, axis=None):
        """
        Maximum label value along the specified axis.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis over which to find the maximum label. By default (None)
            the search for the maximum label element is performed along all
            axes.
            
        Returns
        -------
        out : scalar, string, etc.
            The maximum label element along the specified axis.
            
        Examples
        --------
        What is the maximum label value in the following larry?
        
        >>> y = larry([1, 2, 3], [['a', 'z', 'w']])
        >>> y.maxlabel()
        'z'               
        
        """
        if axis is None:
            return max([max(z) for z in self.label])
        else:
            return max([z for z in self.label[axis]])

    def minlabel(self, axis=None):
        """
        Minimum label value along the specified axis.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis over which to find the minimum label. By default (None)
            the search for the minimum label element is performed along all
            axes.
            
        Returns
        -------
        out : scalar, string, etc.
            The minimum label element along the specified axis.
            
        Examples
        --------
        What is the minimum label value in the following larry?
        
        >>> y = larry([1, 2, 3], [['a', 'z', 'w']])
        >>> y.minlabel()
        'a'               
        
        """
        if axis is None:
            return min([min(z) for z in self.label])
        else:
            return min([z for z in self.label[axis]])
        
    def labelindex(self, name, axis, exact=True):
        """
        Return index of given label element along specified axis.
        
        Parameters
        ----------
        name : str, datetime.date, int, etc.
            Name of label element to index.
        axis : int
            Axis to index along. Cannot be None.
        exact : bool, optional
            If an exact match is specfied (default) then an IndexError is
            raised if an exact match cannot be found. If exact match is False
            and if a perfect match is not found then the index of the nearest
            label is returned. Nearest is defined as the closest that is equal
            or smaller.
            
        Returns
        -------
        idx : int
            Index of given label element.

        Examples
        --------
        What column number (starting from 0) of the following 2d larry is
        labeled 'west'?
        
        >>> from la import larry
        >>> y = larry([[1, 2], [3, 4]], [['north', 'south'], ['east', 'west']])        
        >>> y.labelindex('west', axis=1)
        1        
                        
        """
        if axis >= self.ndim:
            raise IndexError, 'axis out of range'
        if axis is None:
            raise ValueError, 'axis cannot be None'            
        try:
            index = self.label[axis].index(name)
        except ValueError:
            if exact:
                raise IndexError, 'name not in label along axis %d' % axis
            else:
                idx = [i for i, z in enumerate(self.label[axis]) if z <= name]
                if len(idx) == 0:
                    raise IndexError, 'name not in label along axis %d' % axis
                index = max(idx)                        
        return index
        
    def maplabel(self, func, axis=None, copy=True):
        """
        Apply given function to each element of label along specified axis.
        
        Parameters
        ----------
        func : function
            Function to apply to each element of label.
        axis : {int, None}, optional
            Axis along which to apply the function.
        copy : bool
            Whether to return a copy (True, default) or to return a reference.
            
        Returns
        -------
        y : larry
            A copy or a reference (dending on the value of `copy`) of the
            larry with the given function applied to the specified labels.
                    
        Examples
        -------- 
        Create a larry with dates in the label:        
        
        >>> import datetime
        >>> d = datetime.date
        >>> y = larry([1, 2], [[d(2010,1,1), d(2010,1,2)]])
        
        Convert the dates in the label to integers:
        
        >>> y.maplabel(datetime.date.toordinal)
        label_0
            733773
            733774
        x
        array([1, 2])
        
        Convert the dates in the label to strings:
               
        >>> y.maplabel(str)
        label_0
            2010-01-01
            2010-01-02
        x
        array([1, 2])
                                  
        """
        if copy:
            y = self.copy()
        else:
            y = self    
        if axis is None:
            for ax in range(y.ndim):
                y.label[ax] = map(func, y.label[ax])
        else:
            y.label[axis] = map(func, y.label[axis])
        return y                    
            
    # Calc -------------------------------------------------------------------                                            

    def demean(self, axis=None):
        """
        Subtract the mean along the the specified axis.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis along which to remove the mean. The default (None) is
            to subtract the mean of the flattened larry.
        
        Examples
        --------
        >>> y = larry([1, 2, 3, 4])
        >>> y.demean()
        label_0
            0
            1
            2
            3
        x
        array([-1.5, -0.5,  0.5,  1.5])
            
        """
        # Adapted from pylab.demean
        if axis:
            ind = [slice(None)] * axis
            ind.append(np.newaxis)
            x = self.x - nanmean(self.x, axis)[ind]
        else:
            x = self.x - nanmean(self.x, axis)   
        return larry(x, self.copylabel())

    def demedian(self, axis=None):
        """
        Subtract the median along the the specified axis.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis along which to remove the median. The default (None) is
            to subtract the median of the flattened larry.
        
        Examples
        --------
        >>> y = larry([1, 2, 3, 4])
        >>> y.demedian()
        label_0
            0
            1
            2
            3
        x
        array([-1.5, -0.5,  0.5,  1.5])
            
        """
        # Adapted from pylab.demean
        if axis:
            ind = [slice(None)] * axis
            ind.append(np.newaxis)
            x = self.x - nanmedian(self.x, axis)[ind]
        else:
            x = self.x - nanmedian(self.x, axis)   
        return larry(x, self.copylabel())
        
    def zscore(self, axis=None):
        """
        Z-score along the specified axis.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis along which to take the z-score. The default (None) is
            to find the z-score of the flattened larry.
        
        Examples
        --------
        >>> y = larry([1, 2, 3])
        >>> y.zscore()
        label_0
            0
            1
            2
        x
        array([-1.22474487,  0.        ,  1.22474487])
            
        """
        y = self.demean(axis)
        if axis:
            ind = [slice(None)] * axis
            ind.append(np.newaxis)
            y.x /= nanstd(y.x, axis)[ind]
        else:
            y.x /= nanstd(y.x, axis)   
        return y
            
    def movingsum(self, window, axis=-1, norm=False):
        """Moving sum, NaNs treated as 0, optionally normalized for NaNs."""
        y = self.copy()
        y.x = movingsum(y.x, window, axis, norm)
        return y 
        
    def movingsum_forward(self, window, skip=0, axis=1, norm=False):    
        """Movingsum in the forward direction skipping skip dates"""
        self._2donly()        
        y = self.copy()
        y.x = movingsum_forward(y.x, window, skip, axis, norm)
        return y
                         
    def ranking(self, axis=0, norm='-1,1', ties=True):
        """
        Rank elements treating NaN as missing and optionally break ties.

        Parameters
        ----------
        axis : int, optional
            Axis to rank over. Default axis is 0.
        norm: str
            A string that specifies the normalization:
            '0,N-1'     Zero to N-1 ranking
            '-1,1'      Scale zero to N-1 ranking to be between -1 and 1
            'gaussian'  Rank data then scale to a Gaussian distribution
        ties: bool
            If two elements of `x` have the same value then they will be
            ranked by their order in the array (False). If `ties` is set to
            True (default), then the ranks are averaged.
            
        Returns
        -------
        y : larry
            The ranked data. The dtype of the output is always np.float even
            if the dtype of the input is int.
            
        Notes
        -----
        If there is only one non-NaN value along the given axis, then that
        value is set to the midpoint of the specified normalization method.
        For example, if the input is array([1.0, nan]), then 1.0 is set to
        zero for the '-1,1' and 'gaussian' normalizations and is set to 0.5
        (mean of 0 and 1) for the '0,N-1' normalization.
        
        For '0,N-1' normalization, note that N is x.shape[axis] even in there
        are NaNs. That ensures that when ranking along the columns of a 2d
        array, for example, the output will have the same min and max along
        all columns.
        
        """
        y = self.copy()
        y.x = ranking(y.x, axis, norm, ties)
        return y
                            
    def movingrank(self, window, axis=1):
        """Moving rank (normalized to -1 and 1) of a given window along axis.

        Normalized for missing (NaN) data.
        A data point with NaN data is returned as NaN
        If a window is all NaNs except last, this is returned as NaN
        """
        self._2donly()
        y = self.copy()
        y.x = movingrank(y.x, window, axis)
        return y
        
    def quantile(self, q):
        """Convert elements in each column to integers between 1 and q; then
        normalize to to -1, 1
        """
        self._2donly()
        y = self.copy()
        y.x = quantile(y.x, q)       
        return y
     
    def cov(self):
        """
        Covariance matrix adjusted for missing (NaN) values.
        
        Note: Only works on 2d larrys.
        
        The mean of each row is assumed to be zero. So rows are not demeaned
        and therefore the covariance is normalized by the number of columns,
        not by the number of columns minus 1.        
        
        Parameters
        ----------
        No input.
        
        Returns
        -------
        out : larry
            Returns NxN covariance matrix where N is the number of rows.

        """
        self._2donly()       
        y = self.copy()
        y.label[1] = list(y.label[0])
        y.x = covMissing(y.x)
        return y         
        
    def lastrank(self):
        """
        Rank of elements in last column, ignoring NaNs.
        
        Note: Only works on 2d larrys.
            
        Returns
        -------
        d : larry
            A 2d larry is returned.
            
        Raises
        ------
        ValueError
            If larry is not 2d.    
                    
        """
        self._2donly()
        label = self.copylabel()
        label[1] = [label[1][-1]]
        x = lastrank(self.x)
        return type(self)(x, label)
        
    def lastrank_decay(self, decay):
        """
        Exponentially decayed rank of elements in last column, ignoring NaNs.
        
        Note: Only works on 2d larrys.        

        Parameters
        ----------
        decay : scalar
            Exponential decay strength. Should not be negative.
            
        Returns
        -------
        d : larry
            A 2d larry is returned.
            
        Raises
        ------
        ValueError
            If larry is not 2d. 
        AssertionError
            If decay is less than zero.            
                    
        """
        self._2donly()
        label = self.copylabel()
        label[1] = [label[1][-1]]
        x = lastrank_decay(self.x, decay)
        return type(self)(x, label)                                                                       
        
    # Group calc -------------------------------------------------------------  
                 
    def group_ranking(self, group):
        """Group (e.g. sector) ranking along columns.
        
        The row labels of the object must be a subset of the row labels of the
        group.
        """ 
        self._2donly()
        y = self.copy()
        aligned_group_list = y._group_align(group)
        y.x = group_ranking(y.x, aligned_group_list)
        return y
            
    def group_mean(self, group):
        """Group (e.g. sector) mean along columns (zero axis).
        
        The row labels of the object must be a subset of the row labels of the
        group.
        """        
        y = self.copy() 
        aligned_group_list = y._group_align(group)
        y.x = group_mean(y.x, aligned_group_list)                                         
        return y
        
    def group_median(self, group):
        """Group (e.g. sector) median along columns (zero axis).
        
        The row labels of the object must be a subset of the row labels of the
        group.
        """ 
        y = self.copy()
        aligned_group_list = y._group_align(group)   
        y.x = group_median(y.x, aligned_group_list)
        return y
                
    def _group_align(self, group):
        """Return a row aligned group list (e.g. sector list) of values.
        
        group must have exactly one column. The row labels of the object must
        be a subset of the row labels of the group.
        """
        if not isinstance(group, larry):
            raise TypeError, 'group must be a larry'
        if group.ndim != 1:
            raise ValueError, 'group must be a 1d larry'
        if len(frozenset(self.label[0]) - frozenset(group.label[0])):
            raise IndexError, 'label is not a subset of group label'
        g = group.morph(self.label[0], 0)
        g = g.x.tolist()
        return g                                                             

    # Alignment --------------------------------------------------------------

    def morph(self, label, axis):
        """
        Reorder the elements along a specified axis.
        
        If an element in `label` does not exist in the larry, NaNs will be
        used for numeric dtype, None will be used for object dtype, and ''
        will be used for string (np.string_) dtype.
        
        Since NaNs are used to mark missing scalar data, integer input is
        converted to floats.
        
        Parameters
        ----------
        label : list
            Desired ordering of elements along specified axis.
        axis : integer
            axis along which to perform the reordering.
        
        Returns
        -------
        out : larry
            A reordered copy.       
        
        Raises
        ------
        IndexError
            axis is out of range.
            
        """
        if axis >= self.ndim:
            raise IndexError, 'axis out of range'
        label = list(label)    
        shape = list(self.shape)
        shape[axis] = len(label)
        if self.dtype == object:
            x = np.empty(shape, dtype=object)
            x.fill(None)
        elif self.dtype.type == np.string_:
            x = np.zeros(shape, dtype=self.dtype)   
        else:
            x = nans(shape)       
        idx0 = tuple(set(self.label[axis]) & set(label))
        idx1 = map(label.index, idx0)
        idx2 = map(self.label[axis].index, idx0)
        index1 = [slice(None)] * self.ndim
        index1[axis] = idx1
        index2 = [slice(None)] * self.ndim
        index2[axis] = idx2        
        x[index1] = self.x[index2]
        lab = self.copylabel()
        lab[axis] = label
        return type(self)(x, lab)       
        
    def morph_like(self, lar):
        """
        Morph to line up with the specified larry.

        If some elements in the list do not exist in the larry, NaNs will be
        used.
        
        Since NaNs are used to mark missing data, if the input larry uses
        integers then the output will uses floats.
        
        Parameters
        ---------- 
        lar : larry
            The target larry to align to.
            
        Returns
        -------
        lar : larry
            A morphed larry that is aligned with the input larry.
            

        Raises
        ------
        IndexError
            If the larrys are not of the same dimension.                              
        
        """
        if self.ndim != lar.ndim:
            raise IndexError, 'larrys must be of the same dimension.'
        y = self.copy()      
        for i in range(self.ndim):
            y = y.morph(lar.getlabel(i), axis=i)     
        return y        

    def merge(self, other, update=False):
        """
        Merge, or optionally update, a larry with a second larry.
     
        Parameters
        ----------
        other : larry
            The larry to merge or to use to update the values. It must have
            the same number of dimensions as as the existing larry.
        update : bool
            Raise a ValueError (default) if there is any overlap in the two
            larrys. An overlap is defined as a common label in both larrys
            that contains a finite value in both larrys. If `update` is True
            then the overlapped values in the current larry will be
            overwritten with the values in `other`.            
     
        Returns
        -------
        lar1 : larry
            The merged larry.
     
        """

        ndim = self.ndim
        if ndim != other.ndim:
            raise IndexError, 'larrys must be of the same dimension.'
        lar1 = self
        lar2 = other
        for ax in range(ndim):
            if lar1.label[ax] != lar2.label[ax]:
                mergelabel = set(lar1.label[ax]) | set(lar2.label[ax])
                mergelabel = sorted(mergelabel)
                lar1 = lar1.morph(mergelabel, ax)
                lar2 = lar2.morph(mergelabel, ax)
     
        # Check for overlap if requested
        if (not update) and (np.isfinite(lar1.x)*np.isfinite(lar2.x)).any():
            raise ValueError('overlapping values')
        else:
            mask = np.isfinite(lar2.x)
            lar1.x[mask] = lar2.x[mask]
     
        return lar1
        
    def squeeze(self):
        """
        Eliminate all length-1 dimensions and corresponding labels.
        
        Note that a view (reference) is returned, not a copy.
        
        Parameters
        ----------
        No input
        
        Returns
        -------
        out : larry
            Returns a view with all length-1 dimensions and corresponding
            labels removed. 
        
        """
        idx = [i for i, z in enumerate(self.shape) if z != 1]
        label = []
        for i in idx:
            label.append(self.label[i])    
        x = self.x.squeeze()
        return type(self)(x, label)

    def lag(self, nlag, axis=-1):
        """
        Lag the values along the specified axis.
        
        Parameters
        ----------
        nlag : int
            Number of periods (rows, columns, etc) to lag.
        axis : int
            The axis to lag along. The default is -1.
            
        Returns
        -------
        out : larry
            A lagged larry is returned.
            
        Raises
        ------
        ValueError
            If nlag < 0.        
        IndexError
            If the axis is None.   
                        
        """
        if axis is None:
            raise IndexError, 'axis cannot be None.'
        if nlag < 0:
            raise ValueError, 'nlag cannot be negative'
        y = self.copy()
        y.label[axis] = y.label[axis][nlag:]
        index = [slice(None)] * self.ndim
        index[axis] = slice(0,-nlag)            
        y.x = y.x[index]
        return y           

    # Shuffle ----------------------------------------------------------------
    
    def shuffle(self, axis=0):
        """
        Shuffle the data inplace along the specified axis.
        
        Unlike numpy's shuffle, this shuffle takes an axis argument. The
        ordering of the labels is not changed, only the data is shuffled.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis to shuffle the data along. Default is axis 0. If None,
            then the data will be shuffled along all axes.
            
        Returns
        -------
        out : None
            The data are shuffled inplace.        
        
        """
        if axis is None:
            for ax in range(self.ndim):
               shuffle(self.x, ax) 
        else:
            shuffle(self.x, axis)
        
    def shufflelabel(self, axis=0):
        """
        Shuffle the label inplace along the specified axis.
        
        Parameters
        ----------
        axis : {int, None}, optional
            The axis to shuffle the data along. Default is axis 0. If None,
            then the labels will be shuffled along all axes, where each
            label axis will still contain the same set of labels (labels
            from one axis will not be shuffle to another axis).
            
        Returns
        -------
        out : None
            The labels are shuffled inplace.        
        
        """
        if axis is None:
            for ax in range(self.ndim):
               np.random.shuffle(self.label[ax]) 
        else:
            np.random.shuffle(self.label[axis])
            
    # Missing ----------------------------------------------------------------

    def cut_missing(self, fraction, axis=None):
        """
        Cut rows and columns that contain too many NaNs.
        
        Parameters
        ----------
        fraction : scalar
            Usually a float that give the minimum allowable fraction of missing
            data before the row or column is cut.
        axis : {0, 1}
            Look for missing data along this axis. So for axis=0, the missing
            data along columns are checked and columns are cut. For axis=1, the
            missing data along rows are checked and rows are cut.
            
        Returns
        -------
        out : larry
            Returns a copy with rows or columns with lots of missing data cut.                
        
        Raises
        ------
        ValueError
            If larry is not 2d.        
        IndexError
            If axis is not 0 or 1.
            
        """    
        
        y = self.copy()
        ndim = y.ndim
        
        if axis is None:
            axes = range(ndim)
        elif not hasattr(axis, '__iter__'):
            axes = [axis]
        else:
            axes = axis
        # Change meaning of axes to axes not in original axes
        axes = [a for a in range(ndim) if a not in axes]    
        
        threshold = (1.0 - fraction) * np.array(y.shape)
        idxsl = []
        labsnew = []
        for ax in range(ndim):
            sl = [None]*ndim
            if ax not in axes:
                labsnew.append(y.label[ax])
                sl[ax] = slice(None)
                idxsl.append(np.arange(y.shape[ax])[sl])
                continue
            
            # Find all nans over all other axes
            xtmp = np.rollaxis(np.isfinite(y.x), ax, 0)
            count = np.ones(xtmp.shape)
            for _ in range(ndim-1):
                xtmp = xtmp.sum(-1)
                count = count.sum(-1)
    
            xtmp = xtmp > (1.0 - fraction) * count
            labsnew.append([y.label[ax][ii] for ii in np.nonzero(xtmp)[0]])
            sl[ax] = slice(None)
            idxsl.append(np.nonzero(xtmp)[0][sl])
        
        y.x = y.x[idxsl]
        y.label = labsnew
        
        if y.x.size == 0: 
            # Empty larry left over
            return larry(np.array([]))
        else:
            return y
            
    def push(self, window):
        """Fill missing values (NaNs) with most recent non-missing values if
        recent, where recent is defined by the window. The filling proceeds
        from left to right along each row.
        """
        self._2donly()
        y = self.copy()
        y.x = fillforward_partially(y.x, window)
        return y
        
    def vacuum(self, axis=None):
        """
        Remove all rows and/or columns that contain all NaNs.
                     
        Parameters
        ----------
        axis : None or int or tuple of int
            Remove columns (0) or rows (1) or both (None, default) that
            contain no finite values, for nd arrays see Notes.
            
        Returns
        -------
        out : larry
            Return a copy with rows and/or columns removed that contain all
            NaNs.  
            
        Notes
        -----
        
        For nd arrays, axis can also be a tuple. In this case, all other 
        axes are checked for nans. If the corresponding slice of the array
        contains only nans then the slice is removed.
                
        """        

        y = self.copy()
        ndim = y.ndim
        
        if axis is None:
            axes = range(ndim)
        elif not hasattr(axis, '__iter__'):
            axes = [axis]
            # Change meaning of axes to axes not in original axes
            axes = [a for a in range(ndim) if a not in axes]
        else:
            axes = axis
            # Change meaning of axes to axes not in original axes
            axes = [a for a in range(ndim) if a not in axes]
        
        idxsl = []
        labsnew = []
        for ax in range(ndim):
            sl = [None]*ndim
            if ax not in axes:
                labsnew.append(y.label[ax])
                sl[ax] = slice(None)
                idxsl.append(np.arange(y.shape[ax])[sl])
                continue
            
            # Find all nans over all other axes
            xtmp = np.rollaxis(np.isfinite(y.x), ax, 0)
            for _ in range(ndim-1):
                xtmp = xtmp.any(-1)
    
            labsnew.append([y.label[ax][ii] for ii in np.nonzero(xtmp)[0]])
            sl[ax] = slice(None)
            idxsl.append(np.nonzero(xtmp)[0][sl])
        
        y.x = y.x[idxsl]
        y.label = labsnew
        return y        
        
    def nan_replace(self, replace_with=0):
        """
        Replace NaNs.
        
        Parameters
        ----------
        replace_with : scalar
            Value to replace NaNs with.
                        
        Returns
        -------
        out : larry
            Returns a copy with NaNs replaced.     
                    
        """
        y = self.copy()
        y.x[np.isnan(y.x)] = replace_with
        return y                                     

    # Size and shape ---------------------------------------------------------

    @property
    def nx(self):
        """
        Number of finite values (not NaN, -Inf, or Inf) in the larry.
        
        Examples
        --------        
        >>> from la import nan
        >>> y = larry([1, 2, nan])
        >>> y.nx
        2
        
        """
        return np.isfinite(self.x).sum()

    @property
    def size(self):
        """
        Number of elements in the larry.
        
        Examples
        --------   
        >>> from la import nan
        >>> y = larry([1, 2, nan])
        >>> y.size
        3
        
        """
        return self.x.size

    @property
    def shape(self):
        """
        Shape of the larry as a tuple.
        
        Examples
        --------   
        >>> from la import nan
        >>> y = larry([1, 2, nan])
        >>> y.shape
        (3,)       
        """
        return self.x.shape
        
    @property
    def ndim(self):
        """Number of dimensions in the larry.
        
        Examples
        --------   
        >>> from la import nan
        >>> y = larry([1, 2, nan])
        >>> y.ndim
        1          
        """
        return self.x.ndim
        
    @property
    def dtype(self):
        """The dtype of the elements (not the labels) in the larry.
        
        Examples
        --------   
        >>> from la import nan
        >>> y = larry([1, 2, nan])
        >>> y.dtype
        dtype('float64')         
        """
        return self.x.dtype
        
    @property
    def T(self):
        """
        Returns a transposed copy of the larry.

        Examples
        --------        
        >>> y = larry([[1, 2], [3, 4]], [['a', 'b'], ['c', 'd']])
        >>> y
        label_0
            a
            b
        label_1
            c
            d
        x
        array([[1, 2],
               [3, 4]])
        >>> y.T
        label_0
            c
            d
        label_1
            a
            b
        x
        array([[1, 3],
               [2, 4]])
               
        """
        y = self.copy()
        y.x = y.x.T
        y.label = y.label[::-1]
        return y     
        
    def _2donly(self):
        "Only works on 2d arrays"
        if self.ndim != 2:
            raise ValueError, 'This function only works on 2d larrys'
            
    def flatten(self, order='C'):
        """
        Return a copy of the larry collapsed into one dimension.
        
        The elements of the label become tuples.
        
        Parameters
        ----------
        order : {'C', 'F'}, optional
            Whether to flatten in row-major order ('C', default) or
            column-major order ('F').

        Returns
        -------
        y : larry
            A copy of the input larry, collapsed to one dimension where the
            labels are tuples.
            
        See also
        --------
        unflatten : Return an unflattened copy of larry.            
            
        Examples
        --------
        >>> y = larry([[1, 2], [3, 4]], [['a', 'b'], ['c', 'd']])
        >>> y
        label_0
            a
            b
        label_1
            c
            d
        x
        array([[1, 2],
               [3, 4]])
               
        >>> y.flatten()
        label_0
            ('a', 'c')
            ('a', 'd')
            ('b', 'c')
            ('b', 'd')
        x
        array([1, 2, 3, 4])
   
        """
        y = self.copy()
        y.x = y.x.flatten(order)
        y.label = flattenlabel(y.label, order)
        return y
        
    def unflatten(self):
        """
        Return an unflattened copy of larry.
        
        The larry to be unflattened must be in flattened form: 1d and label
        elements must be tuples containing the label elements of the
        corresponding data array element. Refer to the example below to see
        what a flattened array looks like.
        
        Returns
        -------
        y : larry
                    
        See also
        --------
        flatten : Return a copy of the larry collapsed into one dimension.
        
        
        Examples
        --------
        First create a flattened larry:
        
        >>> y = larry([[1, 2], [3, 4]], [['r0', 'r1'], ['c0', 'c1']])
        >>> yf = y.flatten()
        >>> yf
        label_0
            ('r0', 'c0')
            ('r0', 'c1')
            ('r1', 'c0')
            ('r1', 'c1')
        x
        array([1, 2, 3, 4])
        
        Then unflatten it:
        
        >>> yf.unflatten()
        label_0
            r0
            r1
        label_1
            c0
            c1
        x
        array([[ 1.,  2.],
               [ 3.,  4.]])
        
        """
        
        # Check input
        if self.ndim != 1:
            raise ValueError, 'Only 1d larrys can be unflattened.'
        if not isscalar(self.x.flat[0]):
            msg = 'Only scalar dtype is currently supported.'
            raise NotImplementedError, msg 
	    
	    # Determine labels, shape, and index into array	
        labels = zip(*self.label[0])
        x, label = fromlists(self.x, labels) 
    
        return larry(x, label)
        
    # Conversion -------------------------------------------------------------         

    def totuples(self):
        """
        Convert to a flattened list of tuples.
        
        See Also
        --------
        la.fromtuples : Convert a list of tuples to a larry.
        tolist : Convert to a flattened list.
        
        Examples
        --------
        >>> y = larry([[1, 2], [3, 4]], [['a', 'b'], ['c', 'd']])
        >>> y.totuples()
        [('a', 'c', 1), ('a', 'd', 2), ('b', 'c', 3), ('b', 'd', 4)]       
        
        """
        yf = self.flatten()
        z = zip(*yf.label[0])
        z.append(yf.x.tolist())
        return zip(*z)
        
    def tolist(self):
        """
        Convert to a flattened list.
        
        See Also
        --------
        la.fromlist : Convert a flattened list to a larry.
        totuples : Convert to a flattened list of tuples.
        
        Examples
        --------
        >>> y = larry([[1, 2], [3, 4]], [['a', 'b'], ['c', 'd']])
        >>> y.tolist()
        [[1, 2, 3, 4], [('a', 'c'), ('a', 'd'), ('b', 'c'), ('b', 'd')]]       
        
        """
        yf = self.flatten()
        return [yf.x.tolist(), yf.label[0]]                                   
               
    # Copy -------------------------------------------------------------------        
          
    def copy(self):
        """
        Return a copy of a larry.

        Examples
        --------
        >>> y = larry([1, 2], [['a', 'b']])        
        >>> z = y.copy()
        >>> z
        label_0
            a
            b
        x
        array([1, 2])
            
        """
        label = deepcopy(self.label)
        x = self.x.copy()
        return type(self)(x, label)
        
    def copylabel(self):
        """
        Return a copy of a larry's label.
        
        Examples
        --------        
        >>> y = larry([1, 2], [['a', 'b']])        
        >>> label = y.copylabel()
        >>> label
        [['a', 'b']]
        
        """
        return deepcopy(self.label)
        
    def copyx(self):
        """Return a copy of a larry's data as a Numpy array.

        Examples
        --------        
        >>> y = larry([1, 2], [['a', 'b']])  
        >>> x = y.copyx()
        >>> x
        array([1, 2])
        
        """
        return self.x.copy()    
        
    # Print ------------------------------------------------------------------                
                
    def __repr__(self):

        x = []

        # Labels
        pad = '    '
        for i, label in enumerate(self.label):
            x.append('label_%d\n' % i)
            if len(label) > 10:
                x.append(pad + str(self.label[i][0]) + '\n')
                x.append(pad + str(self.label[i][1]) + '\n')
                x.append(pad + str(self.label[i][2]) + '\n')
                x.append(pad + '...\n')
                x.append(pad + str(self.label[i][-3]) + '\n')
                x.append(pad + str(self.label[i][-2]) + '\n')
                x.append(pad + str(self.label[i][-1]) + '\n')
            else:
                for l in label:
                    x.append(pad + str(l) + '\n')       
        
        # x
        x.append('x\n')
        x.append(repr(self.x))
        return ''.join(x)        
        
