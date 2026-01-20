// Agent class
// This is the computation_agent class instantiating the computation_sequencer, computation_driver
// it connects the vif interface to the computation_vif interface
// instantiated in the testbench
class computation_agent extends uvm_agent;

  // Components
  computation_sequencer m_sequencer;
  computation_driver    m_driver;

  // Virtual interface
  virtual computation_if vif;

  `uvm_component_utils(computation_agent)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Get virtual interface from config_db
    if (!uvm_config_db#(virtual computation_if)::get(this, "", "computation_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for computation_agent")

    // Instantiate sequencer and driver
    m_sequencer = computation_sequencer::type_id::create("m_sequencer", this);
    m_driver    = computation_driver::type_id::create("m_driver", this);

    // Pass the interface to the driver via config_db
    uvm_config_db#(virtual computation_if)::set(this, "m_driver", "computation_vif", vif);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Connect driver and sequencer
    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);
  endfunction

endclass
