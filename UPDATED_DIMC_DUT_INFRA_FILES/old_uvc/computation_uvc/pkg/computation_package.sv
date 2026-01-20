//// Importing all files of computation_uvc
package computation_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  //`include "computation_if_interface.sv"

  // Include all your SV files here
  `include "computation_sequence_item.sv"
  `include "computation_write_sequence.sv"
  `include "computation_directed_write_sequence.sv"
  `include "computation_configure_write_sequence.sv"
  `include "computation_sequencer.sv"
  `include "computation_driver.sv"
  `include "computation_agent.sv"
  `include "computation_env.sv"

endpackage
