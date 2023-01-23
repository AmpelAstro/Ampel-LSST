#!/usr/bin/env python


import logging
from io import BytesIO, StringIO

import gzip
import fastavro

from ampel.alert.load.DirAlertLoader import DirAlertLoader

log = logging.getLogger(__name__)

# schema extracted from https://github.com/LSSTDESC/elasticc/blob/c47fbd301b87f915c77ac0046d7845c68c306444/alert_schema/elasticc.v0_9.alert.avsc
DEFAULT_SCHEMA = {
    "type": "record",
    "doc": "sample avro alert schema v4.1",
    "name": "elasticc.v0_9.alert",
    "fields": [
        {"doc": "unique alert identifer", "name": "alertId", "type": "long"},
        {
            "name": "diaSource",
            "type": {
                "type": "record",
                "name": "elasticc.v0_9.diaSource",
                "fields": [
                    {"name": "diaSourceId", "type": "long"},
                    {"name": "ccdVisitId", "type": "long"},
                    {
                        "default": None,
                        "name": "diaObjectId",
                        "type": ["null", "long"],
                    },
                    {
                        "default": None,
                        "name": "parentDiaSourceId",
                        "type": ["null", "long"],
                    },
                    {"name": "midPointTai", "type": "double"},
                    {"name": "filterName", "type": "string"},
                    {"name": "ra", "type": "double"},
                    {"name": "decl", "type": "double"},
                    {"name": "psFlux", "type": "float"},
                    {"name": "psFluxErr", "type": "float"},
                    {"name": "snr", "type": "float"},
                    {
                        "default": None,
                        "name": "nobs",
                        "type": ["null", "float"],
                    },
                ],
            },
        },
        {
            "default": None,
            "name": "prvDiaSources",
            "type": [
                "null",
                {"type": "array", "items": "elasticc.v0_9.diaSource"},
            ],
        },
        {
            "default": None,
            "name": "prvDiaForcedSources",
            "type": [
                "null",
                {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "elasticc.v0_9.diaForcedSource",
                        "fields": [
                            {"name": "diaForcedSourceId", "type": "long"},
                            {"name": "ccdVisitId", "type": "long"},
                            {"name": "diaObjectId", "type": "long"},
                            {"name": "midPointTai", "type": "double"},
                            {"name": "filterName", "type": "string"},
                            {"name": "psFlux", "type": "float"},
                            {"name": "psFluxErr", "type": "float"},
                            {"name": "totFlux", "type": "float"},
                            {"name": "totFluxErr", "type": "float"},
                        ],
                    },
                },
            ],
        },
        {
            "default": None,
            "name": "prvDiaNondetectionLimits",
            "type": [
                "null",
                {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "elasticc.v0_9.diaNondetectionLimit",
                        "fields": [
                            {"name": "ccdVisitId", "type": "long"},
                            {"name": "midPointTai", "type": "double"},
                            {"name": "filterName", "type": "string"},
                            {"name": "diaNoise", "type": "float"},
                        ],
                    },
                },
            ],
        },
        {
            "default": None,
            "name": "diaObject",
            "type": [
                "null",
                {
                    "type": "record",
                    "name": "elasticc.v0_9.diaObject",
                    "fields": [
                        {"name": "diaObjectId", "type": "long"},
                        {
                            "doc": "diaObject provenance",
                            "name": "simVersion",
                            "type": ["null", "string"],
                        },
                        {"name": "ra", "type": "double"},
                        {"name": "decl", "type": "double"},
                        {
                            "default": None,
                            "name": "mwebv",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "mwebv_err",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "z_final",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "z_final_err",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_ellipticity",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_sqradius",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zspec",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zspec_err",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_err",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q000",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q010",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q020",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q030",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q040",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q050",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q060",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q070",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q080",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q090",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_q100",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_zphot_p50",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_mag_u",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_mag_g",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_mag_r",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_mag_i",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_mag_z",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_mag_Y",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_ra",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_dec",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_snsep",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_magerr_u",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_magerr_g",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_magerr_r",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_magerr_i",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_magerr_z",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal_magerr_Y",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_ellipticity",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_sqradius",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zspec",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zspec_err",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_err",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q000",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q010",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q020",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q030",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q040",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q050",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q060",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q070",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q080",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q090",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_q100",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_zphot_p50",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_mag_u",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_mag_g",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_mag_r",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_mag_i",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_mag_z",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_mag_Y",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_ra",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_dec",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_snsep",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_magerr_u",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_magerr_g",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_magerr_r",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_magerr_i",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_magerr_z",
                            "type": ["null", "float"],
                        },
                        {
                            "default": None,
                            "name": "hostgal2_magerr_Y",
                            "type": ["null", "float"],
                        },
                    ],
                },
            ],
        },
        {
            "default": None,
            "name": "cutoutDifference",
            "type": ["null", "bytes"],
        },
        {"default": None, "name": "cutoutTemplate", "type": ["null", "bytes"]},
    ],
}


class ElasticcDirAlertLoader(DirAlertLoader):
    """
    Load alerts from a Dir, but with a schemaless format. Using schema as in
    KafkaAlertLoader.

    """

    #: Message schema
    avro_schema: dict = DEFAULT_SCHEMA

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alert_schema: dict = fastavro.schema.parse_schema(self.avro_schema)

    def __next__(self) -> StringIO | BytesIO:

        if not self.files:
            self.build_file_list()
            self.iter_files = iter(self.files)

        if (fpath := next(self.iter_files, None)) is None:
            raise StopIteration

        if self.logger.verbose > 1:
            self.logger.debug("Loading " + fpath)

        with gzip.open(fpath, self.open_mode) as alert_file:

            alert = fastavro.schemaless_reader(alert_file, self.alert_schema)
            # Assuming one alert per file
            return alert
