// Importing all files of dpmem_uvc
package dpmem_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  //`include "dpmem_interface.sv"

  // Include all your SV files here
  `include "dpmem_sequence_item.sv"
  `include "dpmem_write_sequence.sv"
  `include "dpmem_directed_write_sequence.sv"
  `include "dpmem_read_sequence.sv"
  `include "dpmem_directed_read_sequence.sv"
  `include "dpmem_sequencer.sv"
  `include "dpmem_driver.sv"
  `include "dpmem_agent.sv"
  `include "dpmem_env.sv"

endpackage
