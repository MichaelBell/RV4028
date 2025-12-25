import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, FallingEdge, RisingEdge
from cocotb.utils import get_sim_time
from cocotb.types import LogicArray

from riscvmodel.insn import *

from riscvmodel.regnames import x0, x1, sp, gp, tp, a0, a1, a2, a3, a4, x9, x16
from riscvmodel import csrnames
from riscvmodel.variant import RV32I

async def reset(dut):
    dut.wait_n.value = 1
    dut.busrq_n.value = 1
    dut.rst_n.value = 1
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

async def expect_read(dut, data, addr=None):
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
        addr = dut.addr.value.to_unsigned()
    else:
        assert dut.addr.value == addr

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

async def send_instr(dut, data):
    await expect_read(dut, data)

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

    await send_instr(dut, InstructionLUI(gp, 0x400).encode())

    # Store a value
    await send_instr(dut, InstructionSW(gp, x9, 0x234).encode())
    await expect_write(dut, 0x102, 0x400234)

    # Load a value and store it again
    await send_instr(dut, InstructionLW(x16, gp, 0x334).encode())
    await expect_read(dut, 0x12345678, 0x400334)
    await send_instr(dut, InstructionSW(gp, x16, 0x334).encode())
    await expect_write(dut, 0x12345678, 0x400334)
