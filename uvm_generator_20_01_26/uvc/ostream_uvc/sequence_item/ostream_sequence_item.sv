// ostream_seq_item fields
// ostream_seq_item fields driven by the driver to ostream_if interface
//
// // out_valid - Indicates that the output data is valid and ready to be consumed.
// out_data - Output data bus carrying 64-bit data from the SOUT buffer.
// out_first - Indicates the first data word in an output sequence or packet.
// out_last - Indicates the last data word in an output sequence or packet.
// out_ready - Indicates that the receiver is ready to accept output data. On the cycle the valid goes low it the interface should be able to access 2 valid data.

class ostream_seq_item #(int DATA_WIDTH = 32 ) extends uvm_sequence_item;

  // Driven by sequence (driver drives ostream_ready)
  rand bit ostream_ready;

  // Sampled by driver (driver samples these signals and updates the item)
  bit ostream_valid;
  bit [DATA_WIDTH-1:0] ostream_data;
  bit ostream_first;
  bit ostream_last;

  `uvm_object_utils(ostream_seq_item#(DATA_WIDTH))

  function new(string name = "ostream_seq_item");
    super.new(name);
  endfunction

  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field("ostream_ready", ostream_ready, 1);
    printer.print_field("ostream_valid", ostream_valid, 1);
    printer.print_field("ostream_data", ostream_data, DATA_WIDTH);
    printer.print_field("ostream_first", ostream_first, 1);
    printer.print_field("ostream_last", ostream_last, 1);
  endfunction

  	//Deep Copy method
  	function ostream_seq_item#(DATA_WIDTH) deep_copy();
    		ostream_seq_item#(DATA_WIDTH) new_obj_ostream_seq_item = ostream_seq_item#(DATA_WIDTH)::type_id::create("new_obj_ostream_seq_item");
    		  
		  new_obj_ostream_seq_item.ostream_ready			= this.ostream_ready;
		  new_obj_ostream_seq_item.ostream_valid			= this.ostream_valid;
		  new_obj_ostream_seq_item.ostream_data			        = this.ostream_data;
		  new_obj_ostream_seq_item.ostream_first			= this.ostream_first;
		  new_obj_ostream_seq_item.ostream_last			        = this.ostream_last;


		return new_obj_ostream_seq_item;

  	endfunction     	

endclass

