// ostream_driver which gets ostream_seq_item from the
// ostream_sequencer and drives it to the ostream_vif interface
// signals

class ostream_driver #(int DATA_WIDTH = 32) extends uvm_driver #(ostream_seq_item#(DATA_WIDTH));

  virtual ostream_if#(DATA_WIDTH) vif;

  `uvm_component_utils(ostream_driver#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    //if (!uvm_config_db#(virtual ostream_if#(DATA_WIDTH))::get(this, "", "ostream_vif", vif))
      //`uvm_fatal("NOVIF", "Virtual interface must be set for ostream_driver")
  endfunction

  task run_phase(uvm_phase phase);
    ostream_seq_item#(DATA_WIDTH) req;
    ostream_seq_item#(DATA_WIDTH) rsp;

    forever begin
      seq_item_port.get_next_item(req);

      // Drive ostream_ready as per sequence item
      vif.ostream_ready <= req.ostream_ready;

      // Sample ostream_valid, ostream_data, ostream_first, ostream_last on every clock cycle
      @(posedge vif.ostream_clk);

      // Create a response item
      rsp = ostream_seq_item#(DATA_WIDTH)::type_id::create("rsp");
      rsp.copy(req);
    rsp.set_id_info(req);

    rsp.ostream_valid = vif.ostream_valid;
    rsp.ostream_data  = vif.ostream_data;
    rsp.ostream_first = vif.ostream_first;
    rsp.ostream_last  = vif.ostream_last;

    seq_item_port.put_response(rsp);

      // Inform that item is done with updated sampled signals
      seq_item_port.item_done();
    end
  endtask

endclass
