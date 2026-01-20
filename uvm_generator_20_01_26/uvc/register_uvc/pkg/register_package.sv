//// Importing all files of register_uvc
package register_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  //`include "register_if_interface.sv"

  // Include all your SV files here
  `include "register_sequence_item.sv"
  `include "register_write_sequence.sv"
  `include "register_configure_write_sequence.sv"
  `include "register_sequencer.sv"
  `include "register_driver.sv"
  `include "register_agent.sv"
  `include "register_env.sv"

endpackage
