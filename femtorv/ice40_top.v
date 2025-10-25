/* Copyright 2023-2024 (c) Michael Bell
   SPDX-License-Identifier: BSD-3-Clause
   
   Top module for ICE40 */

module ice40_top(
    input clk,
    input rst_n,

    output [31:0] addr,   // Note low bit is always 0, addresses are 16-bit aligned.

    output        wr_n,   // Write request
    output        rd_n,   // Read request
    output  [1:0] msk_n,  // Read/Write mask, low for bytes to be written
    output        iorq_n, // Asserted if the top bit of the address is set
    output        mreq_n, // Asserted during bus transactions
    input         wait_n, // Read not ready
    
    input         int_n,  // Interrupt - currently not supported

    inout  [15:0] data,
);

    wire [15:0] data_out;
    wire data_oe;

    wire [1:0] mreq_to_buffer;
    wire [1:0] wr_to_buffer;

    RV4028_femtorv i_rv4028(
        .clk(clk),
        .rst_n(rst_n),
        .addr(addr),
        .wr_n(wr_to_buffer),
        .rd_n(rd_n),
        .msk_n(msk_n),
        .iorq_n(iorq_n),
        .mreq_n(mreq_to_buffer),
        .wait_n(wait_n),
        .int_n(int_n),
        .data_in(data),
        .data_out(data_out),
        .data_oe(data_oe)
    );

    assign data = data_oe ? data_out : 16'bz;

    SB_IO #(
		.PIN_TYPE(6'b 0100_01),  // DDR output
		.PULLUP(1'b 0)
    ) io_wr_n (
		.PACKAGE_PIN(wr_n),
        .OUTPUT_CLK(clk),
        .INPUT_CLK(clk),
		.OUTPUT_ENABLE(1'b1),
		.D_OUT_0(wr_to_buffer[0]),
        .D_OUT_1(wr_to_buffer[1])
	);

    SB_IO #(
		.PIN_TYPE(6'b 0100_01),  // DDR output
		.PULLUP(1'b 0)
    ) io_mreq_n (
		.PACKAGE_PIN(mreq_n),
        .OUTPUT_CLK(clk),
        .INPUT_CLK(clk),
		.OUTPUT_ENABLE(1'b1),
		.D_OUT_0(mreq_to_buffer[0]),
        .D_OUT_1(mreq_to_buffer[1])
	);

endmodule