// Agent class
// This is the dpmem_agent class instantiating the dpmem_sequencer, dpmem_driver
// it connects the vif interface to the dpmem_vif interface
// instantiated in the testbench
class dpmem_agent #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_agent;

  // Components
  dpmem_sequencer#(DATA_WIDTH,ADDR_WIDTH) m_sequencer;
  dpmem_driver#(DATA_WIDTH,ADDR_WIDTH)    m_driver;

  // Virtual interface
  virtual dpmem_if#(DATA_WIDTH,ADDR_WIDTH) vif;

  `uvm_component_utils(dpmem_agent#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Get virtual interface from config_db
    //if (!uvm_config_db#(virtual dpmem_if)::get(this, "", "dpmem_vif", vif))
      //`uvm_fatal("NOVIF", "Virtual interface must be set for dpmem_agent")

    // Instantiate sequencer and driver
    m_sequencer = dpmem_sequencer#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("m_sequencer", this);
    m_driver    = dpmem_driver#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("m_driver", this);

    // Pass the interface to the driver via config_db
    //uvm_config_db#(virtual dpmem_if)::set(this, "m_driver", "vif", vif);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Connect driver and sequencer
    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);
  endfunction

endclass
