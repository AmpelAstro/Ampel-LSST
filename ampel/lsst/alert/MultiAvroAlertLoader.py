#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/MultiAvroAlertLoader.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 07.05.2021
# Last Modified Date: 12.05.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Iterable
from io import BytesIO, IOBase
from ampel.base.AmpelBaseModel import AmpelBaseModel
from fastavro import reader

class MultiAvroAlertLoader(AmpelBaseModel):
	"""
	Load avro alerts from another AlertLoader.
	This is needed if there are multiple Alerts in a single avro file.
	"""

	alert_loader: Iterable[IOBase]


	def __init__(self, **kwargs) -> None:
		super().__init__(**kwargs)
		self.set_alert_source(self.alert_loader)

	def set_alert_source(self, alert_loader: Iterable[IOBase]) -> None:
		self.alert_loader = alert_loader
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
