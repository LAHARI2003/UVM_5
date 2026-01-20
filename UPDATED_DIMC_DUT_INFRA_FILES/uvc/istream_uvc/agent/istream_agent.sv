// Agent class
// This is the istream_agent class instantiating the istream_driver, istream_sequencer
// it connects the vif interrface to the istream_vif interface
// instantiated in the testbench
class istream_agent #(int DATA_WIDTH=32) extends uvm_agent;

  // Components
  istream_sequencer#(DATA_WIDTH)        m_sequencer;
  istream_driver#(DATA_WIDTH)           m_driver;
  istream_monitor#(DATA_WIDTH)          m_monitor;

  // Virtual interface
  virtual istream_if#(DATA_WIDTH) vif;

  `uvm_component_utils(istream_agent#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Get virtual interface from config_db
    //if (!uvm_config_db#(virtual istream_if#(DATA_WIDTH))::get(this, "*", "feature_buffer_vif", vif))
     // `uvm_fatal("NOVIF", "Virtual interface must be set for istream_agent")

    // Instantiate sequencer and driver
    m_sequencer = istream_sequencer#(DATA_WIDTH)::type_id::create("m_sequencer", this);
    m_driver    = istream_driver#(DATA_WIDTH)::type_id::create("m_driver", this);
    m_monitor   = istream_monitor#(DATA_WIDTH)::type_id::create("m_monitor", this);

    // Pass the interface to the driver via config_db
    //uvm_config_db#(virtual feature_buffer_if)::set(this, "m_driver", "vif", vif);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Connect driver and sequencer
    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);
   // m_driver.vif = vif;
  endfunction

endclass
