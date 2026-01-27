from collections.abc import Sequence
from typing import Annotated, Any, overload

from annotated_types import MinLen
from pydantic import model_validator

from ampel.abstract.AbsConfigMorpher import AbsConfigMorpher
from ampel.base.AmpelBaseModel import AmpelBaseModel
from ampel.log.AmpelLogger import AmpelLogger
from ampel.model.ingest.CompilerOptions import CompilerOptions
from ampel.model.ingest.FilterModel import FilterModel
from ampel.model.ingest.T2Compute import T2Compute
from ampel.model.UnitModel import UnitModel
from ampel.template.AbsEasyChannelTemplate import AbsEasyChannelTemplate
from ampel.types import ChannelId


class DirectiveTemplate(AmpelBaseModel):
    #: Channel tag for any documents created
    channel: ChannelId
    #: Alert filter. None disables filtering
    filter: None | str | FilterModel
    #: Augment alerts with external content before ingestion
    muxer: None | str | UnitModel
    # Combine datapoints into states
    combiner: str | UnitModel
    #: T2 units to trigger when stock is updated. Dependencies of tied
    #: units will be added automatically.
    t2_compute: list[T2Compute] = []


class MultiChannelAlertConsumerTemplate(AbsConfigMorpher):
    """Configure an AlertConsumer (or subclass) for one or more channels"""

    #: Alert supplier unit
    supplier: str | UnitModel
    #: Optional override for alert loader
    loader: None | str | UnitModel
    #: Alert shaper
    shaper: str | UnitModel
    #: Document creation options
    compiler_opts: CompilerOptions
    #: Directives for each channel
    directives: Annotated[Sequence[DirectiveTemplate], MinLen(1)]

    #: Unit to synthesize config for
    unit: str = "AlertConsumer"

    #: Arbitrary extra fields to add to the final config
    extra: dict = {}

    # target may be UnitModel or JobTaskModel
    model_config = {
        "extra": "allow",
    }

    # template may be JobTaskModel.template, str, or list[str]. Let caller take care of it.
    template: Any = None
    # ensure that JobTaksModel doesn't try to set its own config
    config: None = None

    @model_validator(mode="before")
    @classmethod
    def _migrate_single_directive(cls, v: Any) -> Any:
        if isinstance(v, dict):
            directive = {k: v.pop(k) for k in DirectiveTemplate.model_fields if k in v}
            return {"directives": [directive], **v}
        return v

    def morph(
        self,
        ampel_config: dict[str, Any],
        logger: AmpelLogger,  # noqa: ARG002
    ) -> dict[str, Any]:
        # Build complete AlertConsumer config around each channel
        alertconsumer_configs = [
            AbsEasyChannelTemplate.craft_t0_processor_config(
                channel=directive.channel,
                alconf=ampel_config,
                t2_compute=directive.t2_compute,
                supplier=self._get_supplier(),
                shaper=self._config_as_dict(self.shaper),
                combiner=self._config_as_dict(directive.combiner),
                filter_dict=self._config_as_dict(directive.filter),
                muxer=self._config_as_dict(directive.muxer),
                compiler_opts=self.compiler_opts.dict(),
            )
            for directive in self.directives
        ]
        # Flatten into single AlertConsumer with multiple directives
        flattened_config = alertconsumer_configs[0] | {
            "directives": [config["directives"][0] for config in alertconsumer_configs]
        }

        return (
            UnitModel(
                unit=self.unit,
                config=self.extra | flattened_config,
            ).dict(exclude_unset=True)
            | (self.model_extra or {})
            | {"template": self.template}
        )

    @overload
    @staticmethod
    def _config_as_dict(arg: None) -> None: ...

    @overload
    @staticmethod
    def _config_as_dict(arg: str | UnitModel) -> dict[str, Any]: ...

    @staticmethod
    def _config_as_dict(arg: None | str | UnitModel) -> None | dict[str, Any]:
        if arg is None:
            return None
        return (arg if isinstance(arg, UnitModel) else UnitModel(unit=arg)).dict(
            exclude_unset=True
        )

    def _get_supplier(self) -> dict[str, Any]:
        unit_dict = self._config_as_dict(self.supplier)
        if self.loader:
            unit_dict["config"] = unit_dict.get("config", {}) | {
                "loader": self._config_as_dict(self.loader)
            }
        return unit_dict
