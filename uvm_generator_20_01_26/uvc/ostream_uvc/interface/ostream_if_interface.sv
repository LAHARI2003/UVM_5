// ostream_if interface which gets instantiated in testbench and gets
// connected with the DUT input and output
//
// ostream_valid - Indicates that the output data is valid and ready to be consumed.
// ostream_data - Output data bus carrying 64-bit data from the SOUT buffer.
// ostream_first - Indicates the first data word in an output sequence or packet.
// ostream_last - Indicates the last data word in an ostreamput sequence or packet.
// ostream_ready - Indicates that the receiver is ready to accept output data. On the cycle the valid goes low it the interface should be able to access 2 valid data.
// sout_buff_full - Indicates the SOUT buffer is full.
// sout_buff_empty - Indicates the SOUT buffer is empty.
// psout_buff_full - Indicates the PSOUT buffer is full.
// psout_buff_empty - Indicates the PSOUT buffer is empty.

//interface ostream_if #(parameter DATA_WIDTH = 32) (input logic ostream_clk);
interface ostream_if #(int DATA_WIDTH = 32) (input logic ostream_clk);

  logic ostream_valid;
  //logic [DATA_WIDTH-1:0] ostream_data;
  logic [DATA_WIDTH-1:0] ostream_data;
  logic ostream_first;
  logic ostream_last;
  logic ostream_ready;

  //logic sout_buff_full;
  //logic sout_buff_empty;
  //logic psout_buff_full;
  //logic psout_buff_empty;

  // Clocking block for synchronous access
  clocking cb @(posedge ostream_clk);
    //input ostream_valid, ostream_data, ostream_first, ostream_last,sout_buff_full,sout_buff_empty,psout_buff_full,psout_buff_empty;
    input ostream_valid, ostream_data, ostream_first, ostream_last;
    output ostream_ready;
  endclocking

  initial
   begin
      ostream_ready = 1'b0;
   end

endinterface

