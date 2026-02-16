#!/bin/bash

r=20
while yosys -p "scratchpad -set abc9.D 20000; synth_ice40 -abc9 -device hx -top ice40_top -json femtorv.ys" --autoidx $r -DICE40 ice40_top.v rv4028.v femto_quark_bi.v rom.v > yosys.log 2>& 1
do
  ((--r)) || exit 2
  echo -n "$((r+1)) "
  egrep "[0-9]+ submodules" yosys.log | head -1
done

exit 0
