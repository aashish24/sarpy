# -*- coding: utf-8 -*-
"""
The GeoData definition.
"""

import logging
from collections import OrderedDict
from xml.etree import ElementTree
from typing import List, Union, Dict

import numpy

from .base import Serializable, DEFAULT_STRICT, _StringDescriptor, _StringEnumDescriptor, \
    _SerializableDescriptor, _SerializableArrayDescriptor, \
    _ParametersDescriptor, ParametersCollection, SerializableArray, \
    _SerializableCPArrayDescriptor, SerializableCPArray, _parse_serializable
from .blocks import XYZType, LatLonRestrictionType, LatLonHAERestrictionType, \
    LatLonCornerStringType, LatLonArrayElementType

from sarpy.geometry.geocoords import geodetic_to_ecf, ecf_to_geodetic

__classification__ = "UNCLASSIFIED"
__author__ = "Thomas McCullough"


class GeoInfoType(Serializable):
    """A geographic feature."""
    _fields = ('name', 'Descriptions', 'Point', 'Line', 'Polygon')
    _required = ('name', )
    _set_as_attribute = ('name', )
    _choice = ({'required': False, 'collection': ('Point', 'Line', 'Polygon')}, )
    _collections_tags = {
        'Descriptions': {'array': False, 'child_tag': 'Desc'},
        'Line': {'array': True, 'child_tag': 'Endpoint'},
        'Polygon': {'array': True, 'child_tag': 'Vertex'}, }
    # descriptors
    name = _StringDescriptor(
        'name', _required, strict=True,
        docstring='The name.')  # type: str
    Descriptions = _ParametersDescriptor(
        'Descriptions', _collections_tags, _required, strict=DEFAULT_STRICT,
        docstring='Descriptions of the geographic feature.')  # type: ParametersCollection
    Point = _SerializableDescriptor(
        'Point', LatLonRestrictionType, _required, strict=DEFAULT_STRICT,
        docstring='A geographic point with WGS-84 coordinates.')  # type: LatLonRestrictionType
    Line = _SerializableArrayDescriptor(
        'Line', LatLonArrayElementType, _collections_tags, _required, strict=DEFAULT_STRICT, minimum_length=2,
        docstring='A geographic line (array) with WGS-84 coordinates.'
    )  # type: Union[SerializableArray, List[LatLonArrayElementType]]
    Polygon = _SerializableArrayDescriptor(
        'Polygon', LatLonArrayElementType, _collections_tags, _required, strict=DEFAULT_STRICT, minimum_length=3,
        docstring='A geographic polygon (array) with WGS-84 coordinates.'
    )  # type: Union[SerializableArray, List[LatLonArrayElementType]]

    def __init__(self, name=None, Descriptions=None, Point=None, Line=None, Polygon=None, GeoInfos=None, **kwargs):
        """

        Parameters
        ----------
        name : str
        Descriptions : ParametersCollection|dict
        Point : LatLonRestrictionType|numpy.ndarray|list|tuple
        Line : SerializableArray|List[LatLonArrayElementType]|numpy.ndarray|list|tuple
        Polygon : SerializableArray|List[LatLonArrayElementType]|numpy.ndarray|list|tuple
        GeoInfos : Dict[GeoInfoTpe]
        kwargs : dict
        """

        self.name = name
        self.Descriptions = Descriptions
        self.Point = Point
        self.Line = Line
        self.Polygon = Polygon

        self._GeoInfos = []
        if GeoInfos is None:
            pass
        elif isinstance(GeoInfos, GeoInfoType):
            self.addGeoInfo(GeoInfos)
        elif isinstance(GeoInfos, (list, tuple)):
            for el in GeoInfos:
                self.addGeoInfo(el)
        else:
            raise ('GeoInfos got unexpected type {}'.format(type(GeoInfos)))
        super(GeoInfoType, self).__init__(**kwargs)

    @property
    def FeatureType(self):  # type: () -> Union[None, str]
        """
        str: READ ONLY attribute. Identifies the feature type among. This is determined by
        returning the (first) attribute among `Point`, `Line`, `Polygon` which is populated. None will be returned if
        none of them are populated.
        """

        for attribute in self._choice[0]['collection']:
            if getattr(self, attribute) is not None:
                return attribute
        return None

    @property
    def GeoInfos(self):
        """
        List[GeoInfoType]: list of GeoInfos.
        """

        return self._GeoInfos

    def getGeoInfo(self, key):
        """
        Get GeoInfo(s) with name attribute == `key`.

        Parameters
        ----------
        key : str

        Returns
        -------
        List[GeoInfoType]
        """

        return [entry for entry in self._GeoInfos if entry.name == key]

    def addGeoInfo(self, value):
        """
        Add the given GeoInfo to the GeoInfos list.

        Parameters
        ----------
        value : GeoInfoType

        Returns
        -------
        None
        """

        if isinstance(value, ElementTree.Element):
            value = GeoInfoType.from_node(value)
        elif isinstance(value, dict):
            value = GeoInfoType.from_dict(value)

        if isinstance(value, GeoInfoType):
            self._GeoInfos.append(value)
        else:
            raise TypeError('Trying to set GeoInfo element with unexpected type {}'.format(type(value)))

    def _validate_features(self):
        if self.Line is not None and self.Line.size < 2:
            logging.error('GeoInfo has a Line feature with {} points defined.'.format(self.Line.size))
            return False
        if self.Polygon is not None and self.Polygon.size < 3:
            logging.error('GeoInfo has a Polygon feature with {} points defined.'.format(self.Polygon.size))
            return False
        return True

    def _basic_validity_check(self):
        condition = super(GeoInfoType, self)._basic_validity_check()
        return condition & self._validate_features()

    @classmethod
    def from_node(cls, node, kwargs=None):
        if kwargs is None:
            kwargs = OrderedDict()
        kwargs['GeoInfos'] = node.findall('GeoInfo')
        return super(GeoInfoType, cls).from_node(node, kwargs=kwargs)

    def to_node(self, doc, tag, parent=None, check_validity=False, strict=DEFAULT_STRICT, exclude=()):
        node = super(GeoInfoType, self).to_node(
            doc, tag, parent=parent, check_validity=check_validity, strict=strict, exclude=exclude)
        # slap on the GeoInfo children
        for entry in self._GeoInfos:
            entry.to_node(doc, tag, parent=node, strict=strict)
        return node

    def to_dict(self, check_validity=False, strict=DEFAULT_STRICT, exclude=()):
        out = super(GeoInfoType, self).to_dict(check_validity=check_validity, strict=strict, exclude=exclude)
        # slap on the GeoInfo children
        if len(self.GeoInfos) > 0:
            out['GeoInfos'] = [entry.to_dict(check_validity=check_validity, strict=strict) for entry in self._GeoInfos]
        return out


class SCPType(Serializable):
    """
    Scene Center Point (SCP) in full (global) image. This should be the the precise location.
    Note that setting one of ECF or LLH will implicitly set the other to it's corresponding matched value.
    """

    _fields = ('ECF', 'LLH')
    _required = _fields
    _ECF = None
    _LLH = None

    def __init__(self, ECF=None, LLH=None, **kwargs):
        """
        To avoid the potential of inconsistent state, ECF and LLH are not simultaneously
        used. If ECF is provided, it is used to populate LLH. Otherwise, if LLH is provided,
        then it is used the populate ECF.

        Parameters
        ----------
        ECF : XYZType|numpy.ndarray|list|tuple
        LLH : LatLonHAERestrictionType|numpy.ndarray|list|tuple
        kwargs : dict
        """

        if ECF is not None:
            self.ECF = ECF
        elif LLH is not None:
            self.LLH = LLH
        super(SCPType, self).__init__(**kwargs)

    @property
    def ECF(self):  # type: () -> XYZType
        """
        XYZType: The ECF coordinates.
        """

        return self._ECF

    @ECF.setter
    def ECF(self, value):
        if value is not None:
            self._ECF = _parse_serializable(value, 'ECF', self, XYZType)
            self._LLH = LatLonHAERestrictionType.from_array(ecf_to_geodetic(self._ECF.get_array()))

    @property
    def LLH(self):  # type: () -> LatLonHAERestrictionType
        """
        LatLonHAERestrictionType: The WGS-84 coordinates.
        """

        return self._LLH

    @LLH.setter
    def LLH(self, value):
        if value is not None:
            self._LLH = _parse_serializable(value, 'LLH', self, LatLonHAERestrictionType)
            self._ECF = XYZType.from_array(geodetic_to_ecf(self._LLH.get_array(order='LAT')))


class GeoDataType(Serializable):
    """Container specifying the image coverage area in geographic coordinates."""
    _fields = ('EarthModel', 'SCP', 'ImageCorners', 'ValidData')
    _required = ('EarthModel', 'SCP', 'ImageCorners')
    _collections_tags = {
        'ValidData': {'array': True, 'child_tag': 'Vertex'},
        'ImageCorners': {'array': True, 'child_tag': 'ICP'},
    }
    # other class variables
    _EARTH_MODEL_VALUES = ('WGS_84', )
    # descriptors
    EarthModel = _StringEnumDescriptor(
        'EarthModel', _EARTH_MODEL_VALUES, _required, strict=True, default_value='WGS_84',
        docstring='The Earth Model.'.format(_EARTH_MODEL_VALUES))  # type: str
    SCP = _SerializableDescriptor(
        'SCP', SCPType, _required, strict=DEFAULT_STRICT,
        docstring='The Scene Center Point (SCP) in full (global) image. This is the '
                  'precise location.')  # type: SCPType
    ImageCorners = _SerializableCPArrayDescriptor(
        'ImageCorners', LatLonCornerStringType, _collections_tags, _required, strict=DEFAULT_STRICT,
        docstring='The geographic image corner points array. Image corners points projected to the '
                  'ground/surface level. Points may be projected to the same height as the SCP if ground/surface '
                  'height data is not available. The corner positions are approximate geographic locations and '
                  'not intended for analytical use.')  # type: Union[SerializableCPArray, List[LatLonCornerStringType]]
    ValidData = _SerializableArrayDescriptor(
        'ValidData', LatLonArrayElementType, _collections_tags, _required,
        strict=DEFAULT_STRICT, minimum_length=3,
        docstring='The full image array includes both valid data and some zero filled pixels.'
    )  # type: Union[SerializableArray, List[LatLonArrayElementType]]

    def __init__(self, EarthModel='WGS_84', SCP=None, ImageCorners=None, ValidData=None, GeoInfos=None, **kwargs):
        """

        Parameters
        ----------
        EarthModel : str
        SCP : SCPType
        ImageCorners : SerializableCPArray|List[LatLonCornerStringType]|numpy.ndarray|list|tuple
        ValidData : SerializableArray|List[LatLonArrayElementType]|numpy.ndarray|list|tuple
        GeoInfos : List[GeoInfoType]
        kwargs : dict
        """

        self.EarthModel = EarthModel
        self.SCP = SCP
        self.ImageCorners = ImageCorners
        self.ValidData = ValidData

        self._GeoInfos = []
        if GeoInfos is None:
            pass
        elif isinstance(GeoInfos, GeoInfoType):
            self.setGeoInfo(GeoInfos)
        elif isinstance(GeoInfos, (list, tuple)):
            for el in GeoInfos:
                self.setGeoInfo(el)
        else:
            raise ('GeoInfos got unexpected type {}'.format(type(GeoInfos)))
        super(GeoDataType, self).__init__(**kwargs)

    def derive(self):
        """
        Populates any potential derived data in GeoData. Is expected to be called by
        the `SICD` parent as part of a more extensive derived data effort.

        Returns
        -------
        None
        """

        pass

    @property
    def GeoInfos(self):
        """
        List[GeoInfoType]: list of GeoInfos.
        """

        return self._GeoInfos

    def getGeoInfo(self, key):
        """
        Get the GeoInfo(s) with name attribute == `key`

        Parameters
        ----------
        key : str

        Returns
        -------
        List[GeoInfoType]
        """

        return [entry for entry in self._GeoInfos if entry.name == key]

    def setGeoInfo(self, value):
        """
        Add the given GeoInfo to the GeoInfos list.

        Parameters
        ----------
        value : GeoInfoType

        Returns
        -------
        None
        """

        if isinstance(value, ElementTree.Element):
            value = GeoInfoType.from_node(value)
        elif isinstance(value, dict):
            value = GeoInfoType.from_dict(value)

        if isinstance(value, GeoInfoType):
            self._GeoInfos.append(value)
        else:
            raise TypeError('Trying to set GeoInfo element with unexpected type {}'.format(type(value)))

    @classmethod
    def from_node(cls, node, kwargs=None):
        if kwargs is None:
            kwargs = OrderedDict()
        kwargs['GeoInfos'] = node.findall('GeoInfo')
        return super(GeoDataType, cls).from_node(node, kwargs=kwargs)

    def to_node(self, doc, tag, parent=None, check_validity=False, strict=DEFAULT_STRICT, exclude=()):
        node = super(GeoDataType, self).to_node(
            doc, tag, parent=parent, check_validity=check_validity, strict=strict, exclude=exclude)
        # slap on the GeoInfo children
        for entry in self._GeoInfos:
            entry.to_node(doc, 'GeoInfo', parent=node, strict=strict)
        return node

    def to_dict(self, check_validity=False, strict=DEFAULT_STRICT, exclude=()):
        out = super(GeoDataType, self).to_dict(check_validity=check_validity, strict=strict, exclude=exclude)
        # slap on the GeoInfo children
        if len(self.GeoInfos) > 0:
            out['GeoInfos'] = [entry.to_dict(check_validity=check_validity, strict=strict) for entry in self._GeoInfos]
        return out
