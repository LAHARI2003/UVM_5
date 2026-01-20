// computation_if which gets instantiated in testbench and gets
// connected with the DUT input and output
//
//  K_DIM - Kernel dimension parameter, likely specifying kernel size or dimension.
//  START_COMPUTE - Signal to initiate computation.
//  COMPE - Compute enable signal. Enables computation operations.
//  PS_FIRST - Indicates the first phase or packet in PS (partial sum) mode. Only Feature and Kernel are multiplied and accumulated
//  PS_MODE - Enables partial sum mode operation. Feature and Kernel are multiplied, accumulated and added with PSIN.
//  PS_LAST - Indicates the last phase or packet in PS mode. Feature and Kernal are multiplied, accumulated added with PSIN and ADDIN. The output is SOUT in this case.
//  MODE -
//  Mode selection input, possibly selecting operational modes.
//  Mode = 00 : 1x1 bit mode
//   Mode = 01 : 2x2 bit mode
//   Mode = 10 : 4x4 bit mode
//   Mode = 11: 8x8 bit mode
//  sign_8b - Sign extension or sign mode for 8-bit data operations when mode = 11
//  Sign_8b = 00 : Both kernel and feature unsigned
//  Sign_8b = 01 : Kernel signed, Feature unsigned
//  Sign_8b = 10 : Kernel unsigned, Feature signed
//  Sign_8b = 11 : Kernel and Feature both signed
//  CONT_COMP - Continuous compute mode enable signal.
//  iteration - Iteration count input, specifying number of iterations or processing loops.
//  START_COMPUTE_DISABLE - Signal to disable the start of computation.
//  COMPUTE_DONE - Indicates that computation has completed.
//   iteration_done - Indicates that the specified number of iterations has been completed.
interface computation_if(input logic computation_clk);

  // Output signals (driven by DUT, monitored by TB)
  logic [5:0]  K_DIM;
  logic        START_COMPUTE;
  logic        COMPE;
  logic        PS_FIRST;
  logic        PS_MODE;
  logic        PS_LAST;
  logic [1:0]  MODE;
  logic [1:0]  sign_8b;
  logic        CONT_COMP;
  logic [7:0]  iteration;

  // Input signals (driven by TB, sampled by DUT)
  logic        START_COMPUTE_DISABLE;
  logic        COMPUTE_DONE;
  logic        iteration_done;

  // Clocking block for synchronous access (example for TB driver)
  clocking cb @(posedge computation_clk);
    output K_DIM, START_COMPUTE, COMPE, PS_FIRST, PS_MODE, PS_LAST, MODE, sign_8b, CONT_COMP, iteration;
    input  START_COMPUTE_DISABLE, COMPUTE_DONE, iteration_done;
  endclocking

  initial
    begin
      K_DIM = 6'h0;
      START_COMPUTE = 1'b0;
      COMPE = 1'b0;
      PS_FIRST = 1'b0;
      PS_MODE = 1'b0;
       PS_LAST = 1'b0;
       MODE = 1'b0;
       sign_8b = 1'b0;
       CONT_COMP = 1'b0;
       iteration = 1'b0;
    end

endinterface
