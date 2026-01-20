// Computation directed write sequence which drives computation signals on
// computation_if interface
class computation_configure_write_seq extends uvm_sequence #(computation_seq_item);

  `uvm_object_utils(computation_configure_write_seq)

  function new(string name = "computation_configure_write_seq");
    super.new(name);
  endfunction

  int mode;
  int sign_8b;
  int START_COMPUTE;
  int COMPE;
  int PS_FIRST;
  int PS_MODE;
  int PS_LAST;

  // You can add arguments to this task for specific values if needed
  virtual task body();
    computation_seq_item req;

    // Create and randomize the sequence item
    req = computation_seq_item::type_id::create("req");
    //if (!req.randomize()) begin
    //  `uvm_error("COMPUTE_WRITE_SEQ", "Randomization failed for computation_seq_item")
    //end

    // Optionally, you can assign specific values instead of randomization:
       req.K_DIM         = 32;
       req.START_COMPUTE = START_COMPUTE;
       req.COMPE         = COMPE;
       req.PS_FIRST      = PS_FIRST;
       req.PS_MODE       = PS_MODE;
       req.PS_LAST       = PS_LAST;
       req.MODE          = mode;
       req.sign_8b       = sign_8b;
       req.CONT_COMP     = 0;
       req.iteration     = 8'd0;

    start_item(req);
    finish_item(req);

    // Optionally, print the item for debug
    req.print();
  endtask

endclass
