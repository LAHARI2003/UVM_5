// Agent class
// This is the ostream_agent class instantiating the ostream_sequencer, ostream_driver
// it connects the vif interface to the ostream_vif interface
// instantiated in the testbench
class ostream_agent #(int DATA_WIDTH = 32) extends uvm_agent;

  // Components
  ostream_sequencer#(DATA_WIDTH) m_sequencer;
  ostream_driver#(DATA_WIDTH)    m_driver;
  ostream_monitor#(DATA_WIDTH)   m_monitor;

  // Virtual interface
  virtual ostream_if#(DATA_WIDTH) vif;

  `uvm_component_utils(ostream_agent#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Get virtual interface from config_db
    //if (!uvm_config_db#(virtual ostream_if#(DATA_WIDTH))::get(this, "", "ostream_vif", vif))
      //`uvm_fatal("NOVIF", "Virtual interface must be set for ostream_agent")

    // Instantiate sequencer and driver
    m_sequencer = ostream_sequencer#(DATA_WIDTH)::type_id::create("m_sequencer", this);
    m_driver    = ostream_driver#(DATA_WIDTH)::type_id::create("m_driver", this);
    m_monitor    = ostream_monitor#(DATA_WIDTH)::type_id::create("m_monitor", this);

    // Pass the interface to the driver via config_db
    //uvm_config_db#(virtual ostream_if)::set(this, "m_driver", "ostream_vif", vif);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Connect driver and sequencer
    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);
  endfunction

endclass
