
from ampel.model.UnitModel import UnitModel
from ampel.template.EasyAlertConsumerTemplate import EasyAlertConsumerTemplate
from ampel.lsst.ingest.LSSTCompilerOptions import LSSTCompilerOptions


class LSSTAlertConsumerTemplate(EasyAlertConsumerTemplate):

    supplier = UnitModel(
        unit="LSSTAlertSupplier", config={"deserialize": None}
    )
    shaper = "LSSTDataPointShaper"
    combiner = "LSSTT1Combiner"
    compiler_opts = LSSTCompilerOptions()
    muxer = "LSSTMongoMuxer"
