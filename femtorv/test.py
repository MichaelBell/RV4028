import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, FallingEdge, RisingEdge
from cocotb.utils import get_sim_time
from cocotb.types import LogicArray

from riscvmodel.insn import *

from riscvmodel.regnames import x0, x1, sp, gp, tp, a0, a1, a2, a3, a4, x9, x10, x11, x12, x16
from riscvmodel import csrnames
from riscvmodel.variant import RV32I

async def reset(dut):
    dut.wait_n.value = 1
    dut.busrq_n.value = 1
    dut.rst_n.value = 1
    dut.int_n.value = 1
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    assert dut.wr_n.value == 1
    assert dut.rd_n.value == 1
    assert dut.mreq_n.value == 1
    dut.rst_n.value = 1
    while dut.rd_n.value == 1:
        await ClockCycles(dut.clk, 1)
        await Timer(1, "ns")

async def expect_read(dut, data, addr=None, wait_cycles=0):
    assert dut.wr_n.value == 1
    assert dut.mreq_n.value == 1
    assert dut.rd_n.value == 0
    
    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 0

    if addr is None:
        global last_addr
        addr = dut.addr.value.to_unsigned()
        last_addr = addr
    else:
        assert dut.addr.value == addr

    if wait_cycles > 0:
        for _ in range(wait_cycles):
            dut.wait_n.value = 0
            await ClockCycles(dut.clk, 1, False)
            assert dut.wr_n.value == 1
            assert dut.msk_n.value == 0b00
            assert dut.mreq_n.value == 0
            assert dut.rd_n.value == 0
        dut.wait_n.value = 1

    await ClockCycles(dut.clk, 1, False)
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 0

    dut.data_in.value = data & 0xffff

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.mreq_n.value == 1
    assert dut.rd_n.value == 0
    dut.data_in.value = LogicArray("ZZZZZZZZZZZZZZZZ")

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 0
    assert dut.addr.value == addr + 2

    await ClockCycles(dut.clk, 1, False)
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 0

    dut.data_in.value = data >> 16

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    dut.data_in.value = LogicArray("ZZZZZZZZZZZZZZZZ")

async def expect_read_hword(dut, data, addr=None, mask=0, wait_cycles=0):
    assert dut.wr_n.value == 1
    assert dut.mreq_n.value == 1
    assert dut.rd_n.value == 0
    
    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == mask
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 0

    if addr is None:
        global last_addr
        addr = dut.addr.value.to_unsigned()
        last_addr = addr
    else:
        assert dut.addr.value == addr

    if wait_cycles > 0:
        for _ in range(wait_cycles):
            dut.wait_n.value = 0
            await ClockCycles(dut.clk, 1, False)
            assert dut.wr_n.value == 1
            assert dut.msk_n.value == mask
            assert dut.mreq_n.value == 0
            assert dut.rd_n.value == 0
        dut.wait_n.value = 1

    await ClockCycles(dut.clk, 1, False)
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == mask
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 0

    dut.data_in.value = data

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    dut.data_in.value = LogicArray("ZZZZZZZZZZZZZZZZ")

async def send_instr(dut, data, addr=None):
    await expect_read(dut, data, addr)

async def expect_write(dut, data, addr):
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.addr.value == addr
    assert dut.data_oe.value == 0

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")

    assert dut.wr_n.value == 0
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.addr.value == addr
    assert dut.data_oe.value == 0

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.wr_n.value == 0
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.data_oe.value == 1
    assert dut.data_out.value == data & 0xffff

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.mreq_n.value == 1
    assert dut.rd_n.value == 1
    assert dut.data_oe.value == 1
    assert dut.data_out.value == data & 0xffff

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.addr.value == addr + 2
    assert dut.data_oe.value == 0

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")

    assert dut.wr_n.value == 0
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.addr.value == addr + 2
    assert dut.data_oe.value == 0

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.wr_n.value == 0
    assert dut.msk_n.value == 0b00
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.data_oe.value == 1
    assert dut.data_out.value == data >> 16

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.mreq_n.value == 1
    assert dut.rd_n.value == 1
    assert dut.data_oe.value == 1
    assert dut.data_out.value == data >> 16

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.data_oe.value == 0

async def expect_write_hword(dut, data, addr, mask=0):

    def check_data(val):
        if mask == 0:
            assert val == data
        elif mask == 1:
            assert (val & 0xff00) == ((data & 0xff) << 8)
        elif mask == 2:
            assert (val & 0xff) == (data & 0xff)
        else:
            assert False

    assert dut.wr_n.value == 1
    assert dut.msk_n.value == mask
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.addr.value == addr
    assert dut.data_oe.value == 0

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")

    assert dut.wr_n.value == 0
    assert dut.msk_n.value == mask
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.addr.value == addr
    assert dut.data_oe.value == 0

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.wr_n.value == 0
    assert dut.msk_n.value == mask
    assert dut.mreq_n.value == 0
    assert dut.rd_n.value == 1
    assert dut.data_oe.value == 1
    check_data(dut.data_out.value.to_unsigned())

    await ClockCycles(dut.clk, 1, False)
    await Timer(1, "ns")
    assert dut.wr_n.value == 1
    assert dut.mreq_n.value == 1
    assert dut.rd_n.value == 1
    assert dut.data_oe.value == 1
    check_data(dut.data_out.value.to_unsigned())

    await ClockCycles(dut.clk, 1, True)
    await Timer(1, "ns")
    assert dut.data_oe.value == 0

async def load_reg(dut, reg, value):
    offset = random.randint(0, 0xFF) * 4
    instr = InstructionLW(reg, x0, offset).encode()
    await send_instr(dut, instr)

    await expect_read(dut, value, offset)

async def check_reg(dut, reg, value):
    offset = random.randint(0, 0xFF) * 4
    instr = InstructionSW(x0, reg, offset).encode()
    await send_instr(dut, instr)

    return await expect_write(dut, value & 0xFFFFFFFF, offset)

@cocotb.test()
async def test_start(dut):
    dut._log.info("Start")
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # ROM jumps to address 0
    await send_instr(dut, InstructionLUI(gp, 0x400).encode(), 0)

    # Do some maths
    for i in range(8):
        await send_instr(dut, InstructionADDI(i+8, x0, 0x102*i).encode())

    # Store a value
    await send_instr(dut, InstructionSW(gp, x9, 0x234).encode())
    await expect_write(dut, 0x102, 0x400234)

    # Load a value and store it again
    await send_instr(dut, InstructionLW(x16, gp, 0x334).encode())
    await expect_read(dut, 0x12345678, 0x400334)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x12345678, 0x400334)

@cocotb.test()
async def test_mem(dut):
    dut._log.info("Start")
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # ROM jumps to address 0
    await send_instr(dut, InstructionLUI(gp, 0x400).encode(), 0)

    await send_instr(dut, InstructionADDI(x9, x0, 0x132).encode())
    await send_instr(dut, InstructionLW(x16, gp, 0x334).encode())
    await expect_read(dut, 0x12345678, 0x400334)

    # Store hword
    await send_instr(dut, InstructionSH(gp, x9, 0x234).encode())
    await expect_write_hword(dut, 0x132, 0x400234)

    # Load a value and store it again
    await send_instr(dut, InstructionLH(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x1234, 0x400334)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x1234, 0x400334)
    await send_instr(dut, InstructionLH(x16, gp, 0x336).encode())
    await expect_read_hword(dut, 0x4321, 0x400336)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x4321, 0x400334)

    # Store byte
    await send_instr(dut, InstructionSB(gp, x9, 0x234).encode())
    await expect_write_hword(dut, 0x32, 0x400234, 2)
    await send_instr(dut, InstructionSB(gp, x9, 0x235).encode())
    await expect_write_hword(dut, 0x32, 0x400234, 1)

    # Load a value and store it again
    await send_instr(dut, InstructionLB(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x1234, 0x400334, 2)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x34, 0x400334)
    await send_instr(dut, InstructionLB(x16, gp, 0x335).encode())
    await expect_read_hword(dut, 0x1234, 0x400334, 1)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x12, 0x400334)
    await send_instr(dut, InstructionLB(x16, gp, 0x336).encode())
    await expect_read_hword(dut, 0x1234, 0x400336, 2)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x34, 0x400334)
    await send_instr(dut, InstructionLB(x16, gp, 0x337).encode())
    await expect_read_hword(dut, 0x1234, 0x400336, 1)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x12, 0x400334)

    # Test sign extension
    await send_instr(dut, InstructionLB(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x12c4, 0x400334, 2)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0xffffffc4, 0x400334)
    await send_instr(dut, InstructionLB(x16, gp, 0x335).encode())
    await expect_read_hword(dut, 0x9234, 0x400334, 1)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0xffffff92, 0x400334)
    await send_instr(dut, InstructionLBU(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x12c4, 0x400334, 2)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0xc4, 0x400334)
    await send_instr(dut, InstructionLBU(x16, gp, 0x335).encode())
    await expect_read_hword(dut, 0x9234, 0x400334, 1)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x92, 0x400334)
    await send_instr(dut, InstructionLH(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x9234, 0x400334)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0xffff9234, 0x400334)
    await send_instr(dut, InstructionLHU(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x9234, 0x400334)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x9234, 0x400334)

    # Store bytes
    await send_instr(dut, InstructionADDI(x10, x0, 0x143).encode())
    await send_instr(dut, InstructionADDI(x11, x0, 0x145).encode())
    await send_instr(dut, InstructionADDI(x12, x0, 0x167).encode())
    await send_instr(dut, InstructionSB(gp, x9, 0x234).encode())
    await expect_write_hword(dut, 0x32, 0x400234, 2)
    await send_instr(dut, InstructionSB(gp, x10, 0x236).encode())
    await expect_write_hword(dut, 0x43, 0x400236, 2)
    await send_instr(dut, InstructionSB(gp, x11, 0x238).encode())
    await expect_write_hword(dut, 0x45, 0x400238, 2)
    await send_instr(dut, InstructionSB(gp, x12, 0x23a).encode())
    await expect_write_hword(dut, 0x67, 0x40023a, 2)


@cocotb.test()
async def test_wait(dut):
    dut._log.info("Start")
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # ROM jumps to address 0
    await send_instr(dut, InstructionLUI(gp, 0x400).encode(), 0)

    # Load a value and store it again
    await send_instr(dut, InstructionLW(x16, gp, 0x334).encode())
    await expect_read(dut, 0x12345678, 0x400334, 3)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x12345678, 0x400334)

    await send_instr(dut, InstructionLH(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x1234, 0x400334, 0, 7)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x1234, 0x400334)
    await send_instr(dut, InstructionLH(x16, gp, 0x336).encode())
    await expect_read_hword(dut, 0x4321, 0x400336, 0, 1)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x4321, 0x400334)

    await send_instr(dut, InstructionLB(x16, gp, 0x334).encode())
    await expect_read_hword(dut, 0x1234, 0x400334, 2, 7)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x34, 0x400334)
    await send_instr(dut, InstructionLB(x16, gp, 0x335).encode())
    await expect_read_hword(dut, 0x4321, 0x400334, 1, 1)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x43, 0x400334)

@cocotb.test()
async def test_branch(dut):
    dut._log.info("Start")
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # ROM jumps to address 0
    await send_instr(dut, InstructionLUI(gp, 0x400).encode(), 0)

    await send_instr(dut, InstructionADDI(a0, x0, 0x132).encode())
    await send_instr(dut, InstructionADDI(a1, x0, 0x132).encode())
    await send_instr(dut, InstructionADDI(a2, x0, 0x131).encode())
    await send_instr(dut, InstructionADDI(a3, x0, 0x134).encode())

    await send_instr(dut, InstructionBLT(a1, a0, 0x100).encode(), 0x14)
    await send_instr(dut, InstructionBLT(a2, a0, 0x100).encode(), 0x18)
    await send_instr(dut, InstructionBLT(a3, a0, 0x100).encode(), 0x118)
    await send_instr(dut, InstructionBEQ(a1, a0, 0x100).encode(), 0x11c)
    await send_instr(dut, InstructionBEQ(a2, a0, 0x100).encode(), 0x21c)
    await send_instr(dut, InstructionBEQ(a3, a0, 0x100).encode(), 0x220)
    await send_instr(dut, InstructionBGE(a1, a0, 0x100).encode(), 0x224)
    await send_instr(dut, InstructionBGE(a2, a0, 0x100).encode(), 0x324)
    await send_instr(dut, InstructionBGE(a3, a0, 0x100).encode(), 0x328)
    await send_instr(dut, InstructionBNE(a1, a0, 0x100).encode(), 0x428)
    await send_instr(dut, InstructionBNE(a2, a0, 0x100).encode(), 0x42c)
    await send_instr(dut, InstructionBNE(a3, a0, 0x100).encode(), 0x52c)
    await send_instr(dut, InstructionBLTU(a1, a0, 0x100).encode(), 0x62c)
    await send_instr(dut, InstructionBLTU(a2, a0, 0x100).encode(), 0x630)
    await send_instr(dut, InstructionBLTU(a3, a0, 0x100).encode(), 0x730)
    await send_instr(dut, InstructionBGEU(a1, a0, 0x100).encode(), 0x734)
    await send_instr(dut, InstructionBGEU(a2, a0, 0x100).encode(), 0x834)
    await send_instr(dut, InstructionBGEU(a3, a0, 0x100).encode(), 0x838)

    await send_instr(dut, InstructionNOP().encode(), 0x938)

@cocotb.test()
async def test_interrupt(dut):
    dut._log.info("Start")
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # ROM jumps to 0, cause should be 0
    await send_instr(dut, InstructionCSRRS(a0, x0, csrnames.mcause).encode(), 0)
    await check_reg(dut, a0, 0)

    await send_instr(dut, InstructionLUI(gp, 0x400).encode(), 8)

    # Jump to a higher address
    await send_instr(dut, InstructionJAL(x0, 0x1000).encode(), 0xC)

    # Raise interrupt
    dut.int_n.value = 0

    # Interrupts not enabled so no change
    await send_instr(dut, InstructionADDI(x1, x0, 0x8).encode(), 0x100C)

    # Allow interrupts
    await send_instr(dut, InstructionCSRRW(x0, x1, csrnames.mstatus).encode(), 0x1010)
    await send_instr(dut, InstructionNOP().encode(), 0x1014)

    # Interrupt vectors to 0, cause set
    await send_instr(dut, InstructionCSRRS(a0, x0, csrnames.mcause).encode(), 0)
    await check_reg(dut, a0, 0x80000000)
    await send_instr(dut, InstructionADDI(x1, x0, 0x100).encode(), 0x8)
    await send_instr(dut, InstructionMRET().encode(), 0xC)

    # Return to correct address
    await send_instr(dut, InstructionSW(gp, x1, 0x234).encode(), 0x1018)
    await expect_write(dut, 0x100, 0x400234)

### Random operation testing ###
reg = [0] * 32

# Each Op does reg[d] = fn(a, b)
# fn will access reg global array
class SimpleOp:
    def __init__(self, rvm_insn, fn, name):
        self.rvm_insn = rvm_insn
        self.fn = fn
        self.name = name
        self.is_mem_op = False

    def randomize(self):
        self.rvm_insn_inst = self.rvm_insn()
        self.rvm_insn_inst.randomize(variant=RV32I)
    
    def execute_fn(self, rd, rs1, arg2):
        if rd != 0:
            reg[rd] = self.fn(rs1, arg2)
            while reg[rd] < -0x80000000: reg[rd] += 0x100000000
            while reg[rd] > 0x7FFFFFFF:  reg[rd] -= 0x100000000

    def encode(self, rd, rs1, arg2):
        return self.rvm_insn(rd, rs1, arg2).encode()
    
    def get_valid_rd(self):
        return random.randint(0, 15)

    def get_valid_rs1(self):
        return random.randint(0, 15)

    def get_valid_arg2(self):
        return (random.randint(0, 15) if issubclass(self.rvm_insn, InstructionRType) else 
                self.rvm_insn_inst.shamt.value if issubclass(self.rvm_insn, InstructionISType) else
                self.rvm_insn_inst.imm.value)

ops_alu = [
    SimpleOp(InstructionADDI, lambda rs1, imm: reg[rs1] + imm, "+i"),
    SimpleOp(InstructionADD, lambda rs1, rs2: reg[rs1] + reg[rs2], "+"),
    SimpleOp(InstructionSUB, lambda rs1, rs2: reg[rs1] - reg[rs2], "-"),
    SimpleOp(InstructionANDI, lambda rs1, imm: reg[rs1] & imm, "&i"),
    SimpleOp(InstructionAND, lambda rs1, rs2: reg[rs1] & reg[rs2], "&"),
    SimpleOp(InstructionORI, lambda rs1, imm: reg[rs1] | imm, "|i"),
    SimpleOp(InstructionOR, lambda rs1, rs2: reg[rs1] | reg[rs2], "|"),
    SimpleOp(InstructionXORI, lambda rs1, imm: reg[rs1] ^ imm, "^i"),
    SimpleOp(InstructionXOR, lambda rs1, rs2: reg[rs1] ^ reg[rs2], "^"),
    SimpleOp(InstructionSLTI, lambda rs1, imm: 1 if reg[rs1] < imm else 0, "<i"),
    SimpleOp(InstructionSLT, lambda rs1, rs2: 1 if reg[rs1] < reg[rs2] else 0, "<"),
    SimpleOp(InstructionSLTIU, lambda rs1, imm: 1 if (reg[rs1] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0, "<iu"),
    SimpleOp(InstructionSLTU, lambda rs1, rs2: 1 if (reg[rs1] & 0xFFFFFFFF) < (reg[rs2] & 0xFFFFFFFF) else 0, "<u"),
    SimpleOp(InstructionSLLI, lambda rs1, imm: reg[rs1] << imm, "<<i"),
    SimpleOp(InstructionSLL, lambda rs1, rs2: reg[rs1] << (reg[rs2] & 0x1F), "<<"),
    SimpleOp(InstructionSRLI, lambda rs1, imm: (reg[rs1] & 0xFFFFFFFF) >> imm, ">>li"),
    SimpleOp(InstructionSRL, lambda rs1, rs2: (reg[rs1] & 0xFFFFFFFF) >> (reg[rs2] & 0x1F), ">>l"),
    SimpleOp(InstructionSRAI, lambda rs1, imm: reg[rs1] >> imm, ">>i"),
    SimpleOp(InstructionSRA, lambda rs1, rs2: reg[rs1] >> (reg[rs2] & 0x1F), ">>"),
]

@cocotb.test()
async def test_random_alu(dut):
    dut._log.info("Start")
  
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    seed = random.randint(0, 0xFFFFFFFF)
    #seed = 1508125843
    debug = False
    for test in range(20):
        random.seed(seed + test)
        dut._log.info("Running test with seed {}".format(seed + test))
        for i in range(1, 32):
            reg[i] = random.randint(-0x80000000, 0x7FFFFFFF)
            if debug: print("Set reg {} to {}".format(i, reg[i]))
            await load_reg(dut, i, reg[i])

        if True:
            for i in range(32):
                await check_reg(dut, i, reg[i])

        last_instr = ops_alu[0]
        for i in range(200):
            while True:
                try:
                    instr = random.choice(ops_alu)
                    instr.randomize()
                    rd = instr.get_valid_rd()
                    rs1 = instr.get_valid_rs1()
                    arg2 = instr.get_valid_arg2()

                    instr.execute_fn(rd, rs1, arg2)
                    break
                except ValueError:
                    pass

            if debug: print("x{} = x{} {} {}, now {} {:08x}".format(rd, rs1, arg2, instr.name, reg[rd], instr.encode(rd, rs1, arg2)))
            await send_instr(dut, instr.encode(rd, rs1, arg2))
            if debug:
                await check_reg(dut, rd, reg[rd])

        for i in range(32):
            await check_reg(dut, i, reg[i])
