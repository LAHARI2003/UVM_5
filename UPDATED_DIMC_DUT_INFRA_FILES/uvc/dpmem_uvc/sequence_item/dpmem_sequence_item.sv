// dpmem_seq_item fields
// dpmem_seq_item fields driven by the driver to dpmem_if interface
// WCSN - Write chip select (active low) for kernel memory.
// WA - Write address bus for kernel memory.
// WEN - Write enable for kernel memory.
// RCSN - Read chip select (active low) for kernel memory.
//  RA - Read address bus for kernel memory.
//  M - Mask or modifier input for kernel memory data operations.
//  D - Input data bus to kernel memory (64-bit).
//  Q - Output data bus from kernel memory (64-bit).

// signals

class dpmem_seq_item #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence_item;

  // Write signals
  bit WCSN;
  bit [ADDR_WIDTH-1:0] WA;
  bit WEN;
  // Read signals
  bit RCSN;
  bit [ADDR_WIDTH-1:0] RA;

  bit [DATA_WIDTH-1:0] M;
  bit [DATA_WIDTH-1:0] D;
  bit [DATA_WIDTH-1:0] Q; // sampled during read

  bit sample_read_data; // whether to sample Q during read

  `uvm_object_utils(dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "dpmem_seq_item");
    super.new(name);
    sample_read_data = 1; // default sample read data
  endfunction

  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field("WCSN", WCSN, 1);
    printer.print_field("WEN", WEN, 1);
    printer.print_field("WA", WA, ADDR_WIDTH);
    printer.print_field("RCSN", RCSN, 1);
    printer.print_field("RA", RA, ADDR_WIDTH);
    printer.print_field("M", M, DATA_WIDTH);
    printer.print_field("D", D, DATA_WIDTH);
    printer.print_field("Q", Q, DATA_WIDTH);
    printer.print_field("sample_read_data", sample_read_data, 1);
  endfunction

endclass
