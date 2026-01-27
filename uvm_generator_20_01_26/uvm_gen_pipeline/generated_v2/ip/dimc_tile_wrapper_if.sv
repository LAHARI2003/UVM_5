// dimc_tile_wrapper_if.sv
// Interface for dimc_tile_wrapper_m DUT
// Clock: clk (100MHz)
// Reset: resetn (Active Low)
// This interface provides control, status, and coordination signals for the DUT and its UVM testbench environments.

interface dimc_tile_wrapper_if(input logic clk, input logic resetn);

  // Control signals (driven by TB)
  logic        soft_reset;              // Soft reset for internal DUT logic (active high)
  logic        disable_stall;           // Disable pipeline/dataflow stalling
  logic        disable_ps_stall;        // Disable PS mode stalling
  logic        disable_sout_stall;      // Disable SOUT buffer stalling
  logic        disable_psout_stall;     // Disable PSOUT buffer stalling
  logic        cg_disable;              // Clock gating disable
  logic        feat_en;                 // Feature enable
  logic        tile_en;                 // Tile enable
  logic [7:0]  valid_feat_count;        // Number of valid 64b features
  logic        psout_mode;              // PS output mode enable
  logic [7:0]  compute_mask;            // Compute mask bits
  logic [3:0]  rcsn_rb;                 // Register bank chip select
  logic        test_si;                 // Test scan input
  logic        tst_scanmode;            // Scan mode enable
  logic        tst_scanenable;          // Scan enable
  logic        test_clk;                // Test clock

  // Status/flag signals (driven by DUT, monitored by TB)
  logic        test_so;                 // Test scan output

  // Feature buffer status
  logic        feat_buff_full;
  logic        feat_buff_empty;

  // PSIN buffer status
  logic        psin_buff_full;
  logic        psin_buff_empty;

  // SOUT buffer status
  logic        sout_buff_full;
  logic        sout_buff_empty;

  // PSOUT buffer status
  logic        psout_buff_full;
  logic        psout_buff_empty;

  // Output buffer expected data coordination
  logic        capture_output_buffer_exp_data;
  logic [31:0] output_buffer_exp_data_size;
  logic [7:0]  output_buffer_exp_sout_data_size;

  // Internal PSOUT monitoring
  logic [31:0] psout_internal;

  // Register bank chip select (status)
  logic        rcsn;

  // Interfaces to sub-environments (for hierarchical connections)
  // These are placeholders for modport connections or virtual interface binding in TB
  // logic [63:0]  feature_buffer_data;
  // logic [31:0]  psin_data;
  // logic [63:0]  kernel_mem_data;
  // logic [8:0]   kernel_mem_addr;
  // logic [63:0]  addin_data;
  // logic [3:0]   addin_addr;
  // logic [63:0]  output_buffer_data;

  // Clocking block for synchronous access
  clocking cb @(posedge clk);
    output soft_reset, disable_stall, disable_ps_stall, disable_sout_stall, disable_psout_stall, cg_disable,
           feat_en, tile_en, valid_feat_count, psout_mode, compute_mask, rcsn_rb, test_si, tst_scanmode, tst_scanenable, test_clk,
           capture_output_buffer_exp_data, output_buffer_exp_data_size, output_buffer_exp_sout_data_size;
    input  test_so, feat_buff_full, feat_buff_empty, psin_buff_full, psin_buff_empty,
           sout_buff_full, sout_buff_empty, psout_buff_full, psout_buff_empty, psout_internal, rcsn;
  endclocking

  // Initial block to set default values for all signals
  initial begin
    soft_reset                     = 1'b0;
    disable_stall                  = 1'b0;
    disable_ps_stall               = 1'b0;
    disable_sout_stall             = 1'b0;
    disable_psout_stall            = 1'b0;
    cg_disable                     = 1'b0;
    feat_en                        = 1'b1;
    tile_en                        = 1'b1;
    valid_feat_count               = 8'hF;
    psout_mode                     = 1'b0;
    compute_mask                   = 8'b0;
    rcsn_rb                        = 4'b0;
    test_si                        = 1'b0;
    tst_scanmode                   = 1'b0;
    tst_scanenable                 = 1'b0;
    test_clk                       = 1'b0;
    capture_output_buffer_exp_data = 1'b0;
    output_buffer_exp_data_size    = 32'b0;
    output_buffer_exp_sout_data_size = 8'b0;
  end

endinterface