// istream_if interface which gets instantiated in testbench and gets
// connected with the DUT input and output
// istream_valid - Indicates that the input stream input data is valid and ready to be consumed.
// istream_data - Input stream data bus carrying 64-bit stream data.
// istream_ready - Indicates that the module is ready to accept new stream data.
// istream_buff_full - Indicates the steam_input buffer is full and cannot accept more data
// istream_buff_empty - Indicates the stream input buffer is empty.

interface istream_if #(parameter DATA_WIDTH = 32) (input logic istream_clk);
//interface istream_if (input logic istream_clk);

  logic istream_valid;
  logic [DATA_WIDTH-1:0] istream_data;
  //logic [63:0] istream_data;
  logic istream_ready;

 // logic istream_buff_full;
 // logic istream_buff_empty;

  // Reset logic or other signals can be added here if needed

  // Clocking block for synchronous access
  clocking cb @(posedge istream_clk);
    output istream_valid, istream_data;
    //input istream_ready,istream_buff_full,istream_buff_empty;
    input istream_ready;
    
  endclocking

  initial
   begin
     istream_valid = 1'b0;
     istream_data = 64'h0;
   end

endinterface
