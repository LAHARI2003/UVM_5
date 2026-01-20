// computation_sequencer declaration which drives the computation_seq_item
// to the computation_driver
class computation_sequencer extends uvm_sequencer #(computation_seq_item);

  `uvm_component_utils(computation_sequencer)

  function new(string name = "computation_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction

endclass
