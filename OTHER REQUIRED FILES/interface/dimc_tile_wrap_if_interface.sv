// dimc_tilewrap_if interface
// SOFT_RESET - Soft reset signal to reset internal logic without affecting the entire system. It is active high.
//  DISABLE_STALL - Disables stalling in the pipeline or data flow.
//  DISABLE_PS_STALL - Disables stalling specifically in PS mode.
//  DISABLE_SOUT_STALL - Disables stalling on the SOUT buffer interface.
//  DISABLE_PSOUT_STALL - Disables stalling on PSOUT buffer interface (if applicable).
//  CG_DISABLE - Clock gating disable signal. Disables clock gating for debugging or power reasons.
//  feat_en - Feature enable signal, likely enabling feature buffer or feature processing.
//  tile_en - Tile enable signal, possibly enabling tiled processing mode.
//  valid_feat_count - Number of valid 64 bit features available or processed.
//  psout_mode - Enables PS output mode.
//  compute_mask - Mask bits controlling compute operations or enabling specific compute units.
//  test_si - Test scan input for scan chain.
//  tst_scanmode - Scan mode enable signal.
//  tst_scanenable - Scan enable signal for test operations.
//  test_clk - 
//  test_so - Test scan output for scan chain.

interface dimc_tilewrap_if(input logic dimc_tilewrap_clk, input logic resetn);

  // Input signals (driven by TB)
  logic        SOFT_RESET;
  logic        DISABLE_STALL;
  logic        DISABLE_PS_STALL;
  logic        DISABLE_SOUT_STALL;
  logic        DISABLE_PSOUT_STALL;
  logic        CG_DISABLE;
  logic        feat_en;
  logic        tile_en;
  logic [7:0]  valid_feat_count; // Assuming width, please adjust if needed
  logic        psout_mode;
  logic        compute_mask;
  logic [3:0]  rcsn_rb;
  logic        test_si;
  logic        tst_scanmode;
  logic        tst_scanenable;
  logic        test_clk;

  // Output signal (driven by DUT, monitored by TB)
  logic        test_so;

  logic        capture_output_buffer_exp_data;
  logic [31:0] output_buffer_exp_data_size;
  logic [7:0] output_buffer_exp_sout_data_size;

  logic feat_buff_full;
  logic feat_buff_empty;
  logic psin_buff_full;
  logic psin_buff_empty;

  logic sout_buff_full;
  logic sout_buff_empty;
  logic psout_buff_full;
  logic psout_buff_empty;

  logic [31:0] psout_internal;
  logic rcsn;




  // Clocking block for synchronous access
  clocking cb @(posedge dimc_tilewrap_clk);
    output SOFT_RESET, DISABLE_STALL, DISABLE_PS_STALL, DISABLE_SOUT_STALL, DISABLE_PSOUT_STALL, CG_DISABLE,
           feat_en, tile_en, valid_feat_count, psout_mode, compute_mask, rcsn_rb, test_si, tst_scanmode, tst_scanenable, test_clk;
    input  test_so,feat_buff_full,feat_buff_empty,psin_buff_full,psin_buff_empty,sout_buff_full,sout_buff_empty,psout_buff_full,psout_buff_empty;
  endclocking

  initial
    begin
      SOFT_RESET = 1'b0;
      DISABLE_STALL = 1'b0;
      DISABLE_PS_STALL = 1'b0;
      DISABLE_SOUT_STALL = 1'b0;
      CG_DISABLE = 1'b0;
      feat_en = 1'b1;
      tile_en = 1'b1;
      valid_feat_count = 8'hF;
      psout_mode = 1'b0;
      compute_mask = 1'b0;
      rcsn_rb = 4'b0;
      test_si = 1'b0;
      tst_scanmode = 1'b0;
      tst_scanenable = 1'b0;
      test_clk = 1'b0;
    end

endinterface
