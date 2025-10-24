import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, FallingEdge, RisingEdge
from cocotb.utils import get_sim_time
from cocotb.types import LogicArray

from riscvmodel.insn import *

from riscvmodel.regnames import x0, x1, sp, gp, tp, a0, a1, a2, a3, a4
from riscvmodel import csrnames
from riscvmodel.variant import RV32E

async def reset(dut):
    dut.wait_n.value = 1
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    assert dut.wr_n.value == 1
    assert dut.wrm_n.value == 0b11
    assert dut.rd_n.value == 1
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1, False)

async def send_instr(dut, data):
    for i in range(2):
        assert dut.wr_n.value == 1
        assert dut.wrm_n.value == 0b11
        if dut.rd_n.value == 0: break
        await ClockCycles(dut.clk, 1, False)

    assert dut.wr_n.value == 1
    assert dut.wrm_n.value == 0b11
    assert dut.rd_n.value == 0

    addr = dut.addr.value.to_unsigned()

    await ClockCycles(dut.clk, 1, False)
    assert dut.wr_n.value == 1
    assert dut.wrm_n.value == 0b11
    assert dut.rd_n.value == 0

    dut.data.value = data & 0xffff

    await ClockCycles(dut.clk, 1, False)
    assert dut.wr_n.value == 1
    assert dut.wrm_n.value == 0b11
    assert dut.rd_n.value == 0
    assert dut.addr.value == addr + 2

    await ClockCycles(dut.clk, 1, False)
    assert dut.wr_n.value == 1
    assert dut.wrm_n.value == 0b11
    assert dut.rd_n.value == 0

    dut.data.value = data >> 16

    await ClockCycles(dut.clk, 1, False)
    dut.data.value = LogicArray("ZZZZZZZZZZZZZZZZ")

@cocotb.test()
async def test_start(dut):
    dut._log.info("Start")
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # Do some maths
    for i in range(8):
        await send_instr(dut, InstructionADDI(i+8, x0, 0x102*i).encode())

