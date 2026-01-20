// Computation directed write sequence which drives register signals on
// register_if interface
class register_write_seq extends uvm_sequence #(register_seq_item);

  `uvm_object_utils(register_write_seq)

  function new(string name = "register_write_seq");
    super.new(name);
  endfunction

  // You can add arguments to this task for specific values if needed
  virtual task body();
    register_seq_item req;

    // Create and randomize the sequence item
    req = register_seq_item::type_id::create("req");
    if (!req.randomize()) begin
      `uvm_error("COMPUTE_WRITE_SEQ", "Randomization failed for register_seq_item")
    end

    start_item(req);
    finish_item(req);

    // Optionally, print the item for debug
    req.print();
  endtask

endclass
