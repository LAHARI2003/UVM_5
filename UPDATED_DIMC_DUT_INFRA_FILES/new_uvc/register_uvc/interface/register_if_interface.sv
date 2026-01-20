// register_if which gets instantiated in testbench and gets
// connected with the DUT input and output
//
interface register_if(input logic register_clk);

  // Output signals (driven by DUT, monitored by TB)
  logic [31:0]  register;

  // Input signals (driven by TB, sampled by DUT)
  logic [31:0]  register_status;

  // Clocking block for synchronous access (example for TB driver)
  clocking cb @(posedge register_clk);
    output register;
    input  register_status;
  endclocking

  initial
    begin
      register = 32'h0;
    end

endinterface
