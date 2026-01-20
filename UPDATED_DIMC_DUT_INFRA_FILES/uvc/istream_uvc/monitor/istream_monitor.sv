class istream_monitor #(int DATA_WIDTH = 32) extends uvm_monitor;

  // Virtual interface to observe signals
  virtual istream_if#(DATA_WIDTH) vif;

  // Analysis port to send captured transactions
  uvm_analysis_port#(istream_seq_item#(DATA_WIDTH)) istream_wr_port;

  `uvm_component_utils(istream_monitor#(DATA_WIDTH))

  function new(string name, uvm_component parent);
    super.new(name, parent);
    istream_wr_port = new("istream_wr_port", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // Get the virtual interface handle from config DB
    //if (!uvm_config_db#(virtual istream_if#(DATA_WIDTH))::get(this, "", "istream_vif", vif)) begin
     // `uvm_fatal("NOVIF", "Virtual interface must be set for istream_monitor")
    //end
  endfunction

  task run_phase(uvm_phase phase);
    istream_seq_item#(DATA_WIDTH) trans;

    forever begin
      @(negedge vif.istream_clk);

      // Check if both valid and ready are asserted
      if ((vif.istream_valid == 1'b1) && (vif.istream_ready == 1'b1)) begin
        // Create a new transaction object
        trans = istream_seq_item#(DATA_WIDTH)::type_id::create("trans");

        // Capture the signals
        trans.istream_valid = vif.istream_valid;
        trans.istream_data  = vif.istream_data;
        trans.istream_ready = vif.istream_ready;

        trans.print();
        // Print the transaction details
        `uvm_info("ISTREAM_MON", $sformatf("Captured transaction: valid=%0b, ready=%0b, data=0x%0h",
                 trans.istream_valid, trans.istream_ready, trans.istream_data), UVM_MEDIUM) 
        // Send transaction to analysis port
        istream_wr_port.write(trans);
      end
    end
  endtask

endclass
