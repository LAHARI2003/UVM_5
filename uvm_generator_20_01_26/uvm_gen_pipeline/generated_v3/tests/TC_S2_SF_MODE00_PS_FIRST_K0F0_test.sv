// TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv
//
// UVM test for TC_S2_SF_MODE00_PS_FIRST_K0F0
// - Environment: dimc_tile_wrapper_env
// - Virtual sequence: TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq
// - Virtual interface: dimc_tile_wrapper_if
//

class TC_S2_SF_MODE00_PS_FIRST_K0F0_test extends uvm_test;

  `uvm_component_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_test)

  dimc_tile_wrapper_env env;
  TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq vseq;

  // Virtual interface
  virtual dimc_tile_wrapper_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    env = dimc_tile_wrapper_env::type_id::create("env", this);

    // Create virtual sequence instance
    vseq = TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq::type_id::create("vseq", this);

    // Get virtual interface from config_db
    if (!uvm_config_db#(virtual dimc_tile_wrapper_if)::get(this, "", "dimc_tile_wrapper_m_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface must be set for dimc_tile_wrapper_m")
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // Connect sequencers if needed
  endfunction

  task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    // Wait for reset deassertion
    wait (vif.resetn == 1'b1);
    repeat (5) @(vif.clk);

    // Start the virtual sequence on the environment's virtual sequencer
    vseq.start(env.v_seqr);

    repeat (10) @(vif.clk);

    phase.drop_objection(this);
  endtask

endclass