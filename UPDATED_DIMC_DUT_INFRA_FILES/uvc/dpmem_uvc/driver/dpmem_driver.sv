// Kernel memory driver which gets dpmem_seq_item from the
// dpmem_sequencer and drives it to the dpmem_vif interface
// signals
class dpmem_driver #(int DATA_WIDTH=32, int ADDR_WIDTH=32) extends uvm_driver #(dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH));

  virtual dpmem_if#(DATA_WIDTH,ADDR_WIDTH) vif;

  `uvm_component_utils(dpmem_driver#(DATA_WIDTH,ADDR_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    //if (!uvm_config_db#(virtual dpmem_if)::get(this, "", "dpmem_vif", vif))
     // `uvm_fatal("NOVIF", "Virtual interface must be set for dpmem_driver")
  endfunction

  task run_phase(uvm_phase phase);
    dpmem_seq_item#(DATA_WIDTH,ADDR_WIDTH) req;

    forever begin
      seq_item_port.get_next_item(req);

      // Drive all signals on first clock edge
      @(posedge vif.dpmem_clk);
      vif.WCSN <= req.WCSN;
      vif.WA <= req.WA;
      vif.WEN <= req.WEN;
      vif.RCSN <= req.RCSN;
      vif.RA <= req.RA;
      vif.M <= req.M;
      vif.D <= req.D;

      // If this is a read transaction and sample_read_data is set, sample Q on next clock edge
      //if (req.RCSN == 0 && req.sample_read_data) begin
      //  @(posedge vif.dpmem_clk);
      //  req.Q = vif.cb.Q;
      //end
      // If read but no sampling requested, no wait
      //else if (req.RCSN == 0 && !req.sample_read_data) begin
        // no sampling, no wait
      //end
      // For write transaction, hold signals for one clock cycle
     // else begin
     //   @(posedge vif.dpmem_clk);
     // end

      seq_item_port.item_done();
    end
  endtask

endclass
