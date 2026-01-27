// TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv
// Virtual sequence for TC_S2_SF_MODE00_PS_FIRST_K0F0
// Mode: 00, PS_FIRST=1, PS_MODE=0, PS_LAST=0, K_DIM=0, sign_8b: don't care
// Stimulus: All-zero kernel, feature, addin. Single-frame compute, PS_FIRST phase.

class TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq extends uvm_sequence;

  `uvm_object_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq)
  `uvm_declare_p_sequencer(dimc_tile_wrapper_virtual_sequencer)

  // Sub-sequence handles
  register_configure_write_seq             seq_register_wr;
  dpmem_directed_write_sequence#(64,9)     seq_kernel_wr;
  istream_directed_write_sequence#(64)     seq_feature_wr;
  spmem_directed_write_sequence#(64,4)     seq_addin_wr;
  ostream_random_burst_read_sequence#(64)  seq_output_rd;

  // Test parameters
  int mode;
  int sign_8b;
  int PS_FIRST;
  int PS_MODE;
  int PS_LAST;
  int K_DIM;
  int CONT_COMP;
  int iteration;

  // Helper function to pack register bits
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

  task body();
    int ret_kernel, ret_feature, ret_addin, ret_cmodel;
    int start_compute, compe;
    string kernel_file, feature_file, addin_file, psin_file, output_file;
    string cmodel_cmd;
    int output_size;

    // Set test parameters
    mode      = 0; // MODE = 00
    sign_8b   = 0; // Don't care for this test, set to 0
    PS_FIRST  = 1;
    PS_MODE   = 0;
    PS_LAST   = 0;
    K_DIM     = 0;
    CONT_COMP = 0;
    iteration = 0;

    // File names
    kernel_file  = "kernel_hex.txt";
    feature_file = "feature_hex.txt";
    addin_file   = "addin_hex.txt";
    psin_file    = "psin_hex.txt";
    output_file  = "output_buffer_expected_out_psout_hex.txt";
    output_size  = 32;

    // Generate all-zero kernel data
    ret_kernel = $system($sformatf("python generate_bin_pattern.py --pattern BIN_K_ALL0 --outfile %s", kernel_file));
    if (ret_kernel != 0) begin
      `uvm_error("VSEQ", "Failed to generate all-zero kernel data")
      return;
    end

    // Generate all-zero feature data
    ret_feature = $system($sformatf("python generate_bin_pattern.py --pattern BIN_F_ALL0 --outfile %s", feature_file));
    if (ret_feature != 0) begin
      `uvm_error("VSEQ", "Failed to generate all-zero feature data")
      return;
    end

    // Generate all-zero addin data
    ret_addin = $system($sformatf("python generate_bin_pattern.py --pattern BIN_ADDIN_0 --outfile %s", addin_file));
    if (ret_addin != 0) begin
      `uvm_error("VSEQ", "Failed to generate all-zero addin data")
      return;
    end

    // Generate dummy psin data (not used in PS_FIRST, but required by C model)
    ret_addin = $system($sformatf("python generate_bin_pattern.py --pattern BIN_PSIN_0 --outfile %s", psin_file));
    if (ret_addin != 0) begin
      `uvm_error("VSEQ", "Failed to generate all-zero psin data")
      return;
    end

    // Run C model to generate expected output
    cmodel_cmd = $sformatf("./psout_exe %s %s %s %s %s %02b %02b %01b %01b %01b > result_cmodel.txt",
      kernel_file, feature_file, psin_file, addin_file, output_file,
      mode, sign_8b, PS_FIRST, PS_MODE, PS_LAST);
    ret_cmodel = $system(cmodel_cmd);
    if (ret_cmodel != 0) begin
      `uvm_error("VSEQ", "Failed to run C model executable")
      return;
    end

    // Configure DUT to capture expected output buffer data
    p_sequencer.vif.capture_output_buffer_exp_data = 1'b0;
    @(posedge p_sequencer.vif.clk);

    p_sequencer.vif.capture_output_buffer_exp_data = 1'b1;
    p_sequencer.vif.output_buffer_exp_data_size = output_size;
    @(posedge p_sequencer.vif.clk);
    p_sequencer.vif.capture_output_buffer_exp_data = 1'b0;

    // Initialization register write (START_COMPUTE=0, COMPE=0)
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
      .iteration(iteration)
    );
    seq_register_wr.start(p_sequencer.seqr_computation);

    // Preload kernel memory with all-zero data
    seq_kernel_wr = dpmem_directed_write_sequence#(64,9)::type_id::create("seq_kernel_wr");
    seq_kernel_wr.size = 512;
    seq_kernel_wr.file_path = kernel_file;
    seq_kernel_wr.start(p_sequencer.seqr_kernel_mem);

    // Preload feature buffer with all-zero data
    seq_feature_wr = istream_directed_write_sequence#(64)::type_id::create("seq_feature_wr");
    seq_feature_wr.size = 16;
    seq_feature_wr.file_path = feature_file;
    seq_feature_wr.start(p_sequencer.seqr_feature_buffer);

    // Preload addin memory with all-zero data
    seq_addin_wr = spmem_directed_write_sequence#(64,4)::type_id::create("seq_addin_wr");
    seq_addin_wr.size = 16;
    seq_addin_wr.file_path = addin_file;
    seq_addin_wr.start(p_sequencer.seqr_addin);

    // Start compute register write (START_COMPUTE=1, COMPE=1)
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
      .iteration(iteration)
    );
    seq_register_wr.start(p_sequencer.seqr_computation);

    // Wait for output buffer to be ready (psout_buff_full == 1)
    while (p_sequencer.vif.psout_buff_full != 1) begin
      @(posedge p_sequencer.vif.clk);
    end

    // Read output buffer
    seq_output_rd = ostream_random_burst_read_sequence#(64)::type_id::create("seq_output_rd");
    seq_output_rd.size = output_size;
    seq_output_rd.start(p_sequencer.seqr_output_buffer);

    // Cleanup temporary files
    $system("rm -rf kernel_hex.txt feature_hex.txt addin_hex.txt psin_hex.txt");
    $system("rm -rf result_cmodel.txt");

  endtask

endclass