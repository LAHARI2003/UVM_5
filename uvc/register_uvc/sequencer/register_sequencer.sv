// register_sequencer declaration which drives the register_seq_item
// to the register_driver
class register_sequencer extends uvm_sequencer #(register_seq_item);

  `uvm_component_utils(register_sequencer)

  function new(string name = "register_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction

endclass
