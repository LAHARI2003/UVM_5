// DIMC TILE WRAP testbench instantiating dimc_tile_wrapper DUT and Interfaces
// like feature_buffer_if, output_buffer_if, psin_if, addin_if,
// computation_if, kernel_mem_if, dimc_tilewrap_if
module tb;

  import uvm_pkg::*;
  import dimc_tile_wrap_pkg::*;
 
// Parameters
  parameter FEATURE_BUFFER_DATA_WIDTH = 64;
  parameter OUTPUT_BUFFER_DATA_WIDTH = 64;
  parameter PSIN_DATA_WIDTH = 32;

  logic clk;
  logic resetn;

  //reset generation
  initial
    begin
	resetn = 1'b0;
	#250;
	resetn =1'b1;
    end

  initial clk = 0;
  always #5 clk = ~clk; // 100MHz clock


  // Interface instantiation
  istream_if #(FEATURE_BUFFER_DATA_WIDTH) feature_buffer_if_inst(.istream_clk(clk));
  //feature_buffer_if  feature_buffer_if_inst(.feature_buffer_clk(clk));
  
  //output_buffer_if #(OUTPUT_BUFFER_DATA_WIDTH) output_buffer_if_inst(.output_buffer_clk(clk));
  ostream_if #(OUTPUT_BUFFER_DATA_WIDTH) output_buffer_if_inst(.ostream_clk(clk));
  
  istream_if #(PSIN_DATA_WIDTH) psin_if_inst(.istream_clk(clk));

  //psin_if psin_if_inst(.psin_clk(clk));
  
  spmem_if #(64,4) addin_if_inst(.spmem_clk(clk));
  
  computation_if computation_if_inst(.computation_clk(clk));
  
  dpmem_if #(64,9) kernel_mem_if_inst(.dpmem_clk(clk));
  
  dimc_tilewrap_if dimc_tilewrap_if_inst(.dimc_tilewrap_clk(clk),.resetn(resetn));

  // DUT instantiation here (if any), connect interface signals as needed
  dimc_tile_wrapper_m dimc_tile_wrapper (
      //global
	.clk(clk),	//(memory,decoder and dimc tile)
	.resetn(resetn),
//scan ports
	.test_clk(dimc_tilewrap_if_inst.test_clk),
	.test_si(dimc_tilewrap_if_inst.test_si),
	.test_so(dimc_tilewrap_if_inst.test_so),
	.tst_scanmode(dimc_tilewrap_if_inst.tst_scanmode),
	.tst_scanenable(dimc_tilewrap_if_inst.tst_scanenable),
//feature buffer
	.feat_data(feature_buffer_if_inst.istream_data),
	.feat_valid(feature_buffer_if_inst.istream_valid),
	.feat_ready(feature_buffer_if_inst.istream_ready),	
//psin buff
	.psin_data(psin_if_inst.istream_data),	 
	.psin_valid(psin_if_inst.istream_valid),	 
	.psin_ready(psin_if_inst.istream_ready),
//ADDIN buff
	.addin_q(addin_if_inst.spmem_q),	 
	.addin_be(addin_if_inst.spmem_be),	 
	.addin_wr_n(addin_if_inst.spmem_wr_n),
	.addin_cs_n(addin_if_inst.spmem_cs_n),
	.addin_d(addin_if_inst.spmem_d),	 
	.addin_addr(addin_if_inst.spmem_addr),
	
//SOUT/PSOUT buffer
	.out_valid(output_buffer_if_inst.ostream_valid),
	.out_data(output_buffer_if_inst.ostream_data),
	.out_ready(output_buffer_if_inst.ostream_ready),
	.out_first(output_buffer_if_inst.ostream_first),
	.out_last(output_buffer_if_inst.ostream_last),
//AHB bank
	.SOFT_RESET(dimc_tilewrap_if_inst.SOFT_RESET),
	//TRANS_WID,
	.K_DIM(computation_if_inst.K_DIM),
	.START_COMPUTE_DISABLE(computation_if_inst.START_COMPUTE_DISABLE),
	.COMPUTE_DONE(computation_if_inst.COMPUTE_DONE),
	.START_COMPUTE(computation_if_inst.START_COMPUTE),
	.COMPE(computation_if_inst.COMPE),
	.PS_FIRST(computation_if_inst.PS_FIRST),
	.PS_MODE(computation_if_inst.PS_MODE),
	.PS_LAST(computation_if_inst.PS_LAST),
	.DISABLE_STALL(dimc_tilewrap_if_inst.DISABLE_STALL),
	.DISABLE_PS_STALL(dimc_tilewrap_if_inst.DISABLE_PS_STALL),
	.DISABLE_SOUT_STALL(dimc_tilewrap_if_inst.DISABLE_SOUT_STALL),
	.DISABLE_PSOUT_STALL(dimc_tilewrap_if_inst.DISABLE_PSOUT_STALL),
	//TRANS_WID_OUT,
	//ADDIN,
	.CONT_COMP(computation_if_inst.CONT_COMP),
	.CG_DISABLE(dimc_tilewrap_if_inst.CG_DISABLE), 	//CG pin
        .feat_en(dimc_tilewrap_if_inst.feat_en),	//CG pin
	.tile_en(dimc_tilewrap_if_inst.tile_en),	//CG pin
	.iteration(computation_if_inst.iteration),
	.iteration_done(computation_if_inst.iteration_done),
	.valid_feat_count(dimc_tilewrap_if_inst.valid_feat_count),
	.psout_mode(dimc_tilewrap_if_inst.psout_mode),
//buffer flag signals
	.feat_buff_full(dimc_tilewrap_if_inst.feat_buff_full),
	.feat_buff_empty(dimc_tilewrap_if_inst.feat_buff_empty),
	.psin_buff_full(dimc_tilewrap_if_inst.psin_buff_full),
	.psin_buff_empty(dimc_tilewrap_if_inst.psin_buff_empty),
	.sout_buff_full(dimc_tilewrap_if_inst.sout_buff_full),
	.sout_buff_empty(dimc_tilewrap_if_inst.sout_buff_empty),
	.psout_buff_full(dimc_tilewrap_if_inst.psout_buff_full),
	.psout_buff_empty(dimc_tilewrap_if_inst.psout_buff_empty),

//Kernel Memory 
	.SELCK(kernel_mem_if_inst.SELCK),
	.TBYPASS(kernel_mem_if_inst.TBYPASS),
	//MCT,
	.Q(kernel_mem_if_inst.Q),
	.D(kernel_mem_if_inst.D),
	.LS(kernel_mem_if_inst.LS),	
	.SLEEP(kernel_mem_if_inst.SLEEP),   
	.WA(kernel_mem_if_inst.WA),	
	.WCK(clk),	
	.WCSN(kernel_mem_if_inst.WCSN),	
	.WEN(kernel_mem_if_inst.WEN),	
	.RM(kernel_mem_if_inst.RM),	
	.WM(kernel_mem_if_inst.WM),	
	.HS(kernel_mem_if_inst.HS),
	.M(kernel_mem_if_inst.M),
	.MODE(computation_if_inst.MODE),
	.sign_8b(computation_if_inst.sign_8b),
	.RES_IN(kernel_mem_if_inst.RES_IN),
	.RES_OUT(kernel_mem_if_inst.RES_OUT),
	.RA(kernel_mem_if_inst.RA),
	.RCSN(kernel_mem_if_inst.RCSN),
	.rcsn_rb(dimc_tilewrap_if_inst.rcsn_rb),
	.compute_mask(dimc_tilewrap_if_inst.compute_mask)

 
 );


  // UVM Environment
  initial begin
    // Set the interface in the UVM config_db
    uvm_config_db#(virtual istream_if#(FEATURE_BUFFER_DATA_WIDTH))::set(
  //  uvm_config_db#(virtual feature_buffer_if)::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "feature_buffer_vif", // field name
      feature_buffer_if_inst // actual interface
    );

  uvm_config_db#(virtual istream_if#(PSIN_DATA_WIDTH))::set(
  //  uvm_config_db#(virtual feature_buffer_if)::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "psin_vif", // field name
      psin_if_inst // actual interface
    );

    uvm_config_db#(virtual dpmem_if#(64,9))::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "kernel_mem_vif", // field name
      kernel_mem_if_inst // actual interface
    );

  //uvm_config_db#(virtual output_buffer_if#(OUTPUT_BUFFER_DATA_WIDTH))::set(
  uvm_config_db#(virtual ostream_if#(OUTPUT_BUFFER_DATA_WIDTH))::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "ostream_vif", // field name
      output_buffer_if_inst // actual interface
    );

//  //uvm_config_db#(virtual psin_if#(PSIN_DATA_WIDTH))::set(
//  uvm_config_db#(virtual psin_if)::set(
//      null, // scope: null for global
//      "*",  // instance name: * for allcomputation_mode00_psin_first_vir_seq.sv
//      "psin_vif", // field name
//      psin_if_inst // actual interface
//    );

  uvm_config_db#(virtual spmem_if#(64,4))::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "addin_vif", // field name
      addin_if_inst // actual interface
    );

  uvm_config_db#(virtual computation_if)::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "computation_vif", // field name
      computation_if_inst // actual interface
    );

  uvm_config_db#(virtual dimc_tilewrap_if)::set(
      null, // scope: null for global
      "*",  // instance name: * for all
      "dimc_tilewrap_vif", // field name
      dimc_tilewrap_if_inst // actual interface
    );

    run_test();
  end

endmodule 
