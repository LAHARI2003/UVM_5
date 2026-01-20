// register_seq_item fields
// register_seq_item fields driven by the driver to register_if interface


class register_seq_item extends uvm_sequence_item;

  // Output signals (driven by sequence/driver)
  rand bit [31:0]  register;
  
  `uvm_object_utils(register_seq_item)

  function new(string name = "register_seq_item");
    super.new(name);
  endfunction

  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field("register", register, 32);
  endfunction

  // Optional: Add constraints here if needed

endclass
