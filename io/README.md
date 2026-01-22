# RP2350 IO module for RV4028

## Features

Basic idea is to expose the RP2350's hardware blocks as memory mapped peripherals.

Peripherals:
- 2 UARTs (one to backplane, one on headers)
- 2 I2C (QwST connectors)
- 1 SPI with 3 or 4 chip selects (can be used for programming the FPGA)
- SD card
- Maybe a WS2812 interface (exposing 5V power)
- Further pins as general purpose IO.  Maybe could expose a PIO block?

Clock and reset are connected, and can optionally be driven, depending on the loaded firmware.

WAIT and INT should be connected.

Other wiring:
- USB to the USB pins on the backplane
- SWD to a header

## Interface

Byte at a time data - this is very suitable for UART, I2C, SPI.

Address - A1-A7 connected, plus ~A31 and A30-A28 ORed together, with the module selected when the result is low.  The modules canonical address space is therefore even addresses within 0x8FFF_FF00 - 0x8FFF_FFFF.  Accessing it at other addresses should be avoided to prevent conflicting responses from different modules (maybe we put some protection in the gateware to prevent access to invalid addresses?)

IOSEL = ~A31 OR A30 OR A29 OR A28, RDREQ = REQ OR RD and WR are needed in addition to the 7 low address pins and 8 data pins.

## Implementation

PIO programs are used to detect read and write accesses.

### Write

Watches for WR going low and then checks IOSEL, if it is high the transaction is not for this module.

If low, the address and data pins are DMA'd from the PIO into a ring buffer and an IRQ asserted to wake a CPU task to read the ring buffer.

The CPU reads while the ring buffer is not empty, and forwards the data to the peripheral based on the memory map.

PIO waits for WR to go high.

### Read

Watches for RDREQ going low and then checks IOSEL, if it is high the transaction is not for this module.

If low, the address is DMA'd to the trigger read address of a waiting DMA channel.  This reads from a table of source addresses into the read trigger address of a second waiting DMA channel, which will DMA one byte from (normally) a peripheral address to the PIO, which will set the data pins.  When RDREQ goes high the data are set back to inputs and the PIO resets.

Latency from RDREQ going low to data being presented should be around 10-15 cycles:
- Wait (2 cycles input latency)
- Jmp
- In pins (auto push)
- DMA trigger
- DMA read from lookup table
- DMA write and trigger
- DMA read from peripheral
- Out pins (auto pull)

This has a little less than 1.5 cycles to complete if WAIT isn't asserted, so is rather tight but should work if the RP2350 clock is > 12x faster than the RV4028 clock.  Could do with prototyping to check the cycle count is acheivable.

### Pin mapping

0-1 UART0 to header
2-3 Ground, so they will read as zero
4-10 A1-A7
11-18 D0-D7
19 CLK
20 RESET
21 INT
22 WAIT
23 IOSEL
24 WR
25 RD
26-27 UART1 to backplane
28-31 SPI1
32-33 I2C0
34-39 SD card (SPI0)
40-41 Additional SPI chip selects
42-43 I2C1
44 WS2812b LED data
45 LED
46-47 GPIO
