// TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv
// Virtual sequence for test case: TC_S2_SF_MODE00_PS_FIRST_K0F0

class TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq extends uvm_sequence;

  `uvm_object_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq)
  `uvm_declare_p_sequencer(p18_dimc_tile_wrap_virtual_sequencer)

  // Sub-sequence handles
  register_configure_write_seq                  seq_register_wr;
  dpmem_directed_write_sequence#(64,9)          seq_ker_wr;
  istream_directed_write_sequence#(64)          seq_feat_wr;
  spmem_directed_write_sequence#(64,4)          seq_addin_wr;
  ostream_random_burst_read_sequence#(64)       seq_outbuf_rd;

  // Test parameters
  int mode;
  int sign_8b;
  int PS_FIRST;
  int PS_MODE;
  int PS_LAST;
  int K_DIM;
  int CONT_COMP;
  int iteration;

  // Helper function to pack computation parameters into 32-bit register
  // Register bit mapping:
  // register[5:0]   = K_DIM
  // register[6]     = START_COMPUTE
  // register[7]     = COMPE
  // register[8]     = PS_FIRST
  // register[9]     = PS_MODE
  // register[10]    = PS_LAST
  // register[12:11] = MODE
  // register[14:13] = sign_8b
  // register[15]    = CONT_COMP
  // register[23:16] = iteration
  function int pack_register(
    int k_dim = 0,
    int start_compute = 0,
    int compe = 0,
    int ps_first = 0,
    int ps_mode = 0,
    int ps_last = 0,
    int mode_val = 0,
    int sign_8b_val = 0,
    int cont_comp = 0,
    int iteration_val = 0
  );
    int reg_val;
    reg_val = 0;
    reg_val = reg_val | (k_dim & 6'h3F);                    // bits [5:0]
    reg_val = reg_val | ((start_compute & 1'b1) << 6);      // bit [6]
    reg_val = reg_val | ((compe & 1'b1) << 7);              // bit [7]
    reg_val = reg_val | ((ps_first & 1'b1) << 8);           // bit [8]
    reg_val = reg_val | ((ps_mode & 1'b1) << 9);            // bit [9]
    reg_val = reg_val | ((ps_last & 1'b1) << 10);           // bit [10]
    reg_val = reg_val | ((mode_val & 2'b11) << 11);         // bits [12:11]
    reg_val = reg_val | ((sign_8b_val & 2'b11) << 13);      // bits [14:13]
    reg_val = reg_val | ((cont_comp & 1'b1) << 15);         // bit [15]
    reg_val = reg_val | ((iteration_val & 8'hFF) << 16);    // bits [23:16]
    return reg_val;
  endfunction

  function new(string name = "TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq");
    super.new(name);
  endfunction

  task body();
    int feat_status;
    int ker_status;
    int addin_status;
    int cmodel_status;
    int repeat_count = 1;

    // Set test parameters
    mode      = 0; // MODE = 00
    sign_8b   = 0; // don't care for this test, set to 0
    PS_FIRST  = 1;
    PS_MODE   = 0;
    PS_LAST   = 0;
    K_DIM     = 0;
    CONT_COMP = 0;
    iteration = 0;

    // Generate all-zero kernel data
    ker_status = $system("python generate_data_kernel.py --pattern BIN_K_ALL0 > kernel_hex.txt");
    if (ker_status != 0) begin
      `uvm_error("Vseq", "Failed to generate all-zero kernel data")
      return;
    end

    // Generate all-zero feature data
    feat_status = $system("python generate_data_feature.py --pattern BIN_F_ALL0 > feature_hex.txt");
    if (feat_status != 0) begin
      `uvm_error("Vseq", "Failed to generate all-zero feature data")
      return;
    end

    // Generate all-zero addin data
    addin_status = $system("python generate_data_addin.py --pattern BIN_ADDIN_0 > addin_hex.txt");
    if (addin_status != 0) begin
      `uvm_error("Vseq", "Failed to generate all-zero addin data")
      return;
    end

    // Run C model to generate expected output
    cmodel_status = $system($sformatf("./psout_exe kernel_hex.txt feature_hex.txt psin_hex.txt addin_hex.txt output_buffer_expected_out.txt %02b %02b %01b %01b %01b > result_cmodel.txt",
                                      mode, sign_8b, PS_FIRST, PS_MODE, PS_LAST));
    if (cmodel_status != 0) begin
      `uvm_error("Vseq", "Failed to run C model executable")
      return;
    end

    // Configure capture signals on virtual interface
    p_sequencer.vif.capture_output_buffer_exp_data = 1'b0;
    @(posedge p_sequencer.vif.dimc_tilewrap_clk);

    p_sequencer.vif.capture_output_buffer_exp_data = 1'b1;
    p_sequencer.vif.output_buffer_exp_data_size = 32;
    @(posedge p_sequencer.vif.dimc_tilewrap_clk);
    p_sequencer.vif.capture_output_buffer_exp_data = 1'b0;

    // Initialization register sequence (START_COMPUTE=0, COMPE=0)
    seq_register_wr = register_configure_write_seq::type_id::create("seq_register_wr_init");
    seq_register_wr.register = pack_register(
      .k_dim(K_DIM),
      .start_compute(0),
      .compe(0),
      .ps_first(PS_FIRST),
      .ps_mode(PS_MODE),
      .ps_last(PS_LAST),
      .mode_val(mode),
      .sign_8b_val(sign_8b),
      .cont_comp(CONT_COMP),
      .iteration_val(iteration)
    );
    seq_register_wr.start(p_sequencer.seqr_register);

    // Write all-zero feature data to feature buffer
    seq_feat_wr = istream_directed_write_sequence#(64)::type_id::create("seq_feat_wr");
    seq_feat_wr.size = 16;
    seq_feat_wr.file_path = "./feature_hex.txt";
    seq_feat_wr.start(p_sequencer.seqr_feature_buffer);

    // Write all-zero kernel data to kernel memory
    seq_ker_wr = dpmem_directed_write_sequence#(64,9)::type_id::create("seq_ker_wr");
    seq_ker_wr.size = 512;
    seq_ker_wr.file_path = "./kernel_hex.txt";
    seq_ker_wr.start(p_sequencer.seqr_kernel_mem);

    // Write all-zero addin data to addin memory
    seq_addin_wr = spmem_directed_write_sequence#(64,4)::type_id::create("seq_addin_wr");
    seq_addin_wr.size = 16;
    seq_addin_wr.file_path = "./addin_hex.txt";
    seq_addin_wr.start(p_sequencer.seqr_addin);

    // Start compute register sequence (START_COMPUTE=1, COMPE=1)
    seq_register_wr = register_configure_write_seq::type_id::create("seq_register_wr_start");
    seq_register_wr.register = pack_register(
      .k_dim(K_DIM),
      .start_compute(1),
      .compe(1),
      .ps_first(PS_FIRST),
      .ps_mode(PS_MODE),
      .ps_last(PS_LAST),
      .mode_val(mode),
      .sign_8b_val(sign_8b),
      .cont_comp(CONT_COMP),
      .iteration_val(iteration)
    );
    seq_register_wr.start(p_sequencer.seqr_register);

    // Wait for output buffer to be full (poll status signal)
    while (p_sequencer.vif.psout_buff_full != 1) begin
      @(posedge p_sequencer.vif.dimc_tilewrap_clk);
    end

    // Read output buffer and compare to expected
    seq_outbuf_rd = ostream_random_burst_read_sequence#(64)::type_id::create("seq_outbuf_rd");
    seq_outbuf_rd.size = 32;
    seq_outbuf_rd.start(p_sequencer.seqr_output_buffer);

    // Cleanup temporary files
    $system("rm -rf feature_hex.txt");
    $system("rm -rf kernel_hex.txt");
    $system("rm -rf addin_hex.txt");
    $system("rm -rf psin_hex.txt psin_integer.txt");
    $system("rm -rf output_buffer_expected_out.txt");
    $system($sformatf("mv output_buffer_expected_out_psout_hex.txt outputs_rand/output_buffer_expected_out_psout_hex_%0d.txt", repeat_count));
    $system($sformatf("mv output_buffer_expected_out_sout_hex.txt outputs_rand/output_buffer_expected_out_sout_hex_%0d.txt", repeat_count));
    $system($sformatf("mv output_buffer_expected_out_accu_hex.txt outputs_rand/output_buffer_expected_out_accu_hex_%0d.txt", repeat_count));
  endtask

endclass