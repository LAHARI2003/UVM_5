// DIMC TILE WRAPPER M package file importing all files and UVC packages
package dimc_tile_wrapper_pkg;
    import uvm_pkg::*;
    import istream_pkg::*;
    import dpmem_pkg::*;
    import spmem_pkg::*;
    import register_pkg::*;
    import ostream_pkg::*;
    `include "uvm_macros.svh"

    // Interface definition
    `include "dimc_tile_wrapper_if.sv"

    // Virtual sequencer
    `include "dimc_tile_wrapper_virtual_sequencer.sv"

    // Scoreboard
    `include "dimc_tile_wrapper_scoreboard.sv"

    // Environment
    `include "dimc_tile_wrapper_env.sv"

    // Test
    `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv"

endpackage