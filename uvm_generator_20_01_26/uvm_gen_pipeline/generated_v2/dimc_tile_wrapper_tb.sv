//------------------------------------------------------------------------------
// dimc_tile_wrapper_tb.sv
// Top-level UVM testbench for dimc_tile_wrapper_m
//------------------------------------------------------------------------------

module dimc_tile_wrapper_tb;

  import uvm_pkg::*;
  import dimc_tile_wrapper_m_pkg::*;

  // Parameters
  parameter FEATURE_BUFFER_DATA_WIDTH = 64;
  parameter OUTPUT_BUFFER_DATA_WIDTH  = 64;
  parameter PSIN_DATA_WIDTH          = 32;
  parameter KERNEL_MEM_DATA_WIDTH    = 64;
  parameter KERNEL_MEM_ADDR_WIDTH    = 9;
  parameter ADDIN_DATA_WIDTH         = 64;
  parameter ADDIN_ADDR_WIDTH         = 4;

  logic clk;
  logic resetn;

  // Clock generation
  initial clk = 0;
  always #5 clk = ~clk; // 100MHz clock

  // Reset generation
  initial begin
    resetn = 1'b0;
    #250;
    resetn = 1'b1;
  end

  // Interface instantiations
  istream_if #(FEATURE_BUFFER_DATA_WIDTH) m_feature_buffer_if_inst(.istream_clk(clk));
  istream_if #(PSIN_DATA_WIDTH)           m_psin_if_inst(.istream_clk(clk));
  dpmem_if #(KERNEL_MEM_DATA_WIDTH, KERNEL_MEM_ADDR_WIDTH) m_kernel_mem_if_inst(.dpmem_clk(clk));
  spmem_if #(ADDIN_DATA_WIDTH, ADDIN_ADDR_WIDTH)           m_addin_if_inst(.spmem_clk(clk));
  regbank_if m_computation_if_inst(.regbank_clk(clk));
  ostream_if #(OUTPUT_BUFFER_DATA_WIDTH)  m_output_buffer_if_inst(.ostream_clk(clk));

  // Register decode logic (example mapping, adjust as needed)
  logic [5:0]  K_DIM_decoded;
  logic        START_COMPUTE_decoded;
  logic        COMPE_decoded;
  logic        PS_FIRST_decoded;
  logic        PS_MODE_decoded;
  logic        PS_LAST_decoded;
  logic [1:0]  MODE_decoded;
  logic [1:0]  sign_8b_decoded;
  logic        CONT_COMP_decoded;
  logic [7:0]  iteration_decoded;

  // Status signals to pack into regbank_status
  logic        START_COMPUTE_DISABLE;
  logic        COMPUTE_DONE;
  logic        iteration_done;

  // Decode register into individual signals
  assign K_DIM_decoded         = m_computation_if_inst.regbank[5:0];
  assign START_COMPUTE_decoded = m_computation_if_inst.regbank[6];
  assign COMPE_decoded         = m_computation_if_inst.regbank[7];
  assign PS_FIRST_decoded      = m_computation_if_inst.regbank[8];
  assign PS_MODE_decoded       = m_computation_if_inst.regbank[9];
  assign PS_LAST_decoded       = m_computation_if_inst.regbank[10];
  assign MODE_decoded          = m_computation_if_inst.regbank[12:11];
  assign sign_8b_decoded       = m_computation_if_inst.regbank[14:13];
  assign CONT_COMP_decoded     = m_computation_if_inst.regbank[15];
  assign iteration_decoded     = m_computation_if_inst.regbank[23:16];

  // Pack status signals into regbank_status
  assign m_computation_if_inst.regbank_status = {29'b0, iteration_done, COMPUTE_DONE, START_COMPUTE_DISABLE};

  // DUT instantiation
  dimc_tile_wrapper_m dut (
    // Clock and reset
    .clk(clk),
    .resetn(resetn),

    // Feature buffer interface
    .feat_data   (m_feature_buffer_if_inst.istream_data),
    .feat_valid  (m_feature_buffer_if_inst.istream_valid),
    .feat_ready  (m_feature_buffer_if_inst.istream_ready),

    // PSIN buffer interface
    .psin_data   (m_psin_if_inst.istream_data),
    .psin_valid  (m_psin_if_inst.istream_valid),
    .psin_ready  (m_psin_if_inst.istream_ready),

    // Kernel memory interface
    .SELCK       (m_kernel_mem_if_inst.SELCK),
    .TBYPASS     (m_kernel_mem_if_inst.TBYPASS),
    .Q           (m_kernel_mem_if_inst.Q),
    .D           (m_kernel_mem_if_inst.D),
    .LS          (m_kernel_mem_if_inst.LS),
    .SLEEP       (m_kernel_mem_if_inst.SLEEP),
    .WA          (m_kernel_mem_if_inst.WA),
    .WCK         (clk),
    .WCSN        (m_kernel_mem_if_inst.WCSN),
    .WEN         (m_kernel_mem_if_inst.WEN),
    .RM          (m_kernel_mem_if_inst.RM),
    .WM          (m_kernel_mem_if_inst.WM),
    .HS          (m_kernel_mem_if_inst.HS),
    .M           (m_kernel_mem_if_inst.M),
    .RES_IN      (m_kernel_mem_if_inst.RES_IN),
    .RES_OUT     (m_kernel_mem_if_inst.RES_OUT),
    .RA          (m_kernel_mem_if_inst.RA),
    .RCSN        (m_kernel_mem_if_inst.RCSN),

    // ADDIN buffer interface
    .addin_q     (m_addin_if_inst.spmem_q),
    .addin_be    (m_addin_if_inst.spmem_be),
    .addin_wr_n  (m_addin_if_inst.spmem_wr_n),
    .addin_cs_n  (m_addin_if_inst.spmem_cs_n),
    .addin_d     (m_addin_if_inst.spmem_d),
    .addin_addr  (m_addin_if_inst.spmem_addr),

    // Output buffer interface
    .out_valid   (m_output_buffer_if_inst.ostream_valid),
    .out_data    (m_output_buffer_if_inst.ostream_data),
    .out_ready   (m_output_buffer_if_inst.ostream_ready),
    .out_first   (m_output_buffer_if_inst.ostream_first),
    .out_last    (m_output_buffer_if_inst.ostream_last),

    // Register interface signals (decoded)
    .K_DIM               (K_DIM_decoded),
    .START_COMPUTE       (START_COMPUTE_decoded),
    .COMPE               (COMPE_decoded),
    .PS_FIRST            (PS_FIRST_decoded),
    .PS_MODE             (PS_MODE_decoded),
    .PS_LAST             (PS_LAST_decoded),
    .MODE                (MODE_decoded),
    .sign_8b             (sign_8b_decoded),
    .CONT_COMP           (CONT_COMP_decoded),
    .iteration           (iteration_decoded),
    .START_COMPUTE_DISABLE(START_COMPUTE_DISABLE),
    .COMPUTE_DONE        (COMPUTE_DONE),
    .iteration_done      (iteration_done)

    // Add additional connections as required by the DUT
  );

  // UVM Environment
  initial begin
    // Set all virtual interfaces in the UVM config_db
    uvm_config_db#(virtual istream_if#(FEATURE_BUFFER_DATA_WIDTH))::set(
      null, "*", "feature_buffer_vif", m_feature_buffer_if_inst
    );
    uvm_config_db#(virtual istream_if#(PSIN_DATA_WIDTH))::set(
      null, "*", "psin_vif", m_psin_if_inst
    );
    uvm_config_db#(virtual dpmem_if#(KERNEL_MEM_DATA_WIDTH, KERNEL_MEM_ADDR_WIDTH))::set(
      null, "*", "kernel_mem_vif", m_kernel_mem_if_inst
    );
    uvm_config_db#(virtual spmem_if#(ADDIN_DATA_WIDTH, ADDIN_ADDR_WIDTH))::set(
      null, "*", "addin_vif", m_addin_if_inst
    );
    uvm_config_db#(virtual regbank_if)::set(
      null, "*", "regbank_vif", m_computation_if_inst
    );
    uvm_config_db#(virtual ostream_if#(OUTPUT_BUFFER_DATA_WIDTH))::set(
      null, "*", "ostream_vif", m_output_buffer_if_inst
    );

    run_test();
  end

endmodule