// Kernel memory read sequence driving the read operation to the kernel memory
// interface
class dpmem_read_sequence#(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_sequence #(dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  `uvm_object_utils(dpmem_read_sequence#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name = "dpmem_read_sequence");
    super.new(name);
  endfunction

  task body();
    dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

    forever begin
      req = dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH)::type_id::create("req");

      // Read transaction signals
      req.RCSN = 0; // active low read chip select
      req.RA = $urandom_range(0, 512);
      req.WCSN = 1; // inactive write chip select
      req.WA = 0;
      req.M = '0;   // all 0's mask
      req.D = '0;   // data input zero for read
      req.sample_read_data = 1; // sample read data by default

      start_item(req);
      finish_item(req);

      // sampled Q will be updated by driver
    end
  endtask

endclass
