class dimc_tile_wrapper_virtual_sequencer extends uvm_sequencer;
    
    `uvm_component_utils(dimc_tile_wrapper_virtual_sequencer)

    istream_sequencer#(64)         seqr_feature_buffer;
    istream_sequencer#(32)         seqr_psin;
    dpmem_sequencer#(64,9)         seqr_kernel_mem;
    spmem_sequencer#(64,4)         seqr_addin;
    regbank_sequencer              seqr_computation;
    ostream_sequencer#(64)         seqr_output_buffer;

    // Virtual interface
    virtual dimc_tile_wrapper_if vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
    
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get virtual interface from config_db
        if (!uvm_config_db#(virtual dimc_tile_wrapper_if)::get(this, "", "dimc_tile_wrapper_vif", vif))
            `uvm_fatal("NOVIF", "Virtual interface must be set for dimc_tile_wrapper_m environment")
    endfunction

endclass