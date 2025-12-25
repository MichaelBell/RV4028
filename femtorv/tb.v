
/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
*/

`default_nettype none

module tb ();

    wire clk;
    wire rst_n;
    wire [31:0] addr;
    wire wr_n;
    wire rd_n;
    wire [1:0] msk_n;
    wire wait_n;
    wire [15:0] data_in;
    wire [15:0] data_out;
    wire data_oe;

    wire iorq_n;
    wire mreq_n;
    wire int_n;
    wire busrq_n;
    wire busack_n;

    wire [1:0] mreq_buf;
    wire [1:0] wr_buf;

    RV4028_femtorv i_rv4028 (
        .clk(clk),
        .rst_n(rst_n),
        .addr(addr),
        .wr_n(wr_buf),
        .rd_n(rd_n),
        .msk_n(msk_n),
        .iorq_n(iorq_n),
        .mreq_n(mreq_buf),
        .wait_n(wait_n),
        .int_n(int_n),
        .busrq_n(busrq_n),
        .busack_n(busack_n),
        .data_in(data_in),
        .data_out(data_out),
        .data_oe(data_oe)
    );

    // Implementation of the ICE40 DDR outputs
    reg [1:0] mreq_buf_r;
    reg [1:0] wr_buf_r;

    always @(posedge clk) begin
        mreq_buf_r[0] <= mreq_buf[0];
        wr_buf_r[0] <= wr_buf[0];
    end
    always @(negedge clk) begin
        mreq_buf_r[1] <= mreq_buf[1];
        wr_buf_r[1] <= wr_buf[1];
    end

    assign mreq_n = clk ? mreq_buf_r[0] : mreq_buf_r[1];
    assign wr_n   = clk ? wr_buf_r[0]   : wr_buf_r[1];

endmodule
