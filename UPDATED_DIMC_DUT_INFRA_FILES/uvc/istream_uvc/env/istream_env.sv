// This is the istream_env class instantiating the
// istream_agent class. 
class istream_env #(int DATA_WIDTH = 32) extends uvm_env;

  // Agent instance
  istream_agent#(DATA_WIDTH) m_agent;

  `uvm_component_utils(istream_env#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Create the agent
    m_agent = istream_agent#(DATA_WIDTH)::type_id::create("m_agent", this);
  endfunction

  // Add connect_phase or other phases as needed

endclass
