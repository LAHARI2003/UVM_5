// This is the ostream_env class instantiating the
// ostream_agent class.
class ostream_env #(int DATA_WIDTH = 32) extends uvm_env;

  // Agent instance
  ostream_agent#(DATA_WIDTH) m_agent;

  `uvm_component_utils(ostream_env#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Create the agent
    m_agent = ostream_agent#(DATA_WIDTH)::type_id::create("m_agent", this);
  endfunction

  // Add connect_phase or other phases as needed

endclass
