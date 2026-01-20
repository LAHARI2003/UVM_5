// spmem write sequence which drives write transaction to spmem interface

class spmem_write_sequence #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence #(spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_object_utils(spmem_write_sequence#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "spmem_write_sequence");
    super.new(name);
  endfunction

  task body();
    spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

    forever begin
      req = spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");
      // Drive write signals
      req.spmem_wr_n = 0;       // active low write
      req.spmem_cs_n = 0;       // active low chip select
      req.spmem_be = '1;        // all 1's (64-bit)
      req.spmem_addr = $urandom_range(0, 16);
      req.spmem_d = $urandom();

      start_item(req);
      finish_item(req);
    end
  endtask

endclass
