/* Copyright 2023-2026 (c) Michael Bell
   SPDX-License-Identifier: BSD-3-Clause
   
   Top module for ICE40 */

`default_nettype none

module ice40_top(
    input clk,
    input rst_n,

    inout [31:0] addr,   // Note low bit is always 0, addresses are 16-bit aligned.

    inout        wr_n,   // Write request
    inout        rd_n,   // Read request
    inout  [1:0] msk_n,  // Read/Write mask, low for bytes to be written
    inout        iorq_n, // Asserted if the top bit of the address is set
    inout        req_n,  // Asserted during bus transactions
    input         wait_n, // Read not ready
    
    input         int_n,  // Interrupt - currently not supported
    input         busrq_n,  // Request bus release
    output        busack_n, // Allow bus release

    inout  [15:0] data,

    inout         lo_addr_n,  // Asserted if addr[31:24] is 0
    input   [2:0] spare,
    output        led
);

    wire [31:0] addr_out;
    wire [15:0] data_out;
    wire data_oe;

    wire [1:0] mreq_to_buffer;
    wire [1:0] wr_to_buffer;
    wire       femto_rd_n;
    wire [1:0] femto_msk_n;
    wire       femto_iorq_n;

    reg [1:0] rst_sync = 2'b11;
    always @(negedge clk) begin
        rst_sync <= {rst_sync[0], rst_n};
    end

    RV4028_femtorv i_rv4028(
        .clk(clk),
        .rst_n(rst_sync[1]),
        .addr(addr_out),
        .wr_n(wr_to_buffer),
        .rd_n(femto_rd_n),
        .msk_n(femto_msk_n),
        .iorq_n(femto_iorq_n),
        .mreq_n(mreq_to_buffer),
        .wait_n(wait_n),
        .int_n(int_n),
        .busrq_n(busrq_n),
        .busack_n(busack_n),
        .data_in(data),
        .data_out(data_out),
        .data_oe(data_oe)
    );

    assign data = data_oe ? data_out : 16'bz;
    assign addr = busack_n ? addr_out : 32'bz;

    SB_IO #(
		.PIN_TYPE(6'b 0100_01),  // DDR output
		.PULLUP(1'b 0)
    ) io_wr_n (
		.PACKAGE_PIN(wr_n),
        .OUTPUT_CLK(clk),
        .INPUT_CLK(clk),
		.OUTPUT_ENABLE(busack_n),
		.D_OUT_0(wr_to_buffer[0]),
        .D_OUT_1(wr_to_buffer[1])
	);

    SB_IO #(
		.PIN_TYPE(6'b 0100_01),  // DDR output
		.PULLUP(1'b 0)
    ) io_mreq_n (
		.PACKAGE_PIN(req_n),
        .OUTPUT_CLK(clk),
        .INPUT_CLK(clk),
		.OUTPUT_ENABLE(busack_n),
		.D_OUT_0(mreq_to_buffer[0]),
        .D_OUT_1(mreq_to_buffer[1])
	);

    assign rd_n      = busack_n ? femto_rd_n : 1'bz;
    assign msk_n     = busack_n ? femto_msk_n : 2'bz;
    assign iorq_n    = busack_n ? femto_iorq_n : 1'bz;
    assign lo_addr_n = busack_n ? |addr_out[31:25] : 1'bz;

    assign led = !femto_rd_n;

endmodule