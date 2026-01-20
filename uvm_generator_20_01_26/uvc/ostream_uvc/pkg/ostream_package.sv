// Importing all files of ostream_uvc
package ostream_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  //`include "ostream_if_interface.sv"

  // Include all your SV files here
   `include "ostream_sequence_item.sv"
   `include "op_stall_rand.sv"
   `include "ostream_sequencer.sv"
  
  `include "ostream_sequence.sv"
  `include "ostream_read_sequence.sv"
  `include "ostream_random_burst_read_sequence.sv"
  
  `include "ostream_driver.sv"
  `include "ostream_monitor.sv"
  `include "ostream_agent.sv"
  `include "ostream_env.sv"

endpackage
