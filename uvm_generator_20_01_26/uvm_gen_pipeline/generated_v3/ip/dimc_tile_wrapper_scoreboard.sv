//------------------------------------------------------------------------------
// dimc_tile_wrapper_scoreboard.sv
// UVM Scoreboard for dimc_tile_wrapper_m
// Compares DUT output against expected values from C model
//------------------------------------------------------------------------------

`ifndef DIMC_TILE_WRAPPER_SCOREBOARD_SV
`define DIMC_TILE_WRAPPER_SCOREBOARD_SV

import uvm_pkg::*;
`include "uvm_macros.svh"

// Transaction type for output buffer (assume ostream_transaction#(64) exists)
typedef ostream_transaction#(64) ostream_trx_t;

class dimc_tile_wrapper_scoreboard extends uvm_scoreboard;

  // UVM Factory Registration
  `uvm_component_utils(dimc_tile_wrapper_scoreboard)

  // Analysis imp port for receiving output buffer transactions
  uvm_analysis_imp #(ostream_trx_t, dimc_tile_wrapper_scoreboard) output_buffer_ap;

  // Expected output storage
  bit [63:0] expected_data_q[$]; // Queue of expected 64b values

  // Pass/fail statistics
  int unsigned num_compares;
  int unsigned num_mismatches;

  // File name for expected output
  string expected_file = "output_buffer_expected_out_psout_hex.txt";

  // Constructor
  function new(string name = "dimc_tile_wrapper_scoreboard", uvm_component parent = null);
    super.new(name, parent);
    output_buffer_ap = new("output_buffer_ap", this);
    num_compares = 0;
    num_mismatches = 0;
  endfunction

  // Build phase: can set expected_file via config_db if desired
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // Optionally override expected_file via config_db
    void'(uvm_config_db#(string)::get(this, "", "expected_file", expected_file));
  endfunction

  // Start of simulation: read expected output from file
  function void start_of_simulation_phase(uvm_phase phase);
    super.start_of_simulation_phase(phase);
    read_expected_output();
  endfunction

  // Read expected output from file into expected_data_q
  function void read_expected_output();
    int fd;
    string line;
    bit [63:0] data;
    int count = 0;

    expected_data_q.delete();

    fd = $fopen(expected_file, "r");
    if (fd == 0) begin
      `uvm_fatal(get_type_name(), $sformatf("Failed to open expected output file: %s", expected_file))
      return;
    end

    while ($fgets(line, fd)) begin
      // Remove whitespace and comments
      line = line.tolower().split(" ")[0];
      if (line.len() == 0) continue;
      if (!$sscanf(line, "%h", data)) begin
        `uvm_warning(get_type_name(), $sformatf("Invalid line in expected file: %s", line))
        continue;
      end
      expected_data_q.push_back(data);
      count++;
    end

    $fclose(fd);

    if (count != 32) begin
      `uvm_warning(get_type_name(), $sformatf("Expected 32 entries in expected output file, got %0d", count))
    end else begin
      `uvm_info(get_type_name(), $sformatf("Loaded %0d expected output entries from %s", count, expected_file), UVM_MEDIUM)
    end
  endfunction

  // Analysis write method: compare DUT output to expected
  virtual function void write(ostream_trx_t t);
    bit [63:0] expected;
    bit [63:0] actual;

    if (expected_data_q.size() == 0) begin
      `uvm_error(get_type_name(), "No more expected data to compare against.")
      num_mismatches++;
      return;
    end

    expected = expected_data_q.pop_front();
    actual   = t.data;

    num_compares++;

    if (actual !== expected) begin
      num_mismatches++;
      `uvm_error(get_type_name(),
        $sformatf("Output mismatch at index %0d: expected=0x%016h, actual=0x%016h",
                  num_compares-1, expected, actual))
    end else begin
      `uvm_info(get_type_name(),
        $sformatf("Output match at index %0d: value=0x%016h", num_compares-1, actual), UVM_LOW)
    end
  endfunction

  // Report phase: print summary
  function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    if (num_mismatches == 0 && num_compares == 32) begin
      `uvm_info(get_type_name(), "All output buffer comparisons PASSED.", UVM_NONE)
    end else begin
      `uvm_error(get_type_name(),
        $sformatf("Output buffer comparison FAILED: %0d mismatches out of %0d compares", num_mismatches, num_compares))
    end
  endfunction

endclass

`endif // DIMC_TILE_WRAPPER_SCOREBOARD_SV