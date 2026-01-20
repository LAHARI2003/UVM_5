// dimc_tile_wrapper_tb.sv
// Top-level testbench for dimc_tile_wrapper_m

import uvm_pkg::*;
import dimc_tile_wrapper_pkg::*;

module tb;

  // Parameters for data widths
  parameter FEATURE_BUFFER_DATA_WIDTH = 64;
  parameter PSIN_DATA_WIDTH = 32;
  parameter KERNEL_MEM_DATA_WIDTH = 64;
  parameter KERNEL_MEM_ADDR_WIDTH = 9;
  parameter ADDIN_DATA_WIDTH = 64;
  parameter ADDIN_ADDR_WIDTH = 4;
  parameter OUTPUT_BUFFER_DATA_WIDTH = 64;

  logic clk;
  logic resetn;

  // Clock and reset generation
  initial begin
    resetn = 1'b0;
    #250;
    resetn = 1'b1;
  end

  initial clk = 0;
  always #5 clk = ~clk; // 100MHz clock

  // Interface instantiation
  istream_if #(FEATURE_BUFFER_DATA_WIDTH) m_feature_buffer_if_inst(.istream_clk(clk));
  istream_if #(PSIN_DATA_WIDTH) m_psin_if_inst(.istream_clk(clk));
  dpmem_if #(KERNEL_MEM_DATA_WIDTH, KERNEL_MEM_ADDR_WIDTH) m_kernel_mem_if_inst(.dpmem_clk(clk));
  spmem_if #(ADDIN_DATA_WIDTH, ADDIN_ADDR_WIDTH) m_addin_if_inst(.spmem_clk(clk));
  regbank_if m_computation_if_inst(.regbank_clk(clk));
  ostream_if #(OUTPUT_BUFFER_DATA_WIDTH) m_output_buffer_if_inst(.ostream_clk(clk));

  // DUT instantiation
  dimc_tile_wrapper_m dimc_tile_wrapper_m_inst(
    .clk(clk),
    .resetn(resetn),
    // Feature Buffer Interface
    .feat_data(m_feature_buffer_if_inst.istream_data),
    .feat_valid(m_feature_buffer_if_inst.istream_valid),
    .feat_ready(m_feature_buffer_if_inst.istream_ready),
    // PSIN Interface
    .psin_data(m_psin_if_inst.istream_data),
    .psin_valid(m_psin_if_inst.istream_valid),
    .psin_ready(m_psin_if_inst.istream_ready),
    // Kernel Memory Interface
    .kernel_mem_data(m_kernel_mem_if_inst.dpmem_data),
    .kernel_mem_addr(m_kernel_mem_if_inst.dpmem_addr),
    .kernel_mem_wren(m_kernel_mem_if_inst.dpmem_wren),
    .kernel_mem_rden(m_kernel_mem_if_inst.dpmem_rden),
    // ADDIN Interface
    .addin_data(m_addin_if_inst.spmem_data),
    .addin_addr(m_addin_if_inst.spmem_addr),
    .addin_wren(m_addin_if_inst.spmem_wren),
    // Output Buffer Interface
    .out_data(m_output_buffer_if_inst.ostream_data),
    .out_valid(m_output_buffer_if_inst.ostream_valid),
    .out_ready(m_output_buffer_if_inst.ostream_ready),
    // Computation Interface (decoded signals)
    .start_compute(m_computation_if_inst.start_compute),
    .compute_done(m_computation_if_inst.compute_done)
  );

  // UVM Environment
  initial begin
    // Set the interface in the UVM config_db
    uvm_config_db#(virtual istream_if#(FEATURE_BUFFER_DATA_WIDTH))::set(null, "*", "m_feature_buffer_vif", m_feature_buffer_if_inst);
    uvm_config_db#(virtual istream_if#(PSIN_DATA_WIDTH))::set(null, "*", "m_psin_vif", m_psin_if_inst);
    uvm_config_db#(virtual dpmem_if#(KERNEL_MEM_DATA_WIDTH, KERNEL_MEM_ADDR_WIDTH))::set(null, "*", "m_kernel_mem_vif", m_kernel_mem_if_inst);
    uvm_config_db#(virtual spmem_if#(ADDIN_DATA_WIDTH, ADDIN_ADDR_WIDTH))::set(null, "*", "m_addin_vif", m_addin_if_inst);
    uvm_config_db#(virtual regbank_if)::set(null, "*", "m_computation_vif", m_computation_if_inst);
    uvm_config_db#(virtual ostream_if#(OUTPUT_BUFFER_DATA_WIDTH))::set(null, "*", "m_output_buffer_vif", m_output_buffer_if_inst);

    run_test();
  end

endmodule