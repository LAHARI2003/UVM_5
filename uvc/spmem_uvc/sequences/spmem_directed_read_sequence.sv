// spmem read sequence which drives read transaction to spmem interface
class spmem_directed_read_sequence #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence #(spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_object_utils(spmem_directed_read_sequence#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "spmem_directed_read_sequence");
    super.new(name);
  endfunction

  spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;
  int size;
  int i;

  task body();
    
  for(i = 0; i<size; i++)
      begin
      req = spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");
      // Drive read signals
      req.spmem_wr_n = 1;       // active high read (not write)
      req.spmem_cs_n = 0;       // active low chip select
      req.spmem_be = 64'b0;     // all 0's
      //req.spmem_addr = $urandom_range(0, 16);
      req.spmem_addr = i;
      req.spmem_d = 64'b0;      // data input zero for read

      start_item(req);
      finish_item(req);

      // The sampled spmem_q will be updated by the driver
    end

      req = spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");
      // Drive read signals
      req.spmem_wr_n = 1;       // active high read (not write)
      req.spmem_cs_n = 1;       // active low chip select
      req.spmem_be = 64'b0;     // all 0's
      //req.spmem_addr = $urandom_range(0, 16);
      req.spmem_addr = 0;
      req.spmem_d = 64'b0;      // data input zero for read

      start_item(req);
      finish_item(req);
    
  endtask

endclass

