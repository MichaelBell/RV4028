
/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
*/
module tb ();

    wire clk;
    wire rst_n;
    wire [31:0] addr;
    wire wr_n;
    wire rd_n;
    wire [1:0] wrm_n;
    wire wait_n;
    wire [15:0] data;

    wire iorq_n;
    wire mreq_n;
    wire int_n;

    RV4028_femtorv i_top (
        .clk(clk),
        .rst_n(rst_n),
        .addr(addr),
        .wr_n(wr_n),
        .rd_n(rd_n),
        .wrm_n(wrm_n),
        .iorq_n(iorq_n),
        .mreq_n(mreq_n),
        .wait_n(wait_n),
        .int_n(int_n),
        .data(data)
    );

endmodule
