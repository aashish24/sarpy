# -*- coding: utf-8 -*-
"""
Basic building blocks for SICD standard.
"""

from .base import _get_node_value, _create_text_node, _create_new_node, Serializable, Arrayable, DEFAULT_STRICT, \
    _StringEnumDescriptor, _IntegerDescriptor, _FloatDescriptor, _FloatModularDescriptor, \
    _SerializableDescriptor

from collections import OrderedDict

import numpy
import scipy
if scipy.__version__ >= '1.0':
    from scipy.special import comb
else:
    from scipy.misc import comb


__classification__ = "UNCLASSIFIED"


##########
# Geographical coordinates


class XYZType(Serializable, Arrayable):
    """A spatial point in ECF coordinates."""
    _fields = ('X', 'Y', 'Z')
    _required = _fields
    _numeric_format = {'X': '0.4f', 'Y': '0.4f', 'Z': '0.4f'}
    # descriptors
    X = _FloatDescriptor(
        'X', _required, strict=True,
        docstring='The X attribute. Assumed to ECF or other, similar coordinates.')  # type: float
    Y = _FloatDescriptor(
        'Y', _required, strict=True,
        docstring='The Y attribute. Assumed to ECF or other, similar coordinates.')  # type: float
    Z = _FloatDescriptor(
        'Z', _required, strict=True,
        docstring='The Z attribute. Assumed to ECF or other, similar coordinates.')  # type: float

    def __init__(self, X=None, Y=None, Z=None, **kwargs):
        """
        Parameters
        ----------
        X : float
        Y : float
        Z : float
        kwargs : dict
        """

        self.X, self.Y, self.Z = X, Y, Z
        super(XYZType, self).__init__(**kwargs)

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [X, Y, Z]

        Returns
        -------
        XYZType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(X=array[0], Y=array[1], Z=array[2])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))

    def get_array(self, dtype=numpy.float64):
        """
        Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return

        Returns
        -------
        numpy.ndarray
            array of the form [X,Y,Z]
        """

        return numpy.array([self.X, self.Y, self.Z], dtype=dtype)


class LatLonType(Serializable, Arrayable):
    """A two-dimensional geographic point in WGS-84 coordinates."""
    _fields = ('Lat', 'Lon')
    _required = _fields
    _numeric_format = {'Lat': '0.8f', 'Lon': '0.8f'}
    # descriptors
    Lat = _FloatDescriptor(
        'Lat', _required, strict=True,
        docstring='The latitude attribute. Assumed to be WGS-84 coordinates.')  # type: float
    Lon = _FloatDescriptor(
        'Lon', _required, strict=True,
        docstring='The longitude attribute. Assumed to be WGS-84 coordinates.')  # type: float

    def __init__(self, Lat=None, Lon=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        kwargs : dict
        """
        self.Lat, self.Lon = Lat, Lon
        super(LatLonType, self).__init__(**kwargs)

    def get_array(self, dtype=numpy.float64, order='LAT'):
        """
        Gets an array representation of the data.

        Parameters
        ----------
        order : str
            Determines array order. 'LAT' yields [Lat, Lon], and anything else yields  [Lon, Lat].
        dtype : numpy.dtype
            data type of the return

        Returns
        -------
        numpy.ndarray
            data array with appropriate entry order
        """

        if order.upper() == 'LAT':
            return numpy.array([self.Lat, self.Lon], dtype=dtype)
        else:
            return numpy.array([self.Lon, self.Lat], dtype=dtype)

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon]

        Returns
        -------
        LatLonType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected array to be of length 2, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))

    def dms_format(self, frac_secs=False):
        """
        Get degree-minutes-seconds representation.
        Parameters
        ----------
        frac_secs : bool
            Should a fractional seconds (i.e. a float), otherwise integer

        Returns
        -------
        tuple
            of the form ((deg lat, mins lat, secs lat, N/S), (deg lon, mins lon, secs lon, E/W))
        Here degrees and minutes will be int, secs will be float.
        """

        def reduce(value):
            val = abs(value)
            deg = int(val)
            val = 60*(val - deg)
            mins = int(val)
            secs = 60*(val - mins)
            if not frac_secs:
                secs = int(secs)
            return deg, mins, secs

        X = 'S' if self.Lat < 0 else 'N'
        Y = 'W' if self.Lon < 0 else 'E'
        return reduce(self.Lat) + (X, ), reduce(self.Lon) + (Y, )


class LatLonArrayElementType(LatLonType):
    """An geographic point in an array"""
    _fields = ('Lat', 'Lon', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    _numeric_format = {'Lat': '0.8f', 'Lon': '0.8f'}
    index = _IntegerDescriptor(
        'index', _required, strict=False, docstring="The array index")  # type: int

    def __init__(self, Lat=None, Lon=None, index=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        index : int
        kwargs : dict
        """

        self.index = index
        super(LatLonArrayElementType, self).__init__(Lat=Lat, Lon=Lon, **kwargs)

    @classmethod
    def from_array(cls, array, index=0):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        index : int
            array index
        Returns
        -------
        LatLonArrayElementType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected array to be of length 2, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonRestrictionType(LatLonType):
    """A two-dimensional geographic point in WGS-84 coordinates."""
    _fields = ('Lat', 'Lon')
    _required = _fields
    _numeric_format = {'Lat': '0.8f', 'Lon': '0.8f'}
    # descriptors
    Lat = _FloatModularDescriptor(
        'Lat', 90.0, _required, strict=True,
        docstring='The latitude attribute. Assumed to be WGS-84 coordinates.')  # type: float
    Lon = _FloatModularDescriptor(
        'Lon', 180.0, _required, strict=True,
        docstring='The longitude attribute. Assumed to be WGS-84 coordinates.')  # type: float

    def __init__(self, Lat=None, Lon=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        kwargs : dict
        """

        super(LatLonRestrictionType, self).__init__(Lat=Lat, Lon=Lon, **kwargs)

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        index : int
            array index
        Returns
        -------
        LatLonRestrictionType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected array to be of length 2, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonHAEType(LatLonType):
    """A three-dimensional geographic point in WGS-84 coordinates."""
    _fields = ('Lat', 'Lon', 'HAE')
    _required = _fields
    _numeric_format = {'Lat': '0.8f', 'Lon': '0.8f', 'HAE': '0.6f'}
    # descriptors
    HAE = _FloatDescriptor(
        'HAE', _required, strict=True,
        docstring='The Height Above Ellipsoid (in meters) attribute. Assumed to be '
                  'WGS-84 coordinates.')  # type: float

    def __init__(self, Lat=None, Lon=None, HAE=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        HAE : float
        kwargs : dict
        """
        self.HAE = HAE
        super(LatLonHAEType, self).__init__(Lat=Lat, Lon=Lon, **kwargs)

    def get_array(self, dtype=numpy.float64, order='LAT'):
        """
        Gets an array representation of the data.

        Parameters
        ----------
        order : str
            Determines array order. 'LAT' yields [Lat, Lon, HAE], and anything else yields  [Lon, Lat, HAE].
        dtype : numpy.dtype
            data type of the return

        Returns
        -------
        numpy.ndarray
            data array with appropriate entry order
        """

        if order.upper() == 'LAT':
            return numpy.array([self.Lat, self.Lon, self.HAE], dtype=dtype)
        else:
            return numpy.array([self.Lon, self.Lat, self.HAE], dtype=dtype)

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]

        Returns
        -------
        LatLonHAEType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], HAE=array[2])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonHAERestrictionType(LatLonHAEType):
    _fields = ('Lat', 'Lon', 'HAE')
    _required = _fields
    """A three-dimensional geographic point in WGS-84 coordinates."""
    Lat = _FloatModularDescriptor(
        'Lat', 90.0, _required, strict=True,
        docstring='The latitude attribute. Assumed to be WGS-84 coordinates.')  # type: float
    Lon = _FloatModularDescriptor(
        'Lon', 180.0, _required, strict=True,
        docstring='The longitude attribute. Assumed to be WGS-84 coordinates.')  # type: float

    def __init__(self, Lat=None, Lon=None, HAE=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        HAE : float
        kwargs : dict
        """

        super(LatLonHAERestrictionType, self).__init__(Lat=Lat, Lon=Lon, HAE=HAE, **kwargs)

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]

        Returns
        -------
        LatLonHAERestrictionType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], HAE=array[2])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonCornerType(LatLonType):
    """A two-dimensional geographic point in WGS-84 coordinates representing a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=False, bounds=(1, 4),
        docstring='The integer index. This represents a clockwise enumeration of '
                  'the rectangle vertices wrt the frame of reference of the collector. '
                  'Should be 1-4, but 0-3 may be permissible.')  # type: int

    def __init__(self, Lat=None, Lon=None, index=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        index : int
        kwargs : dict
        """
        self.index = index
        super(LatLonCornerType, self).__init__(Lat=Lat, Lon=Lon, **kwargs)

    @classmethod
    def from_array(cls, array, index=1):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        index : int
            array index
        Returns
        -------
        LatLonCornerType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected coords to be of length 2, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonCornerStringType(LatLonType):
    """A two-dimensional geographic point in WGS-84 coordinates representing a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # other specific class variable
    _CORNER_VALUES = ('1:FRFC', '2:FRLC', '3:LRLC', '4:LRFC')
    # descriptors
    index = _StringEnumDescriptor(
        'index', _CORNER_VALUES, _required, strict=False,
        docstring="The string index.")  # type: str

    def __init__(self, Lat=None, Lon=None, index=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        index : str
        kwargs : dict
        """
        self.index = index
        super(LatLonCornerStringType, self).__init__(Lat=Lat, Lon=Lon, **kwargs)

    @classmethod
    def from_array(cls, array, index='1:FRFC'):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon]
        index : str
            array index in  ('1:FRFC', '2:FRLC', '3:LRLC', '4:LRFC')
        Returns
        -------
        LatLonCornerStringType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected array to be of length 2, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonHAECornerRestrictionType(LatLonHAERestrictionType):
    """A three-dimensional geographic point in WGS-84 coordinates. Represents a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'HAE', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=False, bounds=(1, 4),
        docstring='The integer index. This represents a clockwise enumeration of the '
                  'rectangle vertices wrt the frame of reference of the collector. '
                  'Should be 1-4, but 0-3 may be permissible.')  # type: int

    def __init__(self, Lat=None, Lon=None, HAE=None, index=None, **kwargs):
        """

        Parameters
        ----------
        Lat : float
        Lon : float
        HAE : float
        index : int
        kwargs : dict
        """
        self.index = index
        super(LatLonHAECornerRestrictionType, self).__init__(Lat=Lat, Lon=Lon, HAE=HAE, **kwargs)

    @classmethod
    def from_array(cls, array, index=1):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]
        index : int
            array index
        Returns
        -------
        LatLonHAECornerRestrictionType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], HAE=array[2], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class LatLonHAECornerStringType(LatLonHAEType):
    """A three-dimensional geographic point in WGS-84 coordinates. Represents a collection area box corner point."""
    _fields = ('Lat', 'Lon', 'HAE', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    _CORNER_VALUES = ('1:FRFC', '2:FRLC', '3:LRLC', '4:LRFC')
    # descriptors
    index = _StringEnumDescriptor(
        'index', _CORNER_VALUES, _required, strict=False, docstring="The string index.")  # type: str

    def __init__(self, Lat=None, Lon=None, HAE=None, index=None, **kwargs):
        """
        Parameters
        ----------
        Lat : float
        Lon : float
        HAE : float
        index : str
        kwargs : dict
        """
        self.index = index
        super(LatLonHAECornerStringType, self).__init__(Lat=Lat, Lon=Lon, HAE=HAE, **kwargs)

    @classmethod
    def from_array(cls, array, index='1:FRFC'):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Lat, Lon, HAE]
        index : str
            array index in ('1:FRFC', '2:FRLC', '3:LRLC', '4:LRFC')
        Returns
        -------
        LatLonHAECornerStringType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(Lat=array[0], Lon=array[1], HAE=array[2], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


#######
# Image space coordinates


class RowColType(Serializable, Arrayable):
    """A row and column attribute container - used as indices into array(s)."""
    _fields = ('Row', 'Col')
    _required = _fields
    Row = _IntegerDescriptor(
        'Row', _required, strict=True, docstring='The Row attribute.')  # type: int
    Col = _IntegerDescriptor(
        'Col', _required, strict=True, docstring='The Column attribute.')  # type: int

    def __init__(self, Row=None, Col=None, **kwargs):
        """
        Parameters
        ----------
        Row : int
        Col : int
        kwargs : dict
        """
        self.Row, self.Col = Row, Col
        super(RowColType, self).__init__(**kwargs)

    def get_array(self, dtype=numpy.int64):
        """
        Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return

        Returns
        -------
        numpy.ndarray
            array of the form [Row, Col]
        """

        return numpy.array([self.Row, self.Col], dtype=dtype)

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Row, Col]

        Returns
        -------
        RowColType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected array to be of length 2, and received {}'.format(array))
            return cls(Row=array[0], Col=array[1])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class RowColArrayElement(RowColType):
    """A array element row and column attribute container - used as indices into other array(s)."""
    # Note - in the SICD standard this type is listed as RowColvertexType. This is not a descriptive name
    # and has an inconsistency in camel case
    _fields = ('Row', 'Col', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=False, docstring='The array index attribute.')  # type: int

    def __init__(self, Row=None, Col=None, index=None, **kwargs):
        """
        Parameters
        ----------
        Row : int
        Col : int
        index : int
        kwargs : dict
        """
        self.index = index
        super(RowColArrayElement, self).__init__(Row=Row, Col=Col, **kwargs)

    @classmethod
    def from_array(cls, array, index=0):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [Row, Col]
        index : int
            the array index

        Returns
        -------
        RowColArrayElement
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 2:
                raise ValueError('Expected array to be of length 2, and received {}'.format(array))
            return cls(Row=array[0], Col=array[1], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


###############
# Polynomial Types


class Poly1DType(Serializable, Arrayable):
    """Represents a one-variable polynomial, defined by one-dimensional coefficient array."""
    __slots__ = ('_coefs', )
    _fields = ('Coefs', 'order1')
    _required = ('Coefs', )
    _numeric_format = {'Coefs': '0.10G'}

    def __init__(self, Coefs=None, **kwargs):
        """
        Parameters
        ----------
        Coefs : numpy.ndarray|tuple|list
        kwargs : dict
        """
        self._coefs = None
        self.Coefs = Coefs
        super(Poly1DType, self).__init__(**kwargs)

    @property
    def order1(self):
        """
        int: The order1 attribute [READ ONLY]  - that is, largest exponent presented in the monomial terms of coefs.
        """

        return self.Coefs.size - 1

    @property
    def Coefs(self):
        """
        numpy.ndarray: The one-dimensional polynomial coefficient array of dtype=float64. Assignment object must be a
        one-dimensional numpy.ndarray, or naively convertible to one.

        .. Note: this returns the direct coefficient array. Use the `get_array()` method to get a copy of the
            coefficient array of specified data type.
        """

        return self._coefs

    @Coefs.setter
    def Coefs(self, value):
        if value is None:
            raise ValueError('The coefficient array for a Poly1DType instance must be defined.')

        if isinstance(value, (list, tuple)):
            value = numpy.array(value, dtype=numpy.float64)

        if not isinstance(value, numpy.ndarray):
            raise ValueError(
                'Coefs for class Poly1D must be a list or numpy.ndarray. Received type {}.'.format(type(value)))
        elif len(value.shape) != 1:
            raise ValueError(
                'Coefs for class Poly1D must be one-dimensional. Received numpy.ndarray '
                'of shape {}.'.format(value.shape))
        elif not value.dtype == numpy.float64:
            value = numpy.cast[numpy.float64](value)
        self._coefs = value

    def __call__(self, x):
        """
        Evaluate the polynomial at points `x`. This passes `x` straight through to :func:`polyval` of
        :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        x : numpy.ndarray
            The point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        return numpy.polynomial.polynomial.polyval(x, self._coefs)

    def derivative(self, der_order=1, return_poly=False):
        """
        Calculate the `der_order` derivative of the polynomial.

        Parameters
        ----------
        der_order : int
            the order of the derivative
        return_poly : bool
            return a Poly1DType if True, otherwise return the coefficient array.

        Returns
        -------
        Poly1DType|numpy.ndarray
        """

        coefs = numpy.polynomial.polynomial.polyder(self._coefs, der_order)
        if return_poly:
            return Poly1DType(Coefs=coefs)
        return coefs

    def derivative_eval(self, x, der_order=1):
        """
        Evaluate the `der_order` derivative of the polynomial at points `x`. This uses the
        functionality presented in :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        x : numpy.ndarray
            The point(s) at which to evaluate.
        der_order : int
            The derivative.
        Returns
        -------
        numpy.ndarray
        """

        coefs = self.derivative(der_order=der_order, return_poly=False)
        return numpy.polynomial.polynomial.polyval(x, coefs)

    def shift(self, t_0, alpha=1, return_poly=False):
        r"""
        Transform a polynomial with respect to a affine shift in the coordinate system.
        That is, :math:`P(x) = Q(\alpha\cdot(t-t_0))`.

        Be careful to follow the convention that the transformation parameters express the *current coordinate system*
        as a shifted, **and then** scaled version of the *new coordinate system*. If the new coordinate is
        :math:`t = \beta\cdot x - t_0`, then :math:`x = (t - t_0)/\beta`, and :math:`\alpha = 1/\beta`.

        Parameters
        ----------
        t_0 : float
            the **current center coordinate** in the **new coordinate system.**
            That is, `x=0` when `t=t_0`.

        alpha : float
            the scale. That is, when `t = t0 + 1`, then `x = alpha`. **NOTE:** it is assumed that the
            coordinate system is re-centered, and **then** scaled.

        return_poly : bool
            if `True`, a Poly1DType object be returned, otherwise the coefficients array is returned.

        Returns
        -------
        Poly1DType|numpy.ndarray
        """

        if t_0 == 0:
            out = numpy.copy(self._coefs)
        else:
            out = numpy.zeros(self._coefs.shape, dtype=numpy.float64)
            siz = out.size
            for i in range(siz):
                N = numpy.arange(i, siz)
                K = N-i
                out[i] = numpy.sum(comb(N, K)*self._coefs[i:]*numpy.power(-t_0, K))
                # This is just the binomial expansion and gathering terms

        if alpha != 1:
            out *= numpy.power(alpha, numpy.arange(out.size))

        if return_poly:
            return Poly1DType(Coefs=out)
        else:
            return out

    @classmethod
    def from_array(cls, array):
        """
        Create from the coefficients array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            must be one-dimensional

        Returns
        -------
        Poly1DType
        """

        return cls(Coefs=array)

    def get_array(self, dtype=numpy.float64):
        """
        Gets *a copy* of the coefficent array of specified data type.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return

        Returns
        -------
        numpy.ndarray
            one-dimensional coefficient array
        """

        return numpy.array(self._coefs, dtype=dtype)

    @classmethod
    def from_node(cls, node, kwargs=None):
        """For XML deserialization.

        Parameters
        ----------
        node : ElementTree.Element
            dom element for serialized class instance
        kwargs : None|dict
            `None` or dictionary of previously serialized attributes. For use in inheritance call, when certain
            attributes require specific deserialization.

        Returns
        -------
        Serializable
            corresponding class instance
        """

        order1 = int(node.attrib['order1'])
        coefs = numpy.zeros((order1+1, ), dtype=numpy.float64)
        for cnode in node.findall('Coef'):
            ind = int(cnode.attrib['exponent1'])
            val = float(_get_node_value(cnode))
            coefs[ind] = val
        return cls(Coefs=coefs)

    def to_node(self, doc, tag, parent=None, strict=DEFAULT_STRICT, exclude=()):
        """For XML serialization, to a dom element.

        Parameters
        ----------
        doc : ElementTree.ElementTree
            The xml Document
        tag : None|str
            The tag name. Defaults to the value of `self._tag` and then the class name if unspecified.
        parent : None|ElementTree.Element
            The parent element. Defaults to the document root element if unspecified.
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        ElementTree.Element
            The constructed dom element, already assigned to the parent element.
        """

        if parent is None:
            parent = doc.getroot()

        node = _create_new_node(doc, tag, parent=parent)
        node.attrib['order1'] = str(self.order1)
        fmt_func = self._get_formatter('Coef')
        for i, val in enumerate(self.Coefs):
            # if val != 0.0:  # should we serialize it sparsely?
            cnode = _create_text_node(doc, 'Coef', fmt_func(val), parent=node)
            cnode.attrib['exponent1'] = str(i)
        return node

    def to_dict(self, strict=DEFAULT_STRICT, exclude=()):
        """For json serialization.

        Parameters
        ----------
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        OrderedDict
            dict representation of class instance appropriate for direct json serialization.
        """

        out = OrderedDict()
        out['Coefs'] = self.Coefs.tolist()
        return out


class Poly2DType(Serializable, Arrayable):
    """Represents a one-variable polynomial, defined by two-dimensional coefficient array."""
    __slots__ = '_coefs'
    _fields = ('Coefs', 'order1', 'order2')
    _required = ('Coefs', )
    _numeric_format = {'Coefs': '0.10G'}

    def __init__(self, Coefs=None, **kwargs):
        """
        Parameters
        ----------
        Coefs : numpy.ndarray|list|tuple
        kwargs : dict
        """
        self._coefs = None
        self.Coefs = Coefs
        super(Poly2DType, self).__init__(**kwargs)

    def __call__(self, x, y):
        """
        Evaluate a polynomial at points [`x`, `y`]. This passes `x`,`y` straight through to :func:`polyval2d` of
        :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        x : numpy.ndarray
            The first dependent variable of point(s) at which to evaluate.
        y : numpy.ndarray
            The second dependent variable of point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        return numpy.polynomial.polynomial.polyval2d(x, y, self._coefs)

    @property
    def order1(self):
        """
        int: The order1 attribute [READ ONLY]  - that is, largest exponent1 presented in the monomial terms of coefs.
        """

        return self._coefs.shape[0] - 1

    @property
    def order2(self):
        """
        int: The order1 attribute [READ ONLY]  - that is, largest exponent2 presented in the monomial terms of coefs.
        """

        return self._coefs.shape[1] - 1

    @property
    def Coefs(self):
        """
        numpy.ndarray: The two-dimensional polynomial coefficient array of dtype=float64. Assignment object must be a
        two-dimensional numpy.ndarray, or naively convertible to one.

        .. Note: this returns the direct coefficient array. Use the `get_array()` method to get a copy of the
            coefficient array of specified data type.
        """

        return self._coefs

    @Coefs.setter
    def Coefs(self, value):
        if value is None:
            raise ValueError('The coefficient array for a Poly2DType instance must be defined.')

        if isinstance(value, (list, tuple)):
            value = numpy.array(value, dtype=numpy.float64)

        if not isinstance(value, numpy.ndarray):
            raise ValueError(
                'Coefs for class Poly2D must be a list or numpy.ndarray. Received type {}.'.format(type(value)))
        elif len(value.shape) != 2:
            raise ValueError(
                'Coefs for class Poly2D must be two-dimensional. Received numpy.ndarray '
                'of shape {}.'.format(value.shape))
        elif not value.dtype == numpy.float64:
            value = numpy.cast[numpy.float64](value)
        self._coefs = value

    @classmethod
    def from_array(cls, array):
        """
        Create from the coefficients array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            must be two-dimensional.

        Returns
        -------
        Poly2DType
        """

        return cls(Coefs=array)

    def get_array(self, dtype=numpy.float64):
        """
        Gets *a copy* of the coefficent array of specified data type.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return

        Returns
        -------
        numpy.ndarray
            two-dimensional coefficient array
        """

        return numpy.array(self._coefs, dtype=dtype)

    @classmethod
    def from_node(cls, node, kwargs=None):
        """For XML deserialization.

        Parameters
        ----------
        node : ElementTree.Element
            dom element for serialized class instance
        kwargs : None|dict
            `None` or dictionary of previously serialized attributes. For use in inheritance call, when certain
            attributes require specific deserialization.

        Returns
        -------
        Serializable
            corresponding class instance
        """

        order1 = int(node.attrib['order1'])
        order2 = int(node.attrib['order2'])
        coefs = numpy.zeros((order1+1, order2+1), dtype=numpy.float64)
        for cnode in node.findall('Coef'):
            ind1 = int(cnode.attrib['exponent1'])
            ind2 = int(cnode.attrib['exponent2'])
            val = float(_get_node_value(cnode))
            coefs[ind1, ind2] = val
        return cls(Coefs=coefs)

    def to_node(self, doc, tag, parent=None, strict=DEFAULT_STRICT, exclude=()):
        """For XML serialization, to a dom element.

        Parameters
        ----------
        doc : ElementTree.ElementTree
            The xml Document
        tag : None|str
            The tag name. Defaults to the value of `self._tag` and then the class name if unspecified.
        parent : None|ElementTree.Element
            The parent element. Defaults to the document root element if unspecified.
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        ElementTree.Element
            The constructed dom element, already assigned to the parent element.
        """

        if parent is None:
            parent = doc.getroot()
        node = _create_new_node(doc, tag, parent=parent)
        node.attrib['order1'] = str(self.order1)
        node.attrib['order2'] = str(self.order2)
        fmt_func = self._get_formatter('Coefs')
        for i, val1 in enumerate(self._coefs):
            for j, val in enumerate(val1):
                # if val != 0.0:  # should we serialize it sparsely?
                cnode = _create_text_node(doc, 'Coef', fmt_func(val), parent=node)
                cnode.attrib['exponent1'] = str(i)
                cnode.attrib['exponent2'] = str(j)
        return node

    def to_dict(self, strict=DEFAULT_STRICT, exclude=()):
        """For json serialization.

        Parameters
        ----------
        strict : bool
            If `True`, then raise an Exception (of appropriate type) if the structure is not valid.
            Otherwise, log a hopefully helpful message.
        exclude : tuple
            Attribute names to exclude from this generic serialization. This allows for child classes
            to provide specific serialization for special properties, after using this super method.

        Returns
        -------
        OrderedDict
            dict representation of class instance appropriate for direct json serialization.
        """

        out = OrderedDict()
        out['Coefs'] = self.Coefs.tolist()
        return out


class XYZPolyType(Serializable, Arrayable):
    """
    Represents a single variable polynomial for each of `X`, `Y`, and `Z`. This gives position in ECF coordinates
    as a function of a single dependent variable.
    """

    _fields = ('X', 'Y', 'Z')
    _required = _fields
    # descriptors
    X = _SerializableDescriptor(
        'X', Poly1DType, _required, strict=True,
        docstring='The polynomial for the X coordinate.')  # type: Poly1DType
    Y = _SerializableDescriptor(
        'Y', Poly1DType, _required, strict=True,
        docstring='The polynomial for the Y coordinate.')  # type: Poly1DType
    Z = _SerializableDescriptor(
        'Z', Poly1DType, _required, strict=True,
        docstring='The polynomial for the Z coordinate.')  # type: Poly1DType

    def __init__(self, X=None, Y=None, Z=None, **kwargs):
        """
        Parameters
        ----------
        X : Poly1DType|numpy.ndarray|list|tuple
        Y : Poly1DType|numpy.ndarray|list|tuple
        Z : Poly1DType|numpy.ndarray|list|tuple
        kwargs : dict
        """
        self.X, self.Y, self.Z = X, Y, Z
        super(XYZPolyType, self).__init__(**kwargs)

    def __call__(self, t):
        """
        Evaluate the polynomial at points `t`. This passes `t` straight through
        to :func:`polyval` of :module:`numpy.polynomial.polynomial` for each of
        X,Y,Z components. If any of X,Y,Z is not populated, then None is returned.

        Parameters
        ----------
        t : float|int|numpy.ndarray
            The point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        return numpy.array([self.X(t), self.Y(t), self.Z(t)])

    def get_array(self, dtype=numpy.object):
        """Gets an array representation of the class instance.

        Parameters
        ----------
        dtype : numpy.dtype
            numpy data type of the return.
            If `object`, an array of Poly1DType objects is returned.
            Otherwise, an ndarray of shape (3, N) of coefficient vectors is returned.

        Returns
        -------
        numpy.ndarray
            array of the form [X,Y,Z].
        """

        if dtype in ['object', numpy.object]:
            return numpy.array([self.X, self.Y, self.Z], dtype=numpy.object)
        else:
            # return a 3 x N array of coefficients
            xv = self.X.Coefs
            yv = self.Y.Coefs
            zv = self.Z.Coefs
            length = max(xv.size, yv.size, zv.size)
            out = numpy.zeros((3, length), dtype=dtype)
            out[0, :xv.size] = xv
            out[1, :yv.size] = yv
            out[2, :zv.size] = zv
            return out

    @classmethod
    def from_array(cls, array):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [X, Y, Z]

        Returns
        -------
        XYZPolyType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(X=array[0], Y=array[1], Z=array[2])
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))

    def derivative(self, der_order=1, return_poly=False):
        """
        Calculate the `der_order` derivative of each component polynomial.

        Parameters
        ----------
        der_order : int
            the order of the derivative
        return_poly : bool
            if `True`, a XYZPolyType if returned, otherwise a list of the coefficient arrays is returned.

        Returns
        -------
        XYZPolyType|list
        """

        coefs = [
            getattr(self, attrib).derivative(der_order=der_order, return_poly=False) for attrib in ['X', 'Y', 'Z']]

        if return_poly:
            return XYZPolyType(X=coefs[0], Y=coefs[1], Z=coefs[2])
        return coefs

    def derivative_eval(self, t, der_order=1):
        """
        Evaluate the `der_order` derivative of the polynomial collection at points `x`.
        This uses the functionality presented in :module:`numpy.polynomial.polynomial`.

        Parameters
        ----------
        t : numpy.ndarray
            The point(s) at which to evaluate.
        der_order : int
            The derivative.
        Returns
        -------
        numpy.ndarray
        """

        coefs = self.derivative(der_order=der_order, return_poly=False)
        return numpy.array([numpy.polynomial.polynomial.polyval(t, entry) for entry in coefs], dtype=numpy.float64)

    def shift(self, t_0, alpha=1, return_poly=False):
        r"""
        Transform a polynomial with respect to a affine shift in the coordinate system.
        That is, :math:`P(u) = Q(\alpha\cdot(t-t_0))`.

        Be careful to follow the convention that the transformation parameters express the *current coordinate system*
        as a shifted, **and then** scaled version of the *new coordinate system*. If the new coordinate is
        :math:`t = \beta\cdot u - t_0`, then :math:`u = (t - t_0)/\beta`, and :math:`\alpha = 1/\beta`.

        Parameters
        ----------
        t_0 : float
            the **current center coordinate** in the **new coordinate system.**
            That is, `u=0` when `t=t_0`.

        alpha : float
            the scale. That is, when `t = t0 + 1`, then :math:`u = \alpha`.

        return_poly : bool
            if `True`, an XYZPolyType instance is returned, otherwise a list of the coefficient arrays is returned.

        Returns
        -------
        XYZPolyType|list
        """

        coefs = [
            getattr(self, attrib).shift(t_0, alpha=alpha, return_poly=False) for attrib in ['X', 'Y', 'Z']]

        if return_poly:
            return XYZPolyType(X=coefs[0], Y=coefs[1], Z=coefs[2])
        return coefs


class XYZPolyAttributeType(XYZPolyType):
    """
    An array element of X, Y, Z polynomials. The output of these polynomials are expected
    to be spatial variables in the ECF coordinate system.
    """
    _fields = ('X', 'Y', 'Z', 'index')
    _required = _fields
    _set_as_attribute = ('index', )
    # descriptors
    index = _IntegerDescriptor(
        'index', _required, strict=False, docstring='The array index value.')  # type: int

    def __init__(self, X=None, Y=None, Z=None, index=None, **kwargs):
        """
        Parameters
        ----------
        X : Poly1DType|numpy.ndarray|list|tuple
        Y : Poly1DType|numpy.ndarray|list|tuple
        Z : Poly1DType|numpy.ndarray|list|tuple
        index : int
        kwargs : dict
        """
        self.index = index
        super(XYZPolyAttributeType, self).__init__(X=X, Y=Y, Z=Z, **kwargs)

    @classmethod
    def from_array(cls, array, index=0):
        """
        Create from an array type entry.

        Parameters
        ----------
        array: numpy.ndarray|list|tuple
            assumed [X, Y, Z]
        index : int
            the array index

        Returns
        -------
        XYZPolyAttributeType
        """

        if isinstance(array, (numpy.ndarray, list, tuple)):
            if len(array) < 3:
                raise ValueError('Expected array to be of length 3, and received {}'.format(array))
            return cls(X=array[0], Y=array[1], Z=array[2], index=index)
        raise ValueError('Expected array to be numpy.ndarray, list, or tuple, got {}'.format(type(array)))


class GainPhasePolyType(Serializable):
    """A container for the Gain and Phase Polygon definitions."""

    _fields = ('GainPoly', 'PhasePoly')
    _required = _fields
    # descriptors
    GainPoly = _SerializableDescriptor(
        'GainPoly', Poly2DType, _required, strict=DEFAULT_STRICT,
        docstring='One-way signal gain (in dB) as a function of X-axis direction cosine (DCX) (variable 1) '
                  'and Y-axis direction cosine (DCY) (variable 2). Gain relative to gain at DCX = 0 '
                  'and DCY = 0, so constant coefficient is always 0.0.')  # type: Poly2DType
    PhasePoly = _SerializableDescriptor(
        'PhasePoly', Poly2DType, _required, strict=DEFAULT_STRICT,
        docstring='One-way signal phase (in cycles) as a function of DCX (variable 1) and '
                  'DCY (variable 2). Phase relative to phase at DCX = 0 and DCY = 0, '
                  'so constant coefficient is always 0.0.')  # type: Poly2DType

    def __init__(self, GainPoly=None, PhasePoly=None, **kwargs):
        """
        Parameters
        ----------
        GainPoly : Poly2DType|numpy.ndarray|list|tuple
        PhasePoly : Poly2DType|numpy.ndarray|list|tuple
        kwargs : dict
        """
        self.GainPoly = GainPoly
        self.PhasePoly = PhasePoly
        super(GainPhasePolyType, self).__init__(**kwargs)

    def __call__(self, x, y):
        """
        Evaluate a polynomial at points [`x`, `y`]. This passes `x`,`y` straight
        through to the call method for each component.

        Parameters
        ----------
        x : numpy.ndarray
            The first dependent variable of point(s) at which to evaluate.
        y : numpy.ndarray
            The second dependent variable of point(s) at which to evaluate.

        Returns
        -------
        numpy.ndarray
        """

        # TODO: is it remotely sensible that only one of these is defined?
        if self.GainPoly is None or self.PhasePoly is None:
            return None
        return numpy.array([self.GainPoly(x, y), self.PhasePoly(x, y)], dtype=numpy.float64)


#############
# Error Decorrelation type


class ErrorDecorrFuncType(Serializable):
    """
    This container allows parameterization of linear error decorrelation rate model.
    If `(Delta t) = |t2 - t1|`, then `CC(Delta t) = Min(1.0, Max(0.0, CC0 - DCR*(Delta t)))`.
    """

    _fields = ('CorrCoefZero', 'DecorrRate')
    _required = _fields
    _numeric_format = {'CorrCoefZero': '0.10G', 'DecorrRate': '0.10G'}
    # descriptors
    CorrCoefZero = _FloatDescriptor(
        'CorrCoefZero', _required, strict=True,
        docstring='Error correlation coefficient for zero time difference (CC0).')  # type: float
    DecorrRate = _FloatDescriptor(
        'DecorrRate', _required, strict=True,
        docstring='Error decorrelation rate. Simple linear decorrelation rate (DCR).')  # type: float

    def __init__(self, CorrCoefZero=None, DecorrRate=None, **kwargs):
        """
        Parameters
        ----------
        CorrCoefZero : float
        DecorrRate : float
        kwargs : dict
        """
        self.CorrCoefZero = CorrCoefZero
        self.DecorrRate = DecorrRate
        super(ErrorDecorrFuncType, self).__init__(**kwargs)
