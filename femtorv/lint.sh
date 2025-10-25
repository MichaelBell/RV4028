#!/bin/bash

verilator --lint-only -DSIM --timing -Wall -Wno-DECLFILENAME -Wno-MULTITOP rv4028.v femto_quark_bi.v