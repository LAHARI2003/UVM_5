class CI_TC_005_mode0_sign0_PS_FIRST_vseq extends uvm_sequence; // virtual sequence

  `uvm_object_utils(CI_TC_005_mode0_sign0_PS_FIRST_vseq)
  `uvm_declare_p_sequencer(p18_dimc_tile_wrap_virtual_sequencer)

  istream_directed_write_sequence#(64)  seq_feat_wr;
  dpmem_directed_write_sequence#(64,9)  seq_ker_wr;
  // Updated: use register_configure_write_seq instead of computation_configure_write_seq
  register_configure_write_seq          seq_register_wr;
  ostream_random_burst_read_sequence#(64) seq_outbuf_rd;
  
  int mode;
  int feature_buffer_size;
  int sign_8b;
  int PS_FIRST;
  int PS_MODE;
  int PS_LAST;

  function new(string name = "CI_TC_005_mode0_sign0_PS_FIRST_vseq");
    super.new(name);
  endfunction

  // Helper function to pack computation parameters into 32-bit register
  // Register bit mapping:
  // register[5:0]   = K_DIM (default 0)
  // register[6]     = START_COMPUTE
  // register[7]     = COMPE
  // register[8]     = PS_FIRST
  // register[9]     = PS_MODE
  // register[10]    = PS_LAST
  // register[12:11] = MODE
  // register[14:13] = sign_8b
  // register[15]    = CONT_COMP (default 0)
  // register[23:16] = iteration (default 0)
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
    int iteration = 0
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
    reg_val = reg_val | ((iteration & 8'hFF) << 16);        // bits [23:16]
    return reg_val;
  endfunction

  task body();
    int feat;
    int psin;
    int addin;
    int cmodel;
    int repeat_count = 1;


    // Set parameters (replace placeholders with actual values)
    mode = 0;
    feature_buffer_size = 1;
    sign_8b = 0;
    PS_FIRST = 1;
    PS_MODE = 0;
    PS_LAST = 0;

    feat = $system($sformatf("python generate_data_hex_unique.py --mode %d --feature_buffer_size %d --sign_8b %d > result_feature.txt",mode, feature_buffer_size, sign_8b));
    if (feat != 0) begin
      `uvm_error("Vseq", "Failed to generate feature and kernel data")
      return;
    end

    psin = $system($sformatf("python generate_data_psin_addin.py"));
    if (psin != 0) begin
      `uvm_error("Vseq", "Failed to generate psin and addin data")
      return;
    end

    cmodel = $system($sformatf("./psout_exe kernel_hex.txt feature_hex.txt psin_hex.txt addin_hex.txt output_buffer_expected_out.txt %02b %02b %01b %01b %01b > result_cmodel.txt",
                              mode, sign_8b, PS_FIRST, PS_MODE, PS_LAST));
    if (cmodel != 0) begin
      `uvm_error("Vseq", "Failed to run Cmodel executable")
      return;
    end

    p_sequencer.vif.capture_output_buffer_exp_data = 1'b0;
    @(posedge p_sequencer.vif.dimc_tilewrap_clk);

    p_sequencer.vif.capture_output_buffer_exp_data = 1'b1;
    p_sequencer.vif.output_buffer_exp_data_size = 32;
    @(posedge p_sequencer.vif.dimc_tilewrap_clk);
    p_sequencer.vif.capture_output_buffer_exp_data = 1'b0;

    // Initialization Register sequence (replaces computation sequence)
    // Pack parameters: START_COMPUTE=0, COMPE=0 for initialization
    seq_register_wr = register_configure_write_seq::type_id::create("seq_register_wr");
    seq_register_wr.register = pack_register(
      .k_dim(0),
      .start_compute(0),
      .compe(0),
      .ps_first(PS_FIRST),
      .ps_mode(PS_MODE),
      .ps_last(PS_LAST),
      .mode_val(mode),
      .sign_8b_val(sign_8b),
      .cont_comp(0),
      .iteration(0)
    );
    seq_register_wr.start(p_sequencer.seqr_register);

    // Feature memory write (1k)
    seq_feat_wr = istream_directed_write_sequence#(64)::type_id::create("seq_feat_wr");
    seq_feat_wr.size = 16;
    seq_feat_wr.file_path = "./feature_hex_rtl.txt";
    seq_feat_wr.start(p_sequencer.seqr_feature_buffer);

    // Kernel memory write (32kb)
    seq_ker_wr = dpmem_directed_write_sequence#(64,9)::type_id::create("seq_ker_wr");
    seq_ker_wr.size = 512;
    seq_ker_wr.file_path = "./kernel_hex_rtl.txt";
    seq_ker_wr.start(p_sequencer.seqr_kernel_mem);
    $display("Kernel data at index 0: %h", seq_ker_wr.ker_data_ip[0]);

    // Register sequence - start compute (replaces computation sequence)
    // Pack parameters: START_COMPUTE=1, COMPE=1 to start computation
    seq_register_wr = register_configure_write_seq::type_id::create("seq_register_wr");
    seq_register_wr.register = pack_register(
      .k_dim(0),
      .start_compute(1),
      .compe(1),
      .ps_first(PS_FIRST),
      .ps_mode(PS_MODE),
      .ps_last(PS_LAST),
      .mode_val(mode),
      .sign_8b_val(sign_8b),
      .cont_comp(0),
      .iteration(0)
    );
    seq_register_wr.start(p_sequencer.seqr_register);

    // Output buffer read sequence
    while (p_sequencer.vif.psout_buff_full != 1) begin
      @(posedge p_sequencer.vif.dimc_tilewrap_clk);
    end

    seq_outbuf_rd = ostream_random_burst_read_sequence#(64)::type_id::create("seq_outbuf_rd");
    seq_outbuf_rd.size = 32;
    seq_outbuf_rd.start(p_sequencer.seqr_output_buffer);

    // Cleanup and renaming files
  $system("rm -rf feature_data_binary.txt"); 
$system("rm -rf feature_data.txt"); 
$system("rm -rf feature_hex.txt"); 
$system("mv feature_hex_rtl.txt feature_hex_rtl_test.txt"); 
$system("rm -rf kernel_data_binary.txt"); 
$system("rm -rf kernel_data.txt"); 
$system("rm -rf kernel_hex.txt"); 
$system("mv kernel_hex_rtl.txt kernel_hex_rtl_test.txt");
$system("rm -rf psin_hex.txt psin_integer.txt");
$system("mv psin_hex_rtl.txt psin_hex_rtl_test.txt");

$system("rm -rf addin_hex.txt addin_integer.txt");
$system("mv addin_hex_rtl.txt addin_hex_rtl_test.txt");
 
$system("rm -rf output_buffer_expected_out.txt"); $system($sformatf("mv output_buffer_expected_out_psout_hex.txt outputs_rand/output_buffer_expected_out_psout_hex_%0d.txt", repeat_count)); $system($sformatf("mv output_buffer_expected_out_sout_hex.txt outputs_rand/output_buffer_expected_out_sout_hex_%0d.txt", repeat_count)); $system($sformatf("mv output_buffer_expected_out_accu_hex.txt outputs_rand/output_buffer_expected_out_accu_hex_%0d.txt", repeat_count));

  endtask

endclass
