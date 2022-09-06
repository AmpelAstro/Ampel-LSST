from typing import Any, Union
from ampel.model.ingest.CompilerOptions import CompilerOptions
from ampel.types import ChannelId
from ampel.log.AmpelLogger import AmpelLogger
from ampel.model.UnitModel import UnitModel
from ampel.model.ingest.T2Compute import T2Compute
from ampel.abstract.AbsProcessorTemplate import AbsProcessorTemplate
from ampel.template.AbsEasyChannelTemplate import AbsEasyChannelTemplate
from ampel.lsst.ingest.LSSTCompilerOptions import LSSTCompilerOptions


class ElasticcAlertConsumerTemplate(AbsProcessorTemplate):

    channel: ChannelId

    @staticmethod
    def _str_or_dict(arg: str | UnitModel):
        return arg if isinstance(arg, str) else arg.dict()

    #: Alert supplier
    supplier: UnitModel = UnitModel(
        unit="LSSTAlertSupplier",
        config={
            "deserialize": None,
            "loader": UnitModel(
                unit="KafkaAlertLoader",
                config={
                    "bootstrap": "public.alerts.ztf.uw.edu:9092",
                    "group_name": "ampel-test",
                    "topics": ["elasticc-test-only-3"],
                    "timeout": 30,
                },
            ),
        },
    )
    shaper: Union[str, UnitModel] = "LSSTDataPointShaper"
    combiner: str = "LSSTT1Combiner"
    compiler_opts: CompilerOptions = LSSTCompilerOptions()
    muxer: str = "LSSTMongoMuxer"

    #: T2 units to trigger when transient is updated. Dependencies of tied
    #: units will be added automatically.
    t2_compute: list[T2Compute] = []

    extra: dict = {}

    # Mandatory override
    def get_model(
        self, config: dict[str, Any], logger: AmpelLogger
    ) -> UnitModel:

        return UnitModel(
            unit="AlertConsumer",
            config=self.extra
            | AbsEasyChannelTemplate.craft_t0_processor_config(
                channel=self.channel,
                config=config,
                t2_compute=self.t2_compute,
                supplier=self.supplier.dict(),
                shaper=self._str_or_dict(self.shaper),
                combiner=self._str_or_dict(self.combiner),
                filter_dict=None,
                muxer=self.muxer,
                compiler_opts=self.compiler_opts.dict(),
            ),
        )
