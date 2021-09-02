#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTCompilerOptions.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 25.08.2021
# Last Modified Date: 25.08.2021
# Last Modified By  : mf <vbrinnel@physik.hu-berlin.de>

from typing import Dict, Any
from ampel.model.ingest.CompilerOptions import CompilerOptions

class LSSTCompilerOptions(CompilerOptions):
	stock: Dict[str, Any] = {'tag': 'LSST'}
	t0: Dict[str, Any] = {'tag': 'LSST'}
	t1: Dict[str, Any] = {'tag': 'LSST'}
	state_t2: Dict[str, Any] = {'tag': 'LSST'}
	point_t2: Dict[str, Any] = {'tag': 'LSST'}
	stock_t2: Dict[str, Any] = {'tag': 'LSST'}
