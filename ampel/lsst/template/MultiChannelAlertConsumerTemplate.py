from collections.abc import Callable, Sequence
from functools import cache
from importlib import import_module
from typing import Annotated, Any, overload

from annotated_types import MinLen
from pydantic import model_validator

from ampel.abstract.AbsConfigMorpher import AbsConfigMorpher
from ampel.abstract.AbsTiedT2Unit import AbsTiedT2Unit
from ampel.base.AmpelBaseModel import AmpelBaseModel
from ampel.log.AmpelLogger import AmpelLogger
from ampel.model.ingest.CompilerOptions import CompilerOptions
from ampel.model.ingest.FilterModel import FilterModel
from ampel.model.ingest.T2Compute import T2Compute
from ampel.model.UnitModel import UnitModel
from ampel.template.AbsEasyChannelTemplate import AbsEasyChannelTemplate
from ampel.types import ChannelId, JDict


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

    @staticmethod
    def _as_unitmodel(t2_unit_model: T2Compute) -> UnitModel:
        return UnitModel(
            **{
                k: v
                for k, v in t2_unit_model.dict().items()
                if k in UnitModel.get_model_keys()
            }
        )

    @classmethod
    def _inject_depedencies(
        cls,
        t2_compute: Sequence[T2Compute],
        get_default_dependencies: Callable[[str], list[JDict]],
        get_bases: Callable[[str], set[str]],
    ) -> list[T2Compute]:
        """Inject dependencies of tied T2 units into t2_compute list"""

        all_t2_units: list[T2Compute] = []
        for el in t2_compute:
            if "AbsTiedT2Unit" in get_bases(el.unit):
                t2_deps = (
                    (el.config if isinstance(el.config, dict) else {})
                    | (el.override or {})
                ).get("t2_dependency") or get_default_dependencies(el.unit)
                for t2_dep in t2_deps:
                    dependency_config: UnitModel[str] = UnitModel(
                        **{
                            k: v
                            for k, v in t2_dep.items()
                            if k in UnitModel.get_model_keys()
                        }
                    )
                    if any(
                        cls._as_unitmodel(unit) == dependency_config
                        for unit in all_t2_units
                    ):
                        # dependency already added; do nothing
                        continue
                    args = dependency_config.model_dump(exclude_unset=True)
                    # if link_override specified for point T2 dependency, request ingest filter
                    if "link_override" in t2_dep and "AbsPointT2Unit" in get_bases(
                        dependency_config.unit
                    ):
                        args["ingest"] = t2_dep["link_override"]
                    # add dependency
                    all_t2_units.append(T2Compute(**args))
            all_t2_units.append(el)
        return all_t2_units

    def morph(
        self,
        ampel_config: dict[str, Any],
        logger: AmpelLogger,  # noqa: ARG002
    ) -> dict[str, Any]:
        @cache
        def get_default_dependencies(unit: str) -> list[JDict]:
            klass: type[AbsTiedT2Unit] = getattr(
                import_module(ampel_config["unit"][unit]["fqn"]), unit
            )
            return [dep.dict() for dep in klass.t2_dependency]

        @cache
        def get_bases(unit: str) -> set[str]:
            return set(ampel_config["unit"][unit]["base"])

        # Build complete AlertConsumer config around each channel
        alertconsumer_configs = [
            AbsEasyChannelTemplate.craft_t0_processor_config(
                channel=directive.channel,
                alconf=ampel_config,
                # NB: craft_t0_processor_config validates t2_compute entries
                t2_compute=self._inject_depedencies(
                    directive.t2_compute,
                    get_default_dependencies,
                    get_bases,
                ),
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
