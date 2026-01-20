class dimc_tile_wrapper_env extends uvm_env;

  // Sub-environment instances
  istream_env#(64) m_feature_buffer_env;
  virtual istream_if#(64) feature_buffer_vif;

  istream_env#(32) m_psin_env;
  virtual istream_if#(32) psin_vif;

  dpmem_env#(64,9) m_kernel_mem_env;
  virtual dpmem_if#(64,9) kernel_mem_vif;

  spmem_env#(64,4) m_addin_env;
  virtual spmem_if#(64,4) addin_vif;

  regbank_env m_computation_env;
  virtual regbank_if computation_vif;

  ostream_env#(64) m_output_buffer_env;
  virtual ostream_if#(64) output_buffer_vif;

  // Virtual sequencer
  dimc_tile_wrapper_virtual_sequencer v_seqr;

  // Scoreboard
  // Assuming a scoreboard is needed, adjust as per actual verification plan
  dimc_tile_wrapper_scoreboard scoreboard;

  `uvm_component_utils(dimc_tile_wrapper_env)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Create sub-environments
    m_feature_buffer_env = istream_env#(64)::type_id::create("m_feature_buffer_env", this);
    m_psin_env = istream_env#(32)::type_id::create("m_psin_env", this);
    m_kernel_mem_env = dpmem_env#(64,9)::type_id::create("m_kernel_mem_env", this);
    m_addin_env = spmem_env#(64,4)::type_id::create("m_addin_env", this);
    m_computation_env = regbank_env::type_id::create("m_computation_env", this);
    m_output_buffer_env = ostream_env#(64)::type_id::create("m_output_buffer_env", this);

    v_seqr = dimc_tile_wrapper_virtual_sequencer::type_id::create("v_seqr", this);
    scoreboard = dimc_tile_wrapper_scoreboard::type_id::create("scoreboard", this);

    // Get virtual interfaces from config_db
    if (!uvm_config_db#(virtual istream_if#(64))::get(this, "*", "feature_buffer_vif", feature_buffer_vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for feature_buffer_vif")
    if (!uvm_config_db#(virtual istream_if#(32))::get(this, "*", "psin_vif", psin_vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for psin_vif")
    if (!uvm_config_db#(virtual dpmem_if#(64,9))::get(this, "*", "kernel_mem_vif", kernel_mem_vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for kernel_mem_vif")
    if (!uvm_config_db#(virtual spmem_if#(64,4))::get(this, "*", "addin_vif", addin_vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for addin_vif")
    if (!uvm_config_db#(virtual ostream_if#(64))::get(this, "*", "output_buffer_vif", output_buffer_vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for output_buffer_vif")
    if (!uvm_config_db#(virtual regbank_if)::get(this, "*", "computation_vif", computation_vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for computation_vif")
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Connect sequencers to virtual sequencer
    v_seqr.seqr_feature_buffer = m_feature_buffer_env.m_agent.m_sequencer;
    v_seqr.seqr_psin = m_psin_env.m_agent.m_sequencer;
    v_seqr.seqr_kernel_mem = m_kernel_mem_env.m_agent.m_sequencer;
    v_seqr.seqr_addin = m_addin_env.m_agent.m_sequencer;
    v_seqr.seqr_output_buffer = m_output_buffer_env.m_agent.m_sequencer;
    v_seqr.seqr_computation = m_computation_env.m_agent.m_sequencer;

    // Connect interfaces to agents and drivers
    m_feature_buffer_env.m_agent.vif = feature_buffer_vif;
    m_psin_env.m_agent.vif = psin_vif;
    m_kernel_mem_env.m_agent.vif = kernel_mem_vif;
    m_addin_env.m_agent.vif = addin_vif;
    m_output_buffer_env.m_agent.vif = output_buffer_vif;
    m_computation_env.m_agent.vif = computation_vif;

    // Connect monitor analysis ports to scoreboard
    m_feature_buffer_env.m_agent.m_monitor.analysis_port.connect(scoreboard.analysis_export);
    m_psin_env.m_agent.m_monitor.analysis_port.connect(scoreboard.analysis_export);
    m_kernel_mem_env.m_agent.m_monitor.analysis_port.connect(scoreboard.analysis_export);
    m_addin_env.m_agent.m_monitor.analysis_port.connect(scoreboard.analysis_export);
    m_output_buffer_env.m_agent.m_monitor.analysis_port.connect(scoreboard.analysis_export);
    m_computation_env.m_agent.m_monitor.analysis_port.connect(scoreboard.analysis_export);
  endfunction

endclass