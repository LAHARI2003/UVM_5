// ostream_sequencer declaration which drives the ostream_seq_item
// to the ostream_driver
class ostream_sequencer #(int DATA_WIDTH = 32) extends uvm_sequencer #(ostream_seq_item#(DATA_WIDTH));

  `uvm_component_utils(ostream_sequencer#(DATA_WIDTH))

   // Virtual interface
   virtual ostream_if#(DATA_WIDTH) vif;

  function new(string name = "ostream_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction

   function void build_phase(uvm_phase phase);
      super.build_phase(phase);
 		
      // Get virtual interface from config_db
      //if (!uvm_config_db#(virtual ostream_if#(DATA_WIDTH) )::get(this, "", "ostream_vif", vif))
        // `uvm_fatal("NOVIF", "Virtual interface must be set for feature_buffer_agent")

      endfunction

endclass
