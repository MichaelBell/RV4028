/* Copyright 2023-2024 (c) Michael Bell
   SPDX-License-Identifier: BSD-3-Clause
   
   Top module for RV4028 CPU */

module RV4028_femtorv(
    input clk,
    input rst_n,

    output [31:0] addr,   // Note low bit is always 0, addresses are 16-bit aligned.

    output        wr_n,   // Write request
    output        rd_n,   // Read request
    output  [1:0] wrm_n,  // Write mask, low for bytes to be written
    output        iorq_n, // For compatibility - set if the top bit of the address is set
    output        mreq_n, // For compatibility - set if the top bit of the address is not set
    input         wait_n, // Read not ready
    
    input         int_n,  // Interrupt - currently not supported

    inout  [15:0] data
);

    wire [31:0] femto_addr;
    wire [31:0] femto_wdata;
    wire [31:0] femto_rdata;
    wire  [3:0] femto_wmask;
    wire        femto_rstrb;
    wire        femto_rlo;
    wire        femto_rbusy;

    FemtoRV32 i_femtorv(
        .clk(clk),
        .mem_addr(femto_addr),
        .mem_wdata(femto_wdata),
        .mem_wmask(femto_wmask),
        .mem_rdata(femto_rdata),
        .mem_rstrb(femto_rstrb),
        .mem_rlo(femto_rlo),
        .mem_rbusy(femto_rbusy),
        .mem_wbusy(1'b0),
        .resetn(rst_n)
    );

    reg [15:0] buffered_rdata;
    reg        read_started;
    reg        bus_cycle;
    reg        read_in_progress;
    wire       read_finishing;
    assign femto_rdata = {data, femto_rlo ? data : buffered_rdata};
    assign femto_rbusy = femto_rstrb | (read_in_progress && !read_finishing);
    assign rd_n = !(femto_rstrb | read_in_progress);
    assign wr_n = !(|femto_wmask);

    wire write_lo = femto_wmask[1:0] != 2'b00;
    wire write_hi = femto_wmask[3:2] != 2'b00;

    always @(posedge clk) begin
        if (!rst_n) begin
            bus_cycle <= 0;
            read_started <= 0;
            read_in_progress <= 0;
        end else begin
            if (femto_rstrb || read_in_progress) begin
                if (!read_started) begin
                    read_started <= 1;
                    read_in_progress <= 1;
                end else if (!wait_n) begin
                    // Wait
                end else if (!bus_cycle) begin
                    buffered_rdata <= data;
                    read_started <= 0;
                    if (!femto_rlo) bus_cycle <= 1;
                    else read_in_progress <= 0;
                end else begin
                    read_started <= 0;
                    bus_cycle <= 0;
                    read_in_progress <= 0;
                end
            end
            else if (|femto_wmask) begin
                if (bus_cycle == 0) begin
                    if (write_hi) bus_cycle <= 1;
                end else begin
                    bus_cycle <= 0;
                end
            end
        end
    end

    assign read_finishing = read_in_progress && read_started && wait_n && (femto_rlo || bus_cycle);

    wire addr1 = bus_cycle || (!write_lo && write_hi) || (femto_rbusy && femto_rlo && femto_addr[1]);
    assign addr = {femto_addr[31:2], addr1, 1'b0};
    assign wrm_n = addr1 ? ~femto_wmask[3:2] : ~femto_wmask[1:0];

    assign data = |femto_wmask ? (addr1 ? femto_wdata[31:16] : femto_wdata[15:0]) : 16'bz;

    assign iorq_n = !addr[31] | (rd_n & wr_n);
    assign mreq_n = addr[31] | (rd_n & wr_n);

endmodule
