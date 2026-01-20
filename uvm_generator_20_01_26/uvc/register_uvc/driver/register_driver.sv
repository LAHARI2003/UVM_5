// register_driver which gets register_seq_item from the
// register_sequencer and drives it to the register_vif interface
// signals
class register_driver extends uvm_driver #(register_seq_item);

  virtual register_if vif;

  `uvm_component_utils(register_driver)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
  endfunction

  task run_phase(uvm_phase phase);
    register_seq_item req;

    forever begin
      seq_item_port.get_next_item(req);

      @(posedge vif.register_clk);

      vif.register         <= req.register;

      // Optionally, hold signals for one clock cycle
      @(posedge vif.register_clk);

      // Optionally, de-assert outputs here if protocol requires

      seq_item_port.item_done();
    end
  endtask

endclass
