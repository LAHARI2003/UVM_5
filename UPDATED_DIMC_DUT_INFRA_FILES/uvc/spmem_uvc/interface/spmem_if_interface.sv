// spmem_if interface which gets instantiated in testbench and gets
// connected with the DUT input and output
//
// spmem_cs_n - Active-low chip select signal for the spmem buffer.
// spmem_addr - Address bus for selecting spmem location.
// spmem_wr_n - Active-low write enable signal for the spmem buffer.
// spmem_be - Byte enable signals for spmem data input. Determines which bytes are valid for writing.
// spmem_d - Data input bus for the spmem buffer (64-bit).
// spmem_q - Output data from the spmem buffer (64-bit).


interface spmem_if #(int DATA_WIDTH=32, int ADDR_WIDTH=32) (input logic spmem_clk);

  logic spmem_cs_n;
  logic [ADDR_WIDTH-1:0] spmem_addr;
  logic spmem_wr_n;
  logic [DATA_WIDTH-1:0] spmem_be;
  logic [DATA_WIDTH-1:0] spmem_d;
  logic [DATA_WIDTH-1:0] spmem_q;

  // Clocking block for synchronous access
  clocking cb @(posedge spmem_clk);
    output spmem_cs_n, spmem_addr, spmem_wr_n, spmem_be, spmem_d;
    input spmem_q;
  endclocking

  initial// spmem_cs_n - Active-low chip select signal for the Addin buffer.
// spmem_addr - Address bus for selecting Addin buffer location.
// spmem_wr_n - Active-low write enable signal for the Addin buffer.
// spmem_be - Byte enable signals for Addin buffer data input. Determines which bytes are valid for writing.
// spmem_d - Data input bus for the Addin buffer (64-bit).
// spmem_q - Output data from the Addin buffer (64-bit).

   begin
      spmem_cs_n = 1'b1;
      spmem_addr = '0;
      spmem_wr_n = 1'b1;
      spmem_be = '0;
      spmem_d = '0;
   end

endinterface
