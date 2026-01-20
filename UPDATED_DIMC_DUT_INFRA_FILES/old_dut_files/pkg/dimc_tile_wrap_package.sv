// DIMC TILE WRAP package file importing all files 
package dimc_tile_wrap_pkg;
	import uvm_pkg::*;
        import istream_pkg::*;
        import dpmem_pkg::*;
        //import psin_pkg::*;
        import spmem_pkg::*;
        import computation_pkg::*;
        import ostream_pkg::*;
        `include "uvm_macros.svh"
        //`include "dimc_tile_wrap_if_interface.sv""

         `include "p18_dimc_tile_wrap_virtual_sequencer.sv"
         `include "p18_dimc_tile_wrap_scoreboard.sv"
         `include "p18_dimc_tile_wrap_env.sv"
		   // add here the virtual sequences
	 `include "COMP_006_mode_1sign_8b0_PS_FIRST_vseq.sv"
	 `include "COMP_006_mode_0sign_8b0_PS_FIRST_vseq.sv"
	 `include "COMP_006_mode_0sign_8b0_PS_MODE_vseq.sv"

	
	 `include "CI_TC_005_mode3_sign3_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode3_sign3_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode3_sign3_PS_FIRST_vseq.sv"
	 `include "CI_TC_005_mode3_sign2_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode3_sign2_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode3_sign2_PS_FIRST_vseq.sv"
	 `include "CI_TC_005_mode3_sign1_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode3_sign1_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode3_sign1_PS_FIRST_vseq.sv"
	 `include "CI_TC_005_mode3_sign0_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode3_sign0_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode3_sign0_PS_FIRST_vseq.sv"
	 `include "CI_TC_005_mode2_sign0_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode2_sign0_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode2_sign0_PS_FIRST_vseq.sv"
	 `include "CI_TC_005_mode1_sign0_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode1_sign0_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode1_sign0_PS_FIRST_vseq.sv"
	 `include "CI_TC_005_mode0_sign0_PS_LAST_vseq.sv"
	 `include "CI_TC_005_mode0_sign0_PS_MODE_vseq.sv"
	 `include "CI_TC_005_mode0_sign0_PS_FIRST_vseq.sv"
		   // add here the test files
	 `include "COMP_006_mode_1sign_8b0_PS_FIRST_test.sv"
	 `include "COMP_006_mode_0sign_8b0_PS_FIRST_test.sv"
	 `include "COMP_006_mode_0sign_8b0_PS_MODE_test.sv"

	 `include "CI_TC_005_mode3_sign3_PS_LAST_test.sv"
	 `include "CI_TC_005_mode3_sign3_PS_MODE_test.sv"
	 `include "CI_TC_005_mode3_sign3_PS_FIRST_test.sv"
	 `include "CI_TC_005_mode3_sign2_PS_LAST_test.sv"
	 `include "CI_TC_005_mode3_sign2_PS_MODE_test.sv"
	 `include "CI_TC_005_mode3_sign2_PS_FIRST_test.sv"
	 `include "CI_TC_005_mode3_sign1_PS_LAST_test.sv"
	 `include "CI_TC_005_mode3_sign1_PS_MODE_test.sv"
	 `include "CI_TC_005_mode3_sign1_PS_FIRST_test.sv"
	 `include "CI_TC_005_mode3_sign0_PS_LAST_test.sv"
	 `include "CI_TC_005_mode3_sign0_PS_MODE_test.sv"
	 `include "CI_TC_005_mode3_sign0_PS_FIRST_test.sv"
	 `include "CI_TC_005_mode2_sign0_PS_LAST_test.sv"
	 `include "CI_TC_005_mode2_sign0_PS_MODE_test.sv"
	 `include "CI_TC_005_mode2_sign0_PS_FIRST_test.sv"
	 `include "CI_TC_005_mode1_sign0_PS_LAST_test.sv"
	 `include "CI_TC_005_mode1_sign0_PS_MODE_test.sv"
	 `include "CI_TC_005_mode1_sign0_PS_FIRST_test.sv"
	 `include "CI_TC_005_mode0_sign0_PS_LAST_test.sv"
	 `include "CI_TC_005_mode0_sign0_PS_MODE_test.sv"
	 `include "CI_TC_005_mode0_sign0_PS_FIRST_test.sv"

endpackage
