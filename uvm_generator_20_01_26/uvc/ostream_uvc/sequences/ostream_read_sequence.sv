// Output buffer read sequence which reads the odata from the output buffer
// interface
class ostream_read_sequence #(int DATA_WIDTH = 32) extends uvm_sequence #(ostream_seq_item#(DATA_WIDTH));

  `uvm_object_utils(ostream_read_sequence#(DATA_WIDTH))

  `uvm_declare_p_sequencer(ostream_sequencer#(DATA_WIDTH))

  function new(string name = "ostream_read_sequence");
    super.new(name);
  endfunction

  int i;
  int size;
 
  task body();
    ostream_seq_item#(DATA_WIDTH) req;
    // Get the response from the driver
      ostream_seq_item#(DATA_WIDTH) rsp;
    //ostream_sequencer my_seqr;

  // Cast p_sequencer to your sequencer type
  //if (!$cast(my_seqr, p_sequencer)) begin
   // `uvm_fatal("SEQ", "Failed to cast p_sequencer to ostream_sequencer")
  //end

 // while (p_sequencer.vif.psout_buff_full != 1) begin
 // @(posedge p_sequencer.vif.ostream_clk);
 // end

  for(i = 0; i<size; i++)
    begin
      req = ostream_seq_item#(DATA_WIDTH)::type_id::create("req");
      //assert(req.randomize() with { out_ready inside {[0:1]}; }); // randomize out_ready
      req.ostream_ready = 1'b1;
      start_item(req);
      finish_item(req);
      get_response(rsp);
      //`uvm_info("OUTPUT_SEQ", $sformatf("Sampled: valid=%0b data=%0h first=%0b last=%0b", 
        //     rsp.ostream_valid, rsp.ostream_data, rsp.ostream_first, rsp.ostream_last), UVM_LOW)
  
  end
      req = ostream_seq_item#(DATA_WIDTH)::type_id::create("req");
      //assert(req.randomize() with { out_ready inside {[0:1]}; }); // randomize out_ready
      req.ostream_ready = 1'b0;
      start_item(req);
      finish_item(req);
      get_response(rsp);
     // `uvm_info("OUTPUT_SEQ", $sformatf("Sampled: valid=%0b data=%0h first=%0b last=%0b", 
       //      rsp.ostream_valid, rsp.ostream_data, rsp.ostream_first, rsp.ostream_last), UVM_LOW)
   
 endtask

endclass
