class TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq extends uvm_sequence;

  `uvm_object_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq)
  `uvm_declare_p_sequencer(p18_dimc_tile_wrap_virtual_sequencer)

  dpmem_directed_write_sequence#(64,9)  seq_ker_wr;
  istream_directed_write_sequence#(64)  seq_feat_wr;
  spmem_directed_write_sequence#(64,4) seq_addin_wr;
  register_configure_write_seq          seq_register_wr;
  ostream_random_burst_read_sequence#(64) seq_outbuf_rd;
  
  int mode;
  int sign_8b; // dont_care in this context
  int PS_FIRST;
  int PS_MODE;
  int PS_LAST;

  function new(string name = "TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq");
    super.new(name);
  endfunction

  function int pack_register(
    int k_dim = 0,
    int start_compute = 0,
    int compe = 0,
    int ps_first = 0,
    int ps_mode = 0,
    int ps_last = 0,
    int mode_val = 0,
    int sign_8b_val = 0, // dont_care, not used in this context
    int cont_comp = 0,
    int iteration = 0
  );
    int reg_val;
    reg_val = 0;
    reg_val = reg_val | (k_dim & 6'h3F);
    reg_val = reg_val | ((start_compute & 1'b1) << 6);
    reg_val = reg_val | ((compe & 1'b1) << 7);
    reg_val = reg_val | ((ps_first & 1'b1) << 8);
    reg_val = reg_val | ((ps_mode & 1'b1) << 9);
    reg_val = reg_val | ((ps_last & 1'b1) << 10);
    reg_val = reg_val | ((mode_val & 2'b11) << 11);
    // sign_8b_val is dont_care, not explicitly set
    reg_val = reg_val | ((cont_comp & 1'b1) << 15);
    reg_val = reg_val | ((iteration & 8'hFF) << 16);
    return reg_val;
  endfunction

  task body();
    // Set parameters for this specific test case
    mode = 0; // MODE = 00
    PS_FIRST = 1;
    PS_MODE = 0;
    PS_LAST = 0;

    // Kernel memory write with all-zero pattern
    seq_ker_wr = dpmem_directed_write_sequence#(64,9)::type_id::create("seq_ker_wr");
    seq_ker_wr.pattern = BIN_K_ALL0;
    seq_ker_wr.start(p_sequencer.seqr_kernel_mem);

    // Feature buffer write with all-zero pattern
    seq_feat_wr = istream_directed_write_sequence#(64)::type_id::create("seq_feat_wr");
    seq_feat_wr.pattern = BIN_F_ALL0;
    seq_feat_wr.start(p_sequencer.seqr_feature_buffer);

    // Addin memory write with zeros (not used in PS_FIRST; keeps default consistent)
    seq_addin_wr = spmem_directed_write_sequence#(64,4)::type_id::create("seq_addin_wr");
    seq_addin_wr.pattern = BIN_ADDIN_0;
    seq_addin_wr.start(p_sequencer.seqr_addin);

    // Initialization Register sequence
    seq_register_wr = register_configure_write_seq::type_id::create("seq_register_wr");
    seq_register_wr.register = pack_register(
      .ps_first(PS_FIRST),
      .ps_mode(PS_MODE),
      .ps_last(PS_LAST),
      .mode_val(mode)
    );
    seq_register_wr.start(p_sequencer.seqr_register);

    // Start compute
    seq_register_wr = register_configure_write_seq::type_id::create("seq_register_wr");
    seq_register_wr.register = pack_register(
      .start_compute(1),
      .compe(1),
      .ps_first(PS_FIRST),
      .ps_mode(PS_MODE),
      .ps_last(PS_LAST),
      .mode_val(mode)
    );
    seq_register_wr.start(p_sequencer.seqr_register);

    // Wait for computation to complete
    wait_for_completion();

    // Output buffer read sequence
    seq_outbuf_rd = ostream_random_burst_read_sequence#(64)::type_id::create("seq_outbuf_rd");
    seq_outbuf_rd.start(p_sequencer.seqr_output_buffer);

    // Cleanup
    cleanup_files();
  endtask

  task wait_for_completion();
    // Implement polling of status signals to determine when computation is complete
  endtask

  task cleanup_files();
    // Implement file cleanup operations
  endtask

endclass