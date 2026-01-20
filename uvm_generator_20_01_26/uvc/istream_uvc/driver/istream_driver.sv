// istream_driver which gets istream_seq_item from the
// istream_sequencer and drives it to the istream_if interface
// signals 
class istream_driver #( int DATA_WIDTH =32) extends uvm_driver #(istream_seq_item#(DATA_WIDTH));

  virtual istream_if#(DATA_WIDTH) vif;

  `uvm_component_utils(istream_driver#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    //if (!uvm_config_db#(virtual istream_if)::get(this, "", "istream_vif", vif))
      //`uvm_fatal("NOVIF", "Virtual interface must be set for istream_driver")
  endfunction

  task run_phase(uvm_phase phase);
    istream_seq_item #(DATA_WIDTH) req;

    forever begin
      seq_item_port.get_next_item(req);

      // Wait for feat_ready to be high
      @(posedge vif.istream_clk);
      if ( req.istream_valid == 1'b1 ) begin
        wait (vif.istream_ready == 1);
      end

      // Drive feat_valid and feat_data on clock edge
      vif.istream_valid <= req.istream_valid;
      vif.istream_data <= req.istream_data;

      // Wait one clock cycle to keep valid and data stable
      //@(posedge vif.feature_buffer_clk);

      // De-assert feat_valid after one cycle or keep it asserted as per protocol
      //vif.cb.feat_valid <= 0;

      seq_item_port.item_done();
    end
  endtask

endclass
