//for input stall

class op_stall_rand extends uvm_sequence_item;
	
	`uvm_object_utils(op_stall_rand)
	
    	function new(string name = "op_stall_rand");
        	super.new(name);
    	endfunction

        rand bit [4:0] 		burst_len;
        rand bit [6:0]		inter_bus_latency;

		     	
	 // Constraint to ensure each 16-bit segment is covered
  	constraint ip_stall_rand_c {
		burst_len dist
		{
			[0:10] :/ 30,
			[11:20] :/30,
			[21:30] :/40
		};

		inter_bus_latency dist
		{
			[0:20] :/ 25,
			[21:40] :/25,
			[41:63] :/25,
			[64:100] :/25
		};
    	  }
	
	// Constraint to ensure feat_data_burst_len is less than feat_inter_bus_latency
  	constraint len_lt_latency {
    		burst_len < inter_bus_latency;
  	}

  	// Solve before constraint to ensure feat_data_burst_len is generated before feat_inter_bus_latency
  	constraint solve_order {
    		solve burst_len before inter_bus_latency;
  	}


endclass
 















