class TC_S2_SF_MODE00_PS_FIRST_K0F0_test extends uvm_test;

  `uvm_component_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_test)

  dimc_tile_wrapper_env env;
  TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq vseq;

  // Virtual interface
  virtual dimc_tilewrap_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = dimc_tile_wrapper_env::type_id::create("env", this);

    // Create and start the virtual sequence
    vseq = TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq::type_id::create("vseq", this);

    // Get virtual interface from config_db
    if (!uvm_config_db#(virtual dimc_tilewrap_if)::get(this, "", "dimc_tilewrap_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for dimc_tile_wrapper_env")
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // Connect sequencers if needed
  endfunction

  task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // Wait for reset deassertion
    wait (vif.resetn == 1);
    repeat(5) @(vif.cb);

    // Start the virtual sequence
    vseq.start(env.v_seqr);

    repeat(10) @(vif.cb);

    phase.drop_objection(this);
  endtask

endclass