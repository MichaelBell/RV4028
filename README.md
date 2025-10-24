# RV4028 - A hackable Risc-V computer

RV4028 is intended as a Risc-V equivalent of the excellent [RC2014 Z80](https://rc2014.co.uk/) homebrew computer.

The idea is to create a minimal Risc-V system that is easy to understand and extend.

The inspiration for this came from [@theJPster](https://github.com/thejpster)'s [post](https://bsky.app/profile/thejpster.org.uk/post/3m3ngtx5sfc2i).

All hardware and software will be open source and permissively licensed.

## Architecture

The system bus has a 32-bit address and 16-bit data, which fits reasonably well with an RV32 system and readily available (P)SRAM chips, and runs at 3.3V.

Modules are attached by an 80-pin dual row header, similar to RC2014 modules but with 2 rows of pins instead of 1.

The pinout of the first row is chosen such that RC2014 modules might be compatible, if 3v3 capable components are used.  This also means that modules not requiring access to the full bus can be single row.

![Bus connector](BusConn.png)

### Bus cycle details

Addresses are always 16-bit aligned and a byte mask is used for single byte stores.

All writes complete in a single cycle.

Reads normally complete in two cycles, but a wait pin may be asserted to extend the read cycle.

TODO: Add diagrams.

## Software

The intention is to be able to run standard RV32I programs with a C SDK.  A Micropython port and Rust support are likely.

It is currently not a goal to support either real time operating systems (although this may be possible in future), or Linux (which would likely not be possible without moving to a larger FPGA).

# Initial modules

## CPU

Keeping things minimal and simple, we use a Bruno Levy's [FemtoRV](https://github.com/BrunoLevy/learn-fpga/tree/master/FemtoRV) Quark (RV32I) core with some small modifications, and a wrapper to handle breaking each 32-bit data access into 16-bit accesses.  This is the most minimal Risc-V instruction set and can fit in a small FPGA, so we use an ICE40 [HX1K](https://www.latticesemi.com/ice40), which is available in a 100-pin QFP.

A small flash is required for the FPGA configuration, a header will be provided that will allow the FPGA to be held in reset and the flash programmed.  Although it is significantly larger than required, using a 1MB [W25Q80DV](https://www.lcsc.com/datasheet/C14086.pdf) seems cost effective. 

## RAM

The two candidates here are PSRAM, such as the [IS66WVE](https://www.lcsc.com/datasheet/C1350157.pdf), or SRAM such as the [CY7C1041G30](https://www.lcsc.com/datasheet/C2944680.pdf).

The PSRAM is larger but slower, and the larger capacities only seem available in BGA packages.  The linked SRAM is available in TSOP, which may allow for easier assembly.

## ROM

Something like [SST39VF3202C](https://www.lcsc.com/datasheet/C637403.pdf) looks suitable, and available at the same access speed as the PSRAM (70ns).

ROM might not be required - we can embed a small amount of ROM (6kB) in the CPU gateware which could be enough for a simple SD card driver, allowing a program to be loaded from SD card to RAM without any ROM.

## IO

An [RP2350B](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf) is used for IO.  The board should include:
- A UART
- Two I2C broken out to Qw/ST compatible ports
- A micro SD card socket
- An SPI with a couple of chip selects (this should be made easy to connect to the CPU for updating the gateware)
- Some GPIO

8 bits of address should easily be sufficient, and 8 bits of data should also be fine, which allows this to be single row.

If we also wired clock and reset from the RP2350 then no it could provide a clock, meaning a separate clock module would not be required.
