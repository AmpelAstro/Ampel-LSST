#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTPhotoCombiner.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Tuple, Set, Union
from ampel.type import DataPointId, ChannelId
from ampel.content.DataPoint import DataPoint
from ampel.content.T1Record import T1Record
from ampel.compile.T1PhotoCombiner import T1PhotoCombiner


class LSSTPhotoCombiner(T1PhotoCombiner):

	require = "channel",

	def __init__(self, **kwargs):

		super().__init__(**kwargs)

		if not self.resource:
			raise ValueError("Resource missing")

		if not self.resource.get('channel'):
			raise ValueError("Resource 'channels' is missing")

		self.chan_config = self.resource.get('channel')

		raise NotImplementedError()
