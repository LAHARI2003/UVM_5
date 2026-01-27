//------------------------------------------------------------------------------
// dimc_tile_wrapper_scoreboard.sv
// UVM Scoreboard for dimc_tile_wrapper_m
// Compares DUT output against expected values from C model
//------------------------------------------------------------------------------

`ifndef DIMC_TILE_WRAPPER_SCOREBOARD_SV
`define DIMC_TILE_WRAPPER_SCOREBOARD_SV

import uvm_pkg::*;
`include "uvm_macros.svh"

// Assume ostream_transaction is the transaction type for output buffer
// If not, replace with the correct transaction class
typedef class ostream_transaction;

class dimc_tile_wrapper_scoreboard extends uvm_scoreboard;

  // UVM Factory Registration
  `uvm_component_utils(dimc_tile_wrapper_scoreboard)

  // Analysis imp port for receiving output buffer transactions from monitor
  uvm_analysis_imp_ostream #(ostream_transaction, dimc_tile_wrapper_scoreboard) output_buffer_ap;

  // Expected output storage
  bit [63:0] expected_data_q[$]; // Queue of expected data
  int expected_count;
  int received_count;
  int pass_count;
  int fail_count;

  string expected_output_file = "output_buffer_expected_out_psout_hex.txt";

  // Constructor
  function new(string name, uvm_component parent);
    super.new(name, parent);
    output_buffer_ap = new("output_buffer_ap", this);
    expected_count = 0;
    received_count = 0;
    pass_count = 0;
    fail_count = 0;
  endfunction

  // Build phase: Read expected output from file
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    read_expected_output();
  endfunction

  // Read expected output values from file
  function void read_expected_output();
    int fd;
    string line;
    bit [63:0] data;
    int i;

    fd = $fopen(expected_output_file, "r");
    if (fd == 0) begin
      `uvm_fatal(get_type_name(), $sformatf("Failed to open expected output file: %s", expected_output_file))
    end

    i = 0;
    while (!$feof(fd) && i < 32) begin
      line = "";
      void'($fgets(line, fd));
      if (line.len() == 0) continue;
      if (!$sscanf(line, "%h", data)) begin
        `uvm_error(get_type_name(), $sformatf("Failed to parse line %0d in expected output file: %s", i, line))
        continue;
      end
      expected_data_q.push_back(data);
      i++;
    end
    expected_count = expected_data_q.size();
    $fclose(fd);

    `uvm_info(get_type_name(), $sformatf("Loaded %0d expected output values from %s", expected_count, expected_output_file), UVM_MEDIUM)
  endfunction

  // Analysis write method: Compare DUT output to expected
  virtual function void write(output_buffer_ap.T t);
    bit [63:0] expected;
    bit [63:0] actual;

    received_count++;

    if (expected_data_q.size() == 0) begin
      `uvm_error(get_type_name(), $sformatf("Received extra output transaction %0d: no more expected data", received_count))
      fail_count++;
      return;
    end

    expected = expected_data_q.pop_front();
    actual   = t.data; // Assumes ostream_transaction has 'data' property

    if (actual === expected) begin
      pass_count++;
      `uvm_info(get_type_name(), $sformatf("PASS: Output[%0d] = 0x%016h (expected 0x%016h)", received_count-1, actual, expected), UVM_LOW)
    end else begin
      fail_count++;
      `uvm_error(get_type_name(), $sformatf("FAIL: Output[%0d] = 0x%016h (expected 0x%016h)", received_count-1, actual, expected))
    end
  endfunction

  // Report phase: Print scoreboard results
  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);

    if (fail_count == 0 && received_count == expected_count) begin
      `uvm_info(get_type_name(), $sformatf("SCOREBOARD PASSED: All %0d outputs matched expected values.", pass_count), UVM_NONE)
    end else begin
      `uvm_error(get_type_name(), $sformatf("SCOREBOARD FAILED: %0d/%0d outputs matched, %0d mismatches, %0d expected, %0d received.",
        pass_count, received_count, fail_count, expected_count, received_count))
    end

    if (expected_data_q.size() > 0) begin
      `uvm_error(get_type_name(), $sformatf("SCOREBOARD: %0d expected outputs were not received from DUT.", expected_data_q.size()))
    end
  endfunction

endclass : dimc_tile_wrapper_scoreboard

`endif // DIMC_TILE_WRAPPER_SCOREBOARD_SV