// Kernel memory write sequence driving the write operation to the kernmel
// memory interface

class dpmem_directed_write_sequence#(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence #(dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_object_utils(dpmem_directed_write_sequence#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "dpmem_directed_write_sequence");
    super.new(name);
  endfunction
  
  logic [DATA_WIDTH-1:0] ker_data_ip [];
  int i;
  int size;
  string file_path;

  dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

  task body();
   
    ker_data_ip = new[size];
    

    //$readmemh("./input_data/kernel_data_unique_64x512.txt", ker_data_ip) ;
    $readmemh(file_path, ker_data_ip) ;

    
    for(i = 0; i<size; i++)
      begin : kernel_wr
        req = dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");

        // Write transaction signals
        req.WCSN = 0; // active low write chip select
        req.WEN = 1'b1;
        req.WA = i;
        req.RCSN = 1; // inactive read chip select
        req.RA = 0;
        req.M = '0;   // all 1's mask
        req.D = ker_data_ip[i];
        req.sample_read_data = 0; // no sampling for write

        start_item(req);
        finish_item(req);
    end : kernel_wr

        req = dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");

        // Write transaction signals
        req.WCSN = 1; // active low write chip select
        req.WEN = 1'b1;
        req.WA = 0;
        req.RCSN = 1; // inactive read chip select
        req.RA = 0;
        req.M = '0;   // all 1's mask
        req.D = 64'h0;
        req.sample_read_data = 0; // no sampling for write

        start_item(req);
        finish_item(req);

 endtask

endclass
