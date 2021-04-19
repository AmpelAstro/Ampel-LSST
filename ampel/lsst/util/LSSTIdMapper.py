#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/util/LSSTIdMapper.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import List, Union, Iterable, overload, cast
from ampel.type import StrictIterable, StockId
from ampel.abstract.AbsIdMapper import AbsIdMapper


class LSSTIdMapper(AbsIdMapper):

	@overload
	@classmethod
	def to_ampel_id(cls, lsst_id: str) -> int:
		...

	@overload
	@classmethod
	def to_ampel_id(cls, lsst_id: StrictIterable[str]) -> List[int]:
		...

	@classmethod
	def to_ampel_id(cls, lsst_id: Union[str, StrictIterable[str]]) -> Union[int, List[int]]: # type: ignore[override]

		if isinstance(lsst_id, str):
			raise NotImplementedError()
		else:
			return [cast(int, cls.to_ampel_id(name)) for name in lsst_id]

	@overload
	@classmethod
	def to_ext_id(cls, ampel_id: StockId) -> str:
		...

	@overload
	@classmethod
	def to_ext_id(cls, ampel_id: StrictIterable[StockId]) -> List[str]:
		...

	@classmethod
	def to_ext_id(cls, ampel_id: Union[StockId, StrictIterable[StockId]]) -> Union[str, List[str]]: # type: ignore[override]
		# Handle sequences
		if isinstance(ampel_id, Iterable) and not isinstance(ampel_id, str):
			return [cast(str, cls.to_ext_id(l)) for l in ampel_id]

		elif isinstance(ampel_id, int):
			raise NotImplementedError()

		raise NotImplementedError()


to_ampel_id = LSSTIdMapper.to_ampel_id
to_lsst_id = LSSTIdMapper.to_ext_id
