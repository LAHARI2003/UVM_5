// This is the register_env class instantiating the
// register_agent class.
class register_env extends uvm_env;

  // Agent instance
  register_agent m_agent;

  `uvm_component_utils(register_env)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Create the agent
    m_agent = register_agent::type_id::create("m_agent", this);
  endfunction

  // Add connect_phase or other phases as needed

endclass
