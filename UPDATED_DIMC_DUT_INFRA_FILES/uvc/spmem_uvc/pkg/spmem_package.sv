// Importing all files of spmem_uvc
package spmem_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  //`include "spmem_if_interface.sv"

  // Include all your SV files here
  `include "spmem_sequence_item.sv"
  `include "spmem_write_sequence.sv"
  `include "spmem_directed_write_sequence.sv"
  `include "spmem_read_sequence.sv"
  `include "spmem_directed_read_sequence.sv"
  `include "spmem_sequencer.sv"
  `include "spmem_driver.sv"
  `include "spmem_agent.sv"
  `include "spmem_env.sv"

endpackage
