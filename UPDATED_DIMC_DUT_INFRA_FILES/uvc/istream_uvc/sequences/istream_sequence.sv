// this istream_sequence randomizes the istream_seq_item and pass it to the istream_sequencer
class istream_sequence extends uvm_sequence #(istream_seq_item);

  `uvm_object_utils(istream_sequence)

  function new(string name = "istream_sequence");
    super.new(name);
  endfunction

  task body();
    istream_seq_item#(32) req;
    forever begin
      req = istream_seq_item#(32)::type_id::create("req");
      assert(req.randomize());
      start_item(req);
      finish_item(req);
    end
  endtask

endclass
