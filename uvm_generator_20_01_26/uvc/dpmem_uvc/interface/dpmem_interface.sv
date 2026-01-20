// dpmem_if interface which gets instantiated in testbench and gets
// connected with the DUT input and output
//
// WCSN - Write chip select (active low) for kernel memory.
// WA - Write address bus for kernel memory.
// RCSN - Read chip select (active low) for kernel memory.
// RA - Read address bus for kernel memory.
// M - Mask or modifier input for kernel memory data operations.
// D - Input data bus to kernel memory (64-bit).
// Q - Output data bus from kernel memory (64-bit).
// WEN - Write enable for kernel memory.
// RM - Read mask or mode for kernel memory.
// WM - Write mask or mode for kernel memory.
// dpmem_clk - Write clock for kernel memory.
// SELCK - Select clock signal for kernel memory or related logic.
// TBYPASS - Test bypass signal, possibly bypassing certain logic for testing.
// HS - High-speed mode enable or related signal.
// LS - Low-speed mode enable or related signal.
// SLEEP - Sleep mode enable signal for power saving. 
// RES_IN - Input resolution or reserved bits for kernel memory operations.
// RES_OUT - Output resolution or status bits from kernel memory.

interface dpmem_if #(int DATA_WIDTH=32, int ADDR_WIDTH=32) (input logic dpmem_clk);

  logic WCSN;
  logic [ADDR_WIDTH-1:0] WA;
  logic RCSN;
  logic [ADDR_WIDTH-1:0] RA;
  logic [DATA_WIDTH-1:0] M;
  logic [DATA_WIDTH-1:0] D;
  logic [DATA_WIDTH-1:0] Q;
  logic WEN;
  logic RM;
  logic WM;

  logic SELCK;
  logic TBYPASS;
  logic HS;
  logic LS;
  logic SLEEP;
  logic [9:0] RES_IN;
  logic [9:0] RES_OUT;

  // Clocking block for synchronous access
  clocking cb @(posedge dpmem_clk);
    output WCSN, WA, RCSN, RA, M, D,SELCK,TBYPASS,HS,LS,SLEEP, RES_IN, WEN, RM, WM ;
    input  RES_OUT, Q;
  endclocking

  initial
    begin
       SELCK = 1'b0;
       TBYPASS = 1'b0;
       HS = 1'b0;
       LS = 1'b0;
       SLEEP = 1'b0;
       RES_IN = 10'b0;

       WCSN = 1'b1;
       WA   = '0;
       RCSN = 1'b1;
       RA   = '0;
       M    = '0;
       D    = '0;
       RM   = 1'b0;
       WM   = 1'b0;

    end

endinterface
