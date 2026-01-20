// This is the computation_env class instantiating the
// computation_agent class.
class computation_env extends uvm_env;

  // Agent instance
  computation_agent m_agent;

  `uvm_component_utils(computation_env)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Create the agent
    m_agent = computation_agent::type_id::create("m_agent", this);
  endfunction

  // Add connect_phase or other phases as needed

endclass
