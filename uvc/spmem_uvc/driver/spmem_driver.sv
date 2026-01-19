// spmem_driver which gets spmem_seq_item from the
// spmem_sequencer and drives it to the spmem_vif interface
// signals
class spmem_driver #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_driver #(spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  virtual spmem_if#(DATA_WIDTH,ADDR_WIDTH) vif;

  `uvm_component_utils(spmem_driver#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    //if (!uvm_config_db#(virtual spmem_if)::get(this, "", "spmem_vif", vif))
     // `uvm_fatal("NOVIF", "Virtual interface must be set for spmem_driver")
  endfunction

  task run_phase(uvm_phase phase);
    spmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

    forever begin
      seq_item_port.get_next_item(req);

      // Drive signals on clock edge
      @(posedge vif.spmem_clk);

      vif.cb.spmem_cs_n <= req.spmem_cs_n;
      vif.cb.spmem_addr <= req.spmem_addr;
      vif.cb.spmem_wr_n <= req.spmem_wr_n;
      vif.cb.spmem_be <= req.spmem_be;
      vif.cb.spmem_d <= req.spmem_d;

      // For read, sample spmem_q and update sequence item
      //if (req.spmem_wr_n == 1) begin
      //  @(posedge vif.spmem_clk);
      //  req.spmem_q = vif.cb.spmem_q;
      //end

      // For write, no sampling needed, just one cycle drive assumed
      //else begin
      //  @(posedge vif.spmem_clk);
      //end

      // De-assert chip select after transaction
      //vif.cb.spmem_cs_n <= 1;

      seq_item_port.item_done();
    end
  endtask

endclass
