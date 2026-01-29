/* Copyright 2023-2026 (c) Michael Bell
   SPDX-License-Identifier: BSD-3-Clause
   
   Top module for RV4028 CPU */

`default_nettype none

module RV4028_femtorv(
    input clk,
    input rst_n,

    output [31:0] addr,   // Note low bit is always 0, addresses are 16-bit aligned.

    output  [1:0] wr_n,   // Write request
    output        rd_n,   // Read request
    output  [1:0] msk_n,  // Read/Write mask, low for bytes to be written
    output        iorq_n, // Asserted if the top bit of the address is set
    output  [1:0] mreq_n, // Asserted during bus transactions
    input         wait_n, // Read not ready
    
    input         int_n,  // Interrupt
    input         busrq_n,  // Request bus release
    output reg    busack_n, // Allow bus release

    input  [15:0] data_in,
    output [15:0] data_out,
    output        data_oe
);

    wire [31:0] femto_addr;
    wire [31:0] femto_wdata;
    wire [31:0] femto_rdata;
    wire  [3:0] femto_mask;
    wire        femto_half;
    wire        femto_wnext;
    wire        femto_wstrb;
    wire        femto_rstrb;
    wire        femto_rbusy;
    wire        femto_wbusy;

    FemtoRV32 i_femtorv(
        .clk(clk),
        .mem_addr(femto_addr),
        .mem_wdata(femto_wdata),
        .mem_wnext(femto_wnext),
        .mem_wstrb(femto_wstrb),
        .mem_mask(femto_mask),
        .mem_half(femto_half),
        .mem_rdata(femto_rdata),
        .mem_rstrb(femto_rstrb),
        .mem_rbusy(femto_rbusy),
        .mem_wbusy(femto_wbusy),
        .interrupt_request(!int_n),
        .resetn(rst_n)
    );

    reg [15:0] buffered_rdata;
    wire [15:0] rom_data;
    wire [15:0] rdata;
    reg  [1:0] read_cycle;
    reg  [1:0] write_cycle;
    wire       read_in_progress;
    wire       write_in_progress;
    wire       read_finishing;
    wire       write_finishing;
    wire       is_rom_addr;
    assign femto_rdata = {rdata, read_cycle[1] ? buffered_rdata : rdata};
    assign femto_rbusy = femto_rstrb || (read_in_progress && !read_finishing) || !busack_n;
    assign femto_wbusy = femto_wstrb || (write_in_progress && !write_finishing);
    assign rd_n = !(femto_rstrb || read_in_progress) || is_rom_addr;
    assign wr_n[0] = !(femto_wstrb || write_cycle == 2'b10);
    assign wr_n[1] = !(femto_wstrb || write_cycle == 2'b10);

    assign read_in_progress = |read_cycle;
    assign write_in_progress = |write_cycle;

    assign read_finishing = read_cycle[0] && wait_n && (femto_half || read_cycle[1]);
    assign write_finishing = write_cycle[0] && (femto_half || write_cycle[1]);

    assign is_rom_addr = (femto_addr[31:24] == 8'h08);
    assign rdata = is_rom_addr ? rom_data : data_in;

    always @(posedge clk) begin
        if (!rst_n) begin
            read_cycle <= 0;
            busack_n <= 1'b1;
        end else begin
            if (femto_rstrb && !busrq_n)
                busack_n <= 1'b0;
            else 
            if (femto_rstrb || read_in_progress || (busrq_n && !busack_n)) begin
                busack_n <= 1'b1;
                if (!(!wait_n && read_cycle[0])) begin
                    read_cycle <= read_cycle + 1;
                end
                if (read_cycle[0]) begin
                    buffered_rdata <= rdata;
                end
                if (read_finishing) begin
                    read_cycle <= 0;
                end
            end
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            write_cycle <= 0;
        end else begin
            if (femto_wstrb || write_in_progress) begin
                write_cycle <= write_cycle + 1;
                if (write_finishing) begin
                    write_cycle <= 0;
                end
            end
        end
    end

    wire addr1 = femto_half ? femto_addr[1] : (read_cycle[1] | write_cycle[1]);
    assign addr = {femto_addr[31:2], addr1, 1'b0};
    assign msk_n = addr1 ? ~femto_mask[3:2] : ~femto_mask[1:0];

    assign data_out = addr1 ? femto_wdata[31:16] : femto_wdata[15:0];
    assign data_oe = write_cycle[0];

    assign iorq_n = !addr[31];
    assign mreq_n[0] = !(femto_rstrb || (read_cycle == 2'b10) || 
                         femto_wnext || femto_wstrb || (write_in_progress && !write_finishing));
    assign mreq_n[1] = !(femto_rstrb || read_in_progress || 
                         femto_wstrb || (write_cycle == 2'b10));

    rv4028_rom i_rom(
        .clk(clk),
        .ren(1'b1),
        .addr(addr[12:1]),
        .data_out(rom_data)
    );

    wire unused = &{1'b0, femto_addr[0], int_n};

endmodule
