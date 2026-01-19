// istream_seq_item fields
// istream_valid - Indicates that the input feature data is valid and ready to be consumed.
// istream_data - Input feature data bus carrying 64-bit feature data.
// istream_seq_item fields driven by the driver to feature_buffer_if interface
// signals

import uvm_pkg::*;
`include "uvm_macros.svh"

class istream_seq_item #(int DATA_WIDTH = 32 ) extends uvm_sequence_item;
  rand bit istream_valid;
  bit istream_ready;
  //rand bit [63:0] feat_data;
  rand bit [DATA_WIDTH-1:0] istream_data;

  `uvm_object_utils(istream_seq_item#(DATA_WIDTH))
  //`uvm_param_utils(istream_seq_item#(DATA_WIDTH))

  function new(string name = "istream_seq_item");
    super.new(name);
  endfunction

  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field("istream_valid", istream_valid, 1);
    printer.print_field("istream_ready", istream_ready, 1);
    printer.print_field("istream_data", istream_data, DATA_WIDTH);
  endfunction

  // Optional: constraints can be added here if needed
endclass
