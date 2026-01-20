// dpmem_uvc sequencer declaration which drives the dpmem_seq_item
// to the dpmem_driver
class dpmem_sequencer#(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequencer #(dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_component_utils(dpmem_sequencer#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "dpmem_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction

endclass
