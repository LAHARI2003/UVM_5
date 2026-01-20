// Kernel memory write sequence driving the write operation to the kernel
// memory interface

class dpmem_write_sequence#(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence #(dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_object_utils(dpmem_write_sequence#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "dpmem_write_sequence");
    super.new(name);
  endfunction

  task body();
    dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

    forever begin
      req = dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");

      // Write transaction signals
      req.WCSN = 0; // active low write chip select
      req.WA = $urandom_range(0, 512);
      req.RCSN = 1; // inactive read chip select
      req.RA = 0;
      req.M = '1;   // all 1's mask
      req.D = $urandom();
      req.sample_read_data = 0; // no sampling for write

      start_item(req);
      finish_item(req);
    end
  endtask

endclass
