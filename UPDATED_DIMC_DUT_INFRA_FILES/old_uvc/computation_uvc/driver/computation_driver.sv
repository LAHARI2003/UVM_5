// computation_driver which gets computation_seq_item from the
// computation_sequencer and drives it to the computation_vif interface
// signals
class computation_driver extends uvm_driver #(computation_seq_item);

  virtual computation_if vif;

  `uvm_component_utils(computation_driver)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual computation_if)::get(this, "", "computation_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for computation_driver")
  endfunction

  task run_phase(uvm_phase phase);
    computation_seq_item req;

    forever begin
      seq_item_port.get_next_item(req);

      @(posedge vif.computation_clk);

      vif.cb.K_DIM         <= req.K_DIM;
      vif.cb.START_COMPUTE <= req.START_COMPUTE;
      vif.cb.COMPE         <= req.COMPE;
      vif.cb.PS_FIRST      <= req.PS_FIRST;
      vif.cb.PS_MODE       <= req.PS_MODE;
      vif.cb.PS_LAST       <= req.PS_LAST;
      vif.cb.MODE          <= req.MODE;
      vif.cb.sign_8b       <= req.sign_8b;
      vif.cb.CONT_COMP     <= req.CONT_COMP;
      vif.cb.iteration     <= req.iteration;

      // Optionally, hold signals for one clock cycle
      @(posedge vif.computation_clk);

      // Optionally, de-assert outputs here if protocol requires

      seq_item_port.item_done();
    end
  endtask

endclass
