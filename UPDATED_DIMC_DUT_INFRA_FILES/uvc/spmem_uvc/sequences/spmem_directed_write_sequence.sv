// spmem write sequence which drives write transaction to spmem interface

class spmem_directed_write_sequence #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence #(spmem_seq_item);

  `uvm_object_utils(spmem_directed_write_sequence#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "spmem_directed_write_sequence");
    super.new(name);
  endfunction
  
  logic [DATA_WIDTH-1:0] spmem_data_ip [];
  int i;
  spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

  int size;
  string file_path;

  task body();
   begin
    spmem_data_ip = new[size];
   //$readmemh("./input_data/spmem_data_unique_64x16.txt", spmem_data_ip) ;
   $readmemh(file_path, spmem_data_ip) ;
    

  for(i = 0; i<size; i++)
   begin

      req = spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");
      // Drive write signals
      req.spmem_wr_n = 0;       // active low write
      req.spmem_cs_n = 0;       // active low chip select
      req.spmem_be = '0;        // all 1's (64-bit)
      req.spmem_addr = i;
      req.spmem_d = spmem_data_ip[i];

      start_item(req);
      finish_item(req);
    end

      req = spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");
      // Drive write signals
      req.spmem_wr_n = 1;       // active low write
      req.spmem_cs_n = 1;       // active low chip select
      req.spmem_be = '0;        // all 1's (64-bit)
      req.spmem_addr = 0;
      req.spmem_d = 64'h0;

      start_item(req);
      finish_item(req);

end
  endtask

endclass
