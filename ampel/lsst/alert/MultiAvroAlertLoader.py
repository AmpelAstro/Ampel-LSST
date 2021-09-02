#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/MultiAvroAlertLoader.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 07.05.2021
# Last Modified Date: 25.08.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Iterable
from io import BytesIO, IOBase
from ampel.model.UnitModel import UnitModel

from ampel.base.AmpelBaseModel import AmpelBaseModel
from ampel.base.AuxUnitRegister import AuxUnitRegister
from ampel.abstract.AbsAlertLoader import AbsAlertLoader
from ampel.abstract.AbsAlertLoader import AbsAlertLoader

from fastavro import reader

class MultiAvroAlertLoader(AbsAlertLoader[BytesIO]):
	"""
	Load avro alerts from another AlertLoader.
	This is needed if there are multiple Alerts in a single avro file.
	"""

	loader: UnitModel


	def __init__(self, **kwargs) -> None:
		if 'loader' in kwargs and isinstance(kwargs['loader'], str):
			kwargs['loader'] = {"unit": kwargs['loader']}
		super().__init__(**kwargs)

		self.set_alert_source(self.loader)

	def set_alert_source(self, loader) -> None:
		self.alert_loader: AbsAlertLoader[Iterable[IOBase]] = AuxUnitRegister.new_unit( # type: ignore
			model = loader
		)
		self.next_file()

	def next_file(self) -> None:
		self.reader = reader(next(self.alert_loader))

	def __iter__(self):
		return self

	def __next__(self) -> dict:
		try:
			return next(self.reader)
		except StopIteration:
			self.next_file()
			return next(self.reader)
