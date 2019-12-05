"""
The RgAzCompType definition.
"""

import logging

import numpy
from numpy.polynomial import polynomial as numpy_poly
from numpy.linalg import norm

from .base import Serializable, DEFAULT_STRICT, _FloatDescriptor, _SerializableDescriptor
from .blocks import Poly1DType


__classification__ = "UNCLASSIFIED"


class RgAzCompType(Serializable):
    """Parameters included for a Range, Doppler image."""
    _fields = ('AzSF', 'KazPoly')
    _required = _fields
    # descriptors
    AzSF = _FloatDescriptor(
        'AzSF', _required, strict=DEFAULT_STRICT,
        docstring='Scale factor that scales image coordinate az = ycol (meters) to a delta cosine of the '
                  'Doppler Cone Angle at COA, (in 1/meter)')  # type: float
    KazPoly = _SerializableDescriptor(
        'KazPoly', Poly1DType, _required, strict=DEFAULT_STRICT,
        docstring='Polynomial function that yields azimuth spatial frequency (Kaz = Kcol) as a function of '
                  'slow time (variable 1). Slow Time (sec) -> Azimuth spatial frequency (cycles/meter). '
                  'Time relative to collection start.')  # type: Poly1DType

    def _derive_parameters(self, Grid, Timeline, SCPCOA):
        """
        Expected to be called by the SICD object.

        Parameters
        ----------
        Grid : sarpy.sicd_elements.GridType
        Timeline : sarpy.sicd_elements.TimelineType
        SCPCOA : sarpy.sicd_elements.SCPCOAType

        Returns
        -------
        None
        """

        look = -1 if SCPCOA.SideOfTrack == 'R' else 1
        az_sf = -look*numpy.sin(numpy.deg2rad(SCPCOA.DopplerConeAng))/SCPCOA.SlantRange
        if self.AzSF is None:
            self.AzSF = az_sf
        elif abs(self.AzSF - az_sf) > 1e-3:  # TODO: what is a sensible tolerance here?
            logging.warning(
                'The derived value for RgAzComp.AzSF is {}, while the current '
                'setting is {}.'.format(az_sf, self.AzSF))

        if self.KazPoly is None:
            if Grid.Row.KCtr is not None and Timeline is not None and Timeline.IPP is not None and \
                    Timeline.IPP.size == 1 and Timeline.IPP[0].IPPPoly is not None and SCPCOA.SCPTime is not None:

                st_rate_coa = numpy_poly.polyval(
                    SCPCOA.SCPTime, numpy_poly.polyder(Timeline.IPP[0].IPPPoly.Coefs, 1))

                krg_coa = Grid.Row.KCtr
                if Grid.Row is not None and Grid.Row.DeltaKCOAPoly is not None:
                    krg_coa += Grid.Row.DeltaKCOAPoly.Coefs

                # Scale factor described in SICD spec
                # note that this is scalar or two-dimensional
                delta_kaz_per_delta_v = \
                    look*krg_coa*norm(SCPCOA.ARPVel.get_array()) * \
                    numpy.sin(numpy.deg2rad(SCPCOA.DopplerConeAng))/(SCPCOA.SlantRange*st_rate_coa)
                # TODO: note that this is scalar or two-dimensional * one-dimensional - that doesn't make sense.
                #   maybe it should be .dot() and this is badly translated from matlab?
                self.KazPoly = Poly1DType(Coefs=delta_kaz_per_delta_v*Timeline.IPP[0].IPPPoly.Coefs)