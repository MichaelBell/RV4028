/* Copyright 2023-2024 (c) Michael Bell
   SPDX-License-Identifier: BSD-3-Clause
   
   ROM module for RV4028 CPU */

`default_nettype none

module rv2048_rom(
    input clk,
    input ren,
    input [11:1] addr,

    output reg [15:0] data_out
);

    parameter INIT_FILE = "rom.hex";

    reg [15:0] rom [0:2047];
    initial begin
        $readmemh(INIT_FILE, rom);
    end

    always @(posedge clk) begin
        if (ren) begin
            data_out <= rom[addr];
        end
    end

endmodule
