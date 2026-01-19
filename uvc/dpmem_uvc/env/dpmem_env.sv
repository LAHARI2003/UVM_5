// This is the dpmem_env class instantiating the
// dpmem_agent class.
class dpmem_env #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_env;

  // Agent instance
  dpmem_agent#(DATA_WIDTH,ADDR_WIDTH) m_agent;

  `uvm_component_utils(dpmem_env#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Create the agent
    m_agent = dpmem_agent#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("m_agent", this);
  endfunction

  // Add connect_phase or other phases as needed

endclass
