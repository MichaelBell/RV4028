TARGET = femtorv
TOP = RV4028_femtorv
PROG ?= hello

OBJS += top.v femto_quark_bi.v

all: ${TARGET}.bit

$(TARGET).ys: $(OBJS)
	yosys -p "synth_ice40 -abc9 -device hx -top ${TOP} -json $@" -DICE40 $(OBJS) > yosys.log
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

clean:
	rm -f *.bit *.asc *.ys *.log

.PHONY: all prog clean
