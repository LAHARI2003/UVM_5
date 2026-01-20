// spmem_sequencer declaration which drives the spmem_seq_item
// to the spmem_driver
class spmem_sequencer #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequencer #(spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_component_utils(spmem_sequencer#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "spmem_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction

endclass
