//------------------------------------------------------------------------------
// dimc_tile_wrapper_scoreboard.sv
// UVM Scoreboard for dimc_tile_wrapper_m
// Compares DUT output against C model expected values
//------------------------------------------------------------------------------

`ifndef DIMC_TILE_WRAPPER_SCOREBOARD_SV
`define DIMC_TILE_WRAPPER_SCOREBOARD_SV

import uvm_pkg::*;
`include "uvm_macros.svh"

// Transaction type for output buffer (64-bit data)
class ostream_txn #(int DATA_WIDTH = 64) extends uvm_sequence_item;
  rand bit [DATA_WIDTH-1:0] data;

  `uvm_object_param_utils(ostream_txn#(DATA_WIDTH))

  function new(string name = "ostream_txn");
    super.new(name);
  endfunction

  function void do_copy(uvm_object rhs);
    ostream_txn#(DATA_WIDTH) rhs_;
    if (!$cast(rhs_, rhs)) return;
    this.data = rhs_.data;
  endfunction

  function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    ostream_txn#(DATA_WIDTH) rhs_;
    if (!$cast(rhs_, rhs)) return 0;
    return (this.data === rhs_.data);
  endfunction

  function string convert2string();
    return $sformatf("data=0x%016x", data);
  endfunction
endclass

//------------------------------------------------------------------------------
// Scoreboard
//------------------------------------------------------------------------------

class dimc_tile_wrapper_scoreboard extends uvm_scoreboard;

  `uvm_component_utils(dimc_tile_wrapper_scoreboard)

  // Analysis imp port for output buffer monitor
  uvm_analysis_imp_ostream #(ostream_txn#(64), dimc_tile_wrapper_scoreboard) output_buffer_ap;

  // Expected output storage
  bit [63:0] expected_data_q[$];
  int expected_count;
  int received_count;
  int pass_count;
  int fail_count;

  string expected_file = "output_buffer_expected_out_psout_hex.txt";

  // Constructor
  function new(string name, uvm_component parent);
    super.new(name, parent);
    output_buffer_ap = new("output_buffer_ap", this);
    expected_count = 0;
    received_count = 0;
    pass_count = 0;
    fail_count = 0;
  endfunction

  // Build phase: read expected output from file
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    read_expected_output();
  endfunction

  // Read expected output from file
  function void read_expected_output();
    int fd;
    string line;
    bit [63:0] value;
    int line_num = 0;

    fd = $fopen(expected_file, "r");
    if (fd == 0) begin
      `uvm_fatal(get_type_name(), $sformatf("Failed to open expected output file: %s", expected_file))
    end

    while (!$feof(fd)) begin
      line = "";
      void'($fgets(line, fd));
      if (line.len() == 0) continue;
      if ($sscanf(line, "%h", value) == 1) begin
        expected_data_q.push_back(value);
        line_num++;
      end
    end
    $fclose(fd);
    expected_count = expected_data_q.size();
    `uvm_info(get_type_name(), $sformatf("Read %0d expected output values from %s", expected_count, expected_file), UVM_MEDIUM)
  endfunction

  // Analysis write method: compare DUT output with expected
  function void write_ostream(ostream_txn#(64) t);
    bit [63:0] expected;
    received_count++;

    if (expected_data_q.size() == 0) begin
      `uvm_error(get_type_name(), $sformatf("Received extra output: %s (no more expected data)", t.convert2string()))
      fail_count++;
      return;
    end

    expected = expected_data_q.pop_front();

    if (t.data === expected) begin
      pass_count++;
      `uvm_info(get_type_name(), $sformatf("PASS: Output[%0d] = 0x%016x (expected 0x%016x)", received_count-1, t.data, expected), UVM_LOW)
    end else begin
      fail_count++;
      `uvm_error(get_type_name(), $sformatf("FAIL: Output[%0d] = 0x%016x (expected 0x%016x)", received_count-1, t.data, expected))
    end
  endfunction

  // Alias for UVM analysis imp
  typedef ostream_txn#(64) ostream_txn_t;
  typedef uvm_analysis_imp_ostream #(ostream_txn_t, dimc_tile_wrapper_scoreboard) ostream_ap_t;

  // UVM analysis imp port implementation
  function void write(ostream_txn_t t);
    write_ostream(t);
  endfunction

  // Report phase: print summary
  function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    if (fail_count == 0 && received_count == expected_count) begin
      `uvm_info(get_type_name(), $sformatf("SCOREBOARD PASSED: All %0d outputs matched expected values.", pass_count), UVM_NONE)
    end else begin
      `uvm_error(get_type_name(), $sformatf("SCOREBOARD FAILED: %0d/%0d outputs matched, %0d mismatches, %0d expected, %0d received.",
        pass_count, received_count, fail_count, expected_count, received_count))
      if (expected_data_q.size() > 0) begin
        `uvm_error(get_type_name(), $sformatf("Missing %0d expected outputs (not received from DUT)", expected_data_q.size()))
      end
    end
  endfunction

endclass

`endif // DIMC_TILE_WRAPPER_SCOREBOARD_SV