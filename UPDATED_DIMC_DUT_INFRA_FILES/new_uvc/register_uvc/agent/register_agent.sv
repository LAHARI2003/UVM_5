// Agent class
// This is the register_agent class instantiating the register_sequencer, register_driver
// it connects the vif interface to the register_vif interface
// instantiated in the testbench
class register_agent extends uvm_agent;

  // Components
  register_sequencer m_sequencer;
  register_driver    m_driver;

  // Virtual interface
  virtual register_if vif;

  `uvm_component_utils(register_agent)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Instantiate sequencer and driver
    m_sequencer = register_sequencer::type_id::create("m_sequencer", this);
    m_driver    = register_driver::type_id::create("m_driver", this);

  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Connect driver and sequencer
    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);
  endfunction

endclass
