TARGET = femtorv
TOP = ice40_top
PROG ?= hello

OBJS += ice40_top.v rv4028.v femto_quark_bi.v rom.v

all: ${TARGET}.bit

rom.hex: rom_test.py
	python3 rom_test.py

$(TARGET).ys: $(OBJS) rom.hex
	yosys -p "scratchpad -set abc9.D 20000; synth_ice40 -abc9 -device hx -top ${TOP} -json $@" --autoidx 10 -DICE40 $(OBJS) > yosys.log
	@grep Warn yosys.log || true
	@grep Error yosys.log || true
	@egrep "[0-9]+ submodules" yosys.log | head -1
	@egrep "[0-9]+   SB_DFF" yosys.log | awk '{sum+=$$1;}END{printf("%9d   SB_DFF*\n", sum/2);}'
	@egrep "[0-9]+   SB_LUT" yosys.log | head -1
	@echo

$(TARGET).asc: $(TARGET).ys
	./nextpnr.sh -r --hx1k --json $< --package vq100 --asc $@ --opt-timing --pcf hx1k-vqfp.pcf
	@grep Warn nextpnr.log || true
	@grep Error nextpnr.log || true
	@grep "Max frequency.*clk" nextpnr.log | tail -1
	@echo

$(TARGET).bit: $(TARGET).asc
	icepack $< $@

prog: $(TARGET).bit
	mpremote a1 mount . + exec "import os; os.chdir('/'); import flash_prog; flash_prog.program('/remote/$(TARGET).bit'); flash_prog.release_pins()"

clean:
	rm -f *.bit *.asc *.ys *.log

.PHONY: all prog clean
