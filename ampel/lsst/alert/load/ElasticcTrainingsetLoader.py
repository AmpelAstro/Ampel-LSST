#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/load/ElasticcTrainingsetLoader.py
# License           : BSD-3-Clause
# Author            : J Nordin <jno@physik.hu-berlin.de>
# Date              : 09.06.2022
# Last Modified Date: 09.06.2022
# Last Modified By  : J Nordin <jno@physik.hu-berlin.de>

import codecs
import sncosmo
from typing import IO, Optional, Sequence, Dict
from ampel.log.AmpelLogger import AmpelLogger
from ampel.abstract.AbsAlertLoader import AbsAlertLoader


# These can vary for different models, and more might be needed.
meta_dcast = {
 'SNID': codecs.decode,
 'IAUC': codecs.decode,
 'FAKE': int,
 'RA': float,
 'DEC': float,
 'PIXSIZE': float,
 'NXPIX': int,
 'NYPIX': int,
 'SNTYPE': int,
 'NOBS': int,
 'PTROBS_MIN': int,
 'PTROBS_MAX': int,
 'MWEBV': float,
 'MWEBV_ERR': float,
 'REDSHIFT_HELIO': float,
 'REDSHIFT_HELIO_ERR': float,
 'REDSHIFT_FINAL': float,
 'REDSHIFT_FINAL_ERR': float,
 'VPEC': float,
 'VPEC_ERR': float,
 'HOSTGAL_NMATCH': int,
 'HOSTGAL_NMATCH2': int,
 'HOSTGAL_OBJID': int,
 'HOSTGAL_FLAG': int,
 'HOSTGAL_PHOTOZ': float,
 'HOSTGAL_PHOTOZ_ERR': float,
 'HOSTGAL_SPECZ': float,
 'HOSTGAL_SPECZ_ERR': float,
 'HOSTGAL_RA': float,
 'HOSTGAL_DEC': float,
 'HOSTGAL_SNSEP': float,
 'HOSTGAL_DDLR': float,
 'HOSTGAL_CONFUSION': float,
 'HOSTGAL_LOGMASS': float,
 'HOSTGAL_LOGMASS_ERR': float,
 'HOSTGAL_LOGSFR': float,
 'HOSTGAL_LOGSFR_ERR': float,
 'HOSTGAL_LOGsSFR': float,
 'HOSTGAL_LOGsSFR_ERR': float,
 'HOSTGAL_COLOR': float,
 'HOSTGAL_COLOR_ERR': float,
 'HOSTGAL_ELLIPTICITY': float,
 'HOSTGAL_OBJID2': int,
 'HOSTGAL_SQRADIUS': float,
 'HOSTGAL_OBJID_UNIQUE': int,
 'HOSTGAL_ZPHOT_Q000': float,
 'HOSTGAL_ZPHOT_Q010': float,
 'HOSTGAL_ZPHOT_Q020': float,
 'HOSTGAL_ZPHOT_Q030': float,
 'HOSTGAL_ZPHOT_Q040': float,
 'HOSTGAL_ZPHOT_Q050': float,
 'HOSTGAL_ZPHOT_Q060': float,
 'HOSTGAL_ZPHOT_Q070': float,
 'HOSTGAL_ZPHOT_Q080': float,
 'HOSTGAL_ZPHOT_Q090': float,
 'HOSTGAL_ZPHOT_Q100': float,
 'HOSTGAL_MAG_u': float,
 'HOSTGAL_MAG_g': float,
 'HOSTGAL_MAG_r': float,
 'HOSTGAL_MAG_i': float,
 'HOSTGAL_MAG_z': float,
 'HOSTGAL_MAG_Y': float,
 'HOSTGAL_MAGERR_u': float,
 'HOSTGAL_MAGERR_g': float,
 'HOSTGAL_MAGERR_r': float,
 'HOSTGAL_MAGERR_i': float,
 'HOSTGAL_MAGERR_z': float,
 'HOSTGAL_MAGERR_Y': float,
 'HOSTGAL2_OBJID': int,
 'HOSTGAL2_FLAG': int,
 'HOSTGAL2_PHOTOZ': float,
 'HOSTGAL2_PHOTOZ_ERR': float,
 'HOSTGAL2_SPECZ': float,
 'HOSTGAL2_SPECZ_ERR': float,
 'HOSTGAL2_RA': float,
 'HOSTGAL2_DEC': float,
 'HOSTGAL2_SNSEP': float,
 'HOSTGAL2_DDLR': float,
 'HOSTGAL2_LOGMASS': float,
 'HOSTGAL2_LOGMASS_ERR': float,
 'HOSTGAL2_LOGSFR': float,
 'HOSTGAL2_LOGSFR_ERR': float,
 'HOSTGAL2_LOGsSFR': float,
 'HOSTGAL2_LOGsSFR_ERR': float,
 'HOSTGAL2_COLOR': float,
 'HOSTGAL2_COLOR_ERR': float,
 'HOSTGAL2_ELLIPTICITY': float,
 'HOSTGAL2_OBJID2': int,
 'HOSTGAL2_SQRADIUS': float,
 'HOSTGAL2_OBJID_UNIQUE': int,
 'HOSTGAL2_MAG_u': float,
 'HOSTGAL2_MAG_g': float,
 'HOSTGAL2_MAG_r': float,
 'HOSTGAL2_MAG_i': float,
 'HOSTGAL2_MAG_z': float,
 'HOSTGAL2_MAG_Y': float,
 'HOSTGAL2_MAGERR_u': float,
 'HOSTGAL2_MAGERR_g': float,
 'HOSTGAL2_MAGERR_r': float,
 'HOSTGAL2_MAGERR_i': float,
 'HOSTGAL2_MAGERR_z': float,
 'HOSTGAL2_MAGERR_Y': float,
 'HOSTGAL2_ZPHOT_Q000': float,
 'HOSTGAL2_ZPHOT_Q010': float,
 'HOSTGAL2_ZPHOT_Q020': float,
 'HOSTGAL2_ZPHOT_Q030': float,
 'HOSTGAL2_ZPHOT_Q040': float,
 'HOSTGAL2_ZPHOT_Q050': float,
 'HOSTGAL2_ZPHOT_Q060': float,
 'HOSTGAL2_ZPHOT_Q070': float,
 'HOSTGAL2_ZPHOT_Q080': float,
 'HOSTGAL2_ZPHOT_Q090': float,
 'HOSTGAL2_ZPHOT_Q100': float,
 'HOSTGAL_SB_FLUXCAL_u': float,
 'HOSTGAL_SB_FLUXCAL_g': float,
 'HOSTGAL_SB_FLUXCAL_r': float,
 'HOSTGAL_SB_FLUXCAL_i': float,
 'HOSTGAL_SB_FLUXCAL_z': float,
 'HOSTGAL_SB_FLUXCAL_Y': float,
 'PEAKMJD': float,
 'MJD_TRIGGER': float,
 'MJD_DETECT_FIRST': float,
 'MJD_DETECT_LAST': float,
 'SEARCH_TYPE': int,
 'SIM_MODEL_NAME': codecs.decode,
 'SIM_MODEL_INDEX': int,
 'SIM_TYPE_INDEX': int,
 'SIM_TYPE_NAME': codecs.decode,
 'SIM_TEMPLATE_INDEX': int,
 'SIM_LIBID': int,
 'SIM_NGEN_LIBID': int,
 'SIM_NOBS_UNDEFINED': int,
 'SIM_SEARCHEFF_MASK': int,
 'SIM_REDSHIFT_HELIO': float,
 'SIM_REDSHIFT_CMB': float,
 'SIM_REDSHIFT_HOST': float,
 'SIM_REDSHIFT_FLAG': int,
 'SIM_VPEC': float,
 'SIM_HOSTLIB_GALID': int,
 'SIM_HOSTLIB(LOGMASS_TRUE)': float,
 'SIM_HOSTLIB(LOG_SFR)': float,
 'SIM_DLMU': float,
 'SIM_LENSDMU': float,
 'SIM_RA': float,
 'SIM_DEC': float,
 'SIM_MWEBV': float,
 'SIM_PEAKMJD': float,
 'SIM_MAGSMEAR_COH': float,
 'SIM_AV': float,
 'SIM_RV': float,
 'SIM_SALT2x0': float,
 'SIM_SALT2x1': float,
 'SIM_SALT2c': float,
 'SIM_SALT2mB': float,
 'SIM_SALT2alpha': float,
 'SIM_SALT2beta': float,
 'SIM_SALT2gammaDM': float,
 'SIM_PEAKMAG_u': float,
 'SIM_PEAKMAG_g': float,
 'SIM_PEAKMAG_r': float,
 'SIM_PEAKMAG_i': float,
 'SIM_PEAKMAG_z': float,
 'SIM_PEAKMAG_Y': float,
 'SIM_EXPOSURE_u': float,
 'SIM_EXPOSURE_g': float,
 'SIM_EXPOSURE_r': float,
 'SIM_EXPOSURE_i': float,
 'SIM_EXPOSURE_z': float,
 'SIM_EXPOSURE_Y': float,
 'SIM_GALFRAC_u': float,
 'SIM_GALFRAC_g': float,
 'SIM_GALFRAC_r': float,
 'SIM_GALFRAC_i': float,
 'SIM_GALFRAC_z': float,
 'SIM_GALFRAC_Y': float,
 'SIM_SUBSAMPLE_INDEX': int
}


class ElasticcLcIterator:
    """
    Iterator returns the next alert which would be generated from a lightcurve.

    lightcurve is assumed to be an ELAsTICC AstropyTable where 'SIM_MAGOBS'
    determines whether an alert was generated (otherwise 99)

    """

    def __init__(self, lightcurve, startindex=0, cut_col = [], decode_col=[], change_col={}):
        self.lightcurve = lightcurve
        self.lightcurve.sort('MJD')    # Prob already done, but critical for usage.
        self.lightcurve.remove_columns(cut_col)
        for dcol in decode_col:
            # self.lightcurve[dcol] = self.lightcurve[dcol].astype(str)
            # Reading fits like this also cause trailing whitespaces, so instead
            self.lightcurve[dcol] = [str(s).rstrip() for s in self.lightcurve[dcol]]
        for oldname, newname in change_col.items():
            self.lightcurve.rename_column(oldname, newname)

        self.lightcurve.meta = {
                k: meta_dcast[k](v)
                   if (k in meta_dcast and v is not None)
                   else v for k, v in self.lightcurve.meta.items()
            }

        # Determine index of first "detection"
        for i, mag in enumerate(self.lightcurve['SIM_MAGOBS']):
            if mag<99 and i>=startindex:
                break
        self.index = i

    def __iter__(self):
        return self

    def __next__(self):
        if self.index==len(self.lightcurve):
            raise StopIteration

        lc = self.lightcurve[0:self.index+1]
        # Determine next viable index
        self.index += 1
        while( self.index<len(self.lightcurve) and self.lightcurve['SIM_MAGOBS'][self.index]==99.0):
            self.index += 1
        return lc


class ElasticcTrainingsetLoader(AbsAlertLoader[IO[bytes]]):
    """
    Load alerts from the ELAsTICC training set lightcurves.
    These are assumed to be distributed in "SNANA" fits format:
    - Simulated based on models.
    - Two connected files ({file_path}_HEAD.FITS.gz, {file_path}_PHOT.FITS.gz)
    - A PHOT file contains *full* lightcurves of transients.
    - Each *lightcurve* will be broken into individual alerts.


	"""

    skip_transients: int = 0
    file_path: str
    logger: Optional[AmpelLogger]

    #
    cut_col: Sequence[str] = ['CCDNUM','FIELD', 'PHOTFLAG', 'PHOTPROB', 'PSF_SIG2','PSF_RATIO', 'SKY_SIG_T', 'XPIX', 'YPIX', 'SIM_FLUXCAL_HOSTERR']
    decode_col: Sequence[str] = ['BAND']
    change_col: Dict[str,str] = {'MJD':'midPointTai', 'BAND':'filterName', 'FLUXCAL':'psFlux', 'FLUXCALERR':'psFluxErr'}

    def __init__(self, **kwargs) -> None:

        if kwargs.get('logger') is None:
            kwargs['logger'] = AmpelLogger.get_logger()
        super().__init__(**kwargs)
        self.lightcurves = iter( sncosmo.read_snana_fits(self.file_path+'_HEAD.FITS.gz',
                                                   self.file_path+'_PHOT.FITS.gz') )

        if self.skip_transients != 0:
            count = 0
            for lc in self.lightcurves:
                count += 1
                if count >= self.skip_transients:
                    break

        self.next_lightcurve()


    def next_lightcurve(self) -> None:
        self.lciter = ElasticcLcIterator( next(self.lightcurves),
                cut_col=self.cut_col, change_col=self.change_col,
                decode_col=self.decode_col)


    def __iter__(self):
        return self


    def __next__(self) -> IO[bytes]:

        try:
            return next(self.lciter)
        except StopIteration:
            self.next_lightcurve()
            return next(self.lciter)
