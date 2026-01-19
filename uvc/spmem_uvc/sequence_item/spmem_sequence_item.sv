// spmem_seq_item fields
// spmem_seq_item fields driven by the driver to spmem_if interface
//
//// spmem_cs_n - Active-low chip select signal for the Addin buffer.
// spmem_addr - Address bus for selecting Addin buffer location.
// spmem_wr_n - Active-low write enable signal for the Addin buffer.
// spmem_be - Byte enable signals for Addin buffer data input. Determines which bytes are valid for writing.
// spmem_d - Data input bus for the Addin buffer (64-bit).
// spmem_q - Output data from the Addin buffer (64-bit).

class spmem_seq_item #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence_item;

  bit spmem_cs_n;
  bit [ADDR_WIDTH-1:0] spmem_addr;
  bit spmem_wr_n;
  bit [DATA_WIDTH-1:0] spmem_be;
  bit [DATA_WIDTH-1:0] spmem_d;
  bit [DATA_WIDTH-1:0] spmem_q; // sampled during read

  `uvm_object_utils(spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "spmem_seq_item");
    super.new(name);
  endfunction

  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field("spmem_cs_n", spmem_cs_n, 1);
    printer.print_field("spmem_addr", spmem_addr, ADDR_WIDTH);
    printer.print_field("spmem_wr_n", spmem_wr_n, 1);
    printer.print_field("spmem_be", spmem_be, DATA_WIDTH);
    printer.print_field("spmem_d", spmem_d, DATA_WIDTH);
    printer.print_field("spmem_q", spmem_q, DATA_WIDTH);
  endfunction

endclass
