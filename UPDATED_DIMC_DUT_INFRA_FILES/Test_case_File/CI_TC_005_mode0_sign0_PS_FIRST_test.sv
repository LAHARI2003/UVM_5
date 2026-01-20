
class CI_TC_005_mode0_sign0_PS_FIRST_test extends uvm_test;

  `uvm_component_utils(CI_TC_005_mode0_sign0_PS_FIRST_test)

  p18_dimc_tile_wrap_env env;
  CI_TC_005_mode0_sign0_PS_FIRST_vseq vseq_compu;

  // Virtual interface
  virtual dimc_tilewrap_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = p18_dimc_tile_wrap_env::type_id::create("env", this);

    // Create and start the default sequence
    vseq_compu = CI_TC_005_mode0_sign0_PS_FIRST_vseq::type_id::create($sformatf("vseq_compu_mode%02x_sign%02x", 0, 0), this);

    // Get virtual interface from config_db
    if (!uvm_config_db#(virtual dimc_tilewrap_if)::get(this, "", "dimc_tilewrap_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for feature_buffer_agent")
  endfunction

  task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    wait (vif.resetn == 1);
    repeat(5) @(vif.cb);

    vseq_compu.start(env.v_seqr);

    repeat(10) @(vif.cb);

    phase.drop_objection(this);
  endtask

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // Connect sequencers if needed
  endfunction

endclass
