// computation_seq_item fields
// computation_seq_item fields driven by the driver to computation_if interface
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

class computation_seq_item extends uvm_sequence_item;

  // Output signals (driven by sequence/driver)
  rand bit [5:0]  K_DIM;
  rand bit        START_COMPUTE;
  rand bit        COMPE;
  rand bit        PS_FIRST;
  rand bit        PS_MODE;
  rand bit        PS_LAST;
  rand bit [1:0]  MODE;
  rand bit [1:0]  sign_8b;
  rand bit        CONT_COMP;
  rand bit [7:0]  iteration;

  // Input signals (sampled by driver)
  bit             START_COMPUTE_DISABLE;
  bit             COMPUTE_DONE;
  bit             iteration_done;

  `uvm_object_utils(computation_seq_item)

  function new(string name = "computation_seq_item");
    super.new(name);
  endfunction

  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field("K_DIM", K_DIM, 6);
    printer.print_field("START_COMPUTE", START_COMPUTE, 1);
    printer.print_field("COMPE", COMPE, 1);
    printer.print_field("PS_FIRST", PS_FIRST, 1);
    printer.print_field("PS_MODE", PS_MODE, 1);
    printer.print_field("PS_LAST", PS_LAST, 1);
    printer.print_field("MODE", MODE, 2);
    printer.print_field("sign_8b", sign_8b, 2);
    printer.print_field("CONT_COMP", CONT_COMP, 1);
    printer.print_field("iteration", iteration, 8);
    printer.print_field("START_COMPUTE_DISABLE", START_COMPUTE_DISABLE, 1);
    printer.print_field("COMPUTE_DONE", COMPUTE_DONE, 1);
    printer.print_field("iteration_done", iteration_done, 1);
  endfunction

  // Optional: Add constraints here if needed

endclass
