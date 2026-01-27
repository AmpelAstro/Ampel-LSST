from collections.abc import Sequence
from typing import Annotated

from annotated_types import MinLen

from ampel.lsst.ingest.LSSTCompilerOptions import (
    CompilerOptions,
    LSSTCompilerOptions,
)
from ampel.model.UnitModel import UnitModel

from .MultiChannelAlertConsumerTemplate import (
    DirectiveTemplate,
    MultiChannelAlertConsumerTemplate,
)


class LSSTDirecitiveTemplate(DirectiveTemplate):
    muxer: None | str | UnitModel = "LSSTMongoMuxer"
    combiner: str | UnitModel = "LSSTT1Combiner"


class LSSTAlertConsumerTemplate(MultiChannelAlertConsumerTemplate):
    supplier: str | UnitModel = UnitModel(
        unit="LSSTAlertSupplier", config={"deserialize": None}
    )
    shaper: str | UnitModel = "LSSTDataPointShaper"
    compiler_opts: CompilerOptions = LSSTCompilerOptions()
    directives: Annotated[Sequence[LSSTDirecitiveTemplate], MinLen(1)]
