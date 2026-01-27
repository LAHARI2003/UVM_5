// dimc_tile_wrapper_if.sv
// Interface for dimc_tile_wrapper_m DUT
// Clock: clk (100MHz)
// Reset: resetn (Active Low)

interface dimc_tile_wrapper_if(input logic clk, input logic resetn);

  // Control signals (driven by TB)
  logic        soft_reset;           // Soft reset, active high
  logic        disable_stall;        // Disable pipeline/dataflow stall
  logic        disable_ps_stall;     // Disable PS mode stall
  logic        disable_sout_stall;   // Disable SOUT buffer stall
  logic        disable_psout_stall;  // Disable PSOUT buffer stall
  logic        cg_disable;           // Clock gating disable
  logic        feat_en;              // Feature enable
  logic        tile_en;              // Tile enable
  logic [7:0]  valid_feat_count;     // Number of valid 64b features
  logic        psout_mode;           // PS output mode enable
  logic        compute_mask;         // Compute mask bits
  logic [3:0]  rcsn_rb;              // Redundant chip select
  logic        test_si;              // Test scan input
  logic        tst_scanmode;         // Scan mode enable
  logic        tst_scanenable;       // Scan enable
  logic        test_clk;             // Test clock

  // Status/flag signals (driven by DUT, monitored by TB)
  logic        test_so;              // Test scan output

  logic        capture_output_buffer_exp_data;
  logic [31:0] output_buffer_exp_data_size;
  logic [7:0]  output_buffer_exp_sout_data_size;

  logic        feat_buff_full;
  logic        feat_buff_empty;
  logic        psin_buff_full;
  logic        psin_buff_empty;

  logic        sout_buff_full;
  logic        sout_buff_empty;
  logic        psout_buff_full;
  logic        psout_buff_empty;

  logic [31:0] psout_internal;
  logic        rcsn;

  // Connections to sub-environments (for reference/documentation)
  // m_feature_buffer_env: istream_env#(64)
  // m_psin_env:           istream_env#(32)
  // m_kernel_mem_env:     dpmem_env#(64,9)
  // m_addin_env:          spmem_env#(64,4)
  // m_computation_env:    register_env
  // m_output_buffer_env:  ostream_env#(64)

  // Clocking block for synchronous access
  clocking cb @(posedge clk);
    output soft_reset, disable_stall, disable_ps_stall, disable_sout_stall, disable_psout_stall, cg_disable,
           feat_en, tile_en, valid_feat_count, psout_mode, compute_mask, rcsn_rb, test_si, tst_scanmode, tst_scanenable, test_clk;
    input  test_so, feat_buff_full, feat_buff_empty, psin_buff_full, psin_buff_empty,
           sout_buff_full, sout_buff_empty, psout_buff_full, psout_buff_empty;
  endclocking

  // Initial block with default values
  initial begin
    soft_reset                   = 1'b0;
    disable_stall                = 1'b0;
    disable_ps_stall             = 1'b0;
    disable_sout_stall           = 1'b0;
    disable_psout_stall          = 1'b0;
    cg_disable                   = 1'b0;
    feat_en                      = 1'b1;
    tile_en                      = 1'b1;
    valid_feat_count             = 8'hF;
    psout_mode                   = 1'b0;
    compute_mask                 = 1'b0;
    rcsn_rb                      = 4'b0;
    test_si                      = 1'b0;
    tst_scanmode                 = 1'b0;
    tst_scanenable               = 1'b0;
    test_clk                     = 1'b0;
    capture_output_buffer_exp_data      = 1'b0;
    output_buffer_exp_data_size         = 32'b0;
    output_buffer_exp_sout_data_size    = 8'b0;
  end

endinterface