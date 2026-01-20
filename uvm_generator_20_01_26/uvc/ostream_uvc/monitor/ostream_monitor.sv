class ostream_monitor #(int DATA_WIDTH = 32) extends uvm_monitor;

  // Virtual interface to observe signals
  virtual ostream_if#(DATA_WIDTH) vif;

  // Analysis port to send captured transactions
  uvm_analysis_port#(ostream_seq_item#(DATA_WIDTH)) ostream_rd_port;

  `uvm_component_utils(ostream_monitor#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ostream_rd_port = new("ostream_rd_port", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // Get the virtual interface handle from config DB
    //if (!uvm_config_db#(virtual ostream_if#(DATA_WIDTH))::get(this, "", "ostream_vif", vif)) begin
     // `uvm_fatal("NOVIF", "Virtual interface must be set for ostream_monitor")
    //end
  endfunction

  task run_phase(uvm_phase phase);
    ostream_seq_item#(DATA_WIDTH) trans;

    forever begin
      @(negedge vif.ostream_clk);

      // Sample and check conditions
      // if ((vif.ostream_last == 1'b1) && (vif.ostream_ready == 1'b1) && (vif.ostream_valid == 1'b1)) begin
      if (vif.ostream_valid == 1'b1) begin
        // Create a new transaction object
        trans = ostream_seq_item#(DATA_WIDTH)::type_id::create("trans");

        // Capture the signals
        trans.ostream_valid = vif.ostream_valid;
        trans.ostream_data  = vif.ostream_data;
        trans.ostream_first = vif.ostream_first;
        trans.ostream_last  = vif.ostream_last;
        trans.ostream_ready = vif.ostream_ready;

        // Print captured transaction info
       // `uvm_info("OSTREAM_MON", $sformatf(
       //   "Captured transaction: valid=%0b, ready=%0b, first=%0b, last=%0b, data=0x%0h",
       //   trans.ostream_valid, trans.ostream_ready, trans.ostream_first, trans.ostream_last, trans.ostream_data), UVM_MEDIUM)

        // Send transaction to analysis port
        ostream_rd_port.write(trans);
      end
    end
  endtask

endclass
