package dimc_tile_wrapper_pkg;
  import uvm_pkg::*;
  import istream_pkg::*;
  import dpmem_pkg::*;
  import spmem_pkg::*;
  import regbank_pkg::*;
  import ostream_pkg::*;
  `include "uvm_macros.svh"

  // Interfaces
  `include "dimc_tile_wrapper_if.sv"

  // Environment Components
  `include "dimc_tile_wrapper_virtual_sequencer.sv"
  `include "dimc_tile_wrapper_scoreboard.sv"
  `include "dimc_tile_wrapper_env.sv"

  // Test Sequences
  `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv"

  // Tests
  `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv"

endpackage