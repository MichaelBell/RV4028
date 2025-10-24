#!/bin/bash

verilator --lint-only -DSIM --timing -Wall -Wno-DECLFILENAME -Wno-MULTITOP top.v femto_quark_bi.v