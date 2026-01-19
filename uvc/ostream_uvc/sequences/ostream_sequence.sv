// Output buffer read sequence which reads the odata from the output buffer
// interface
class ostream_sequence #(int DATA_WIDTH = 32) extends uvm_sequence #(ostream_seq_item);

  `uvm_object_utils(ostream_sequence)

  function new(string name = "ostream_sequence");
    super.new(name);
  endfunction

  task body();
    ostream_seq_item req;

    forever begin
      req = ostream_seq_item::type_id::create("req");
      assert(req.randomize() with { ostream_ready inside {[0:1]}; }); // randomize out_ready

      start_item(req);
      finish_item(req);

      // Here you can use sampled signals from req.out_valid, out_data, etc.
      `uvm_info("OUTPUT_SEQ", $sformatf("Sampled: valid=%0b data=%0h first=%0b last=%0b", req.ostream_valid, req.ostream_data, req.ostream_first, req.ostream_last), UVM_LOW)
    end
  endtask

endclass
