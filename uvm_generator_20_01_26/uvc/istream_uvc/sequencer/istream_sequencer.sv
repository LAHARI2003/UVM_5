// istream_uvc sequencer declaration which drives the feature_seq_item
// to the featuer_driver

// Import U// Import UVM and your sequence item
//import uvm_pkg::*;
//`include "uvm_macros.svh"
//`include "feature_seq_item.sv"

class istream_sequencer #(int DATA_WIDTH = 32) extends uvm_sequencer #(istream_seq_item #(DATA_WIDTH));

  `uvm_component_utils(istream_sequencer#(DATA_WIDTH))
  //`uvm_param_utils(istream_sequencer#(DATA_WIDTH))

  function new(string name = "istream_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction

endclass
