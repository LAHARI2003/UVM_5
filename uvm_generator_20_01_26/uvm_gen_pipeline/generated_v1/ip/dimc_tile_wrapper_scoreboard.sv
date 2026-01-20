class dimc_tile_wrapper_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(dimc_tile_wrapper_scoreboard)

  // Ports
  uvm_analysis_imp #(uvm_sequence_item, dimc_tile_wrapper_scoreboard) output_buffer_port;

  // Local variables
  protected string expected_output_file_name = "output_buffer_expected_out_psout_hex.txt";
  protected int unsigned expected_outputs[$];
  protected int num_mismatches = 0;
  protected int num_comparisons = 0;

  // Constructor
  function new(string name, uvm_component parent);
    super.new(name, parent);
    output_buffer_port = new("output_buffer_port", this);
  endfunction

  // Phase: build_phase
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // Read expected output values from file
    if (!$value$plusargs("expected_output_file_name=%s", expected_output_file_name)) begin
      `uvm_warning(get_type_name(), "Parameter expected_output_file_name not set. Using default.");
    end
    read_expected_outputs_from_file(expected_output_file_name);
  endfunction

  // Function to read expected outputs from file
  protected function void read_expected_outputs_from_file(string file_name);
    int fd, code;
    string line;
    fd = $fopen(file_name, "r");
    if (fd == 0) begin
      `uvm_error(get_type_name(), $sformatf("Failed to open expected output file: %s", file_name));
      return;
    end
    while (!$feof(fd)) begin
      code = $fgets(line, fd);
      expected_outputs.push_back($sscanf(line, "%h"));
    end
    $fclose(fd);
  endfunction

  // Method: write
  // This method is called by the analysis port with transaction items
  virtual function void write(uvm_sequence_item item);
    uvm_sequence_item trans;
    bit [63:0] received_data;
    bit [63:0] expected_data;

    if (!$cast(trans, item)) begin
      `uvm_error(get_type_name(), "write() received non-uvm_sequence_item!");
      return;
    end

    // Assuming the transaction has a data field
    received_data = trans.data;

    // Get expected data
    if (num_comparisons < expected_outputs.size()) begin
      expected_data = expected_outputs[num_comparisons];
      num_comparisons++;

      // Compare received data with expected data
      if (received_data !== expected_data) begin
        `uvm_error(get_type_name(), $sformatf("Mismatch detected. Expected: %h, Received: %h", expected_data, received_data));
        num_mismatches++;
      end
    end else begin
      `uvm_warning(get_type_name(), "No more expected data for comparison.");
    end
  endfunction

  // Phase: report_phase
  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info(get_type_name(), $sformatf("Comparison completed. Total comparisons: %d, Mismatches: %d", num_comparisons, num_mismatches), UVM_NONE);
    if (num_mismatches > 0) begin
      `uvm_error(get_type_name(), "Scoreboard detected mismatches. Check logs for details.");
    end else begin
      `uvm_info(get_type_name(), "All data matched expected values.", UVM_NONE);
    end
  endfunction

endclass