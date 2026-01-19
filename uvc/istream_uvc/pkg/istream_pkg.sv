// Importing all files of feature_buffer_uvc
package istream_pkg;

  //parameter DATA_WIDTH=32;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  //`include "istream_if_interface.sv"

  // Include all your SV files here
  `include "istream_sequence_item.sv"
  `include "ip_stall_rand.sv"
 // `include "feature_sequence.sv"
  `include "istream_directed_write_sequence.sv"
  `include "istream_directed_random_burst_write_sequence.sv"
  `include "istream_sequencer.sv"
  `include "istream_driver.sv"
  `include "istream_monitor.sv"
  `include "istream_agent.sv"
  `include "istream_env.sv"

endpackage
