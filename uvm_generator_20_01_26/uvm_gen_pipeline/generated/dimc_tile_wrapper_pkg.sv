// DIMC TILE WRAPPER M package file importing all files
package dimc_tile_wrapper_pkg;
    import uvm_pkg::*;
    import istream_pkg::*;
    import dpmem_pkg::*;
    import spmem_pkg::*;
    import regbank_pkg::*;
    import ostream_pkg::*;
    `include "uvm_macros.svh"

    // Interface definition
    `include "dimc_tile_wrapper_if.sv"

    // UVM environment components
    `include "dimc_tile_wrapper_virtual_sequencer.sv"
    `include "dimc_tile_wrapper_scoreboard.sv"
    `include "dimc_tile_wrapper_env.sv"

    // Virtual sequence(s)
    `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv"

    // Test(s)
    `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv"

endpackage