interface dimc_tile_wrapper_if(input logic clk, input logic resetn);

  // Control signals for DUT operation
  logic        start;
  logic        stop;
  logic        config_mode;
  logic [3:0]  operation_mode;
  logic        clear_status;

  // Status/flag signals from DUT
  logic        busy;
  logic        error;
  logic        done;

  // Interface signals for coordination with environments
  // Feature Buffer Environment
  logic [63:0] m_feature_data;
  logic        m_feature_valid;
  logic        m_feature_ready;

  // PSIN Environment
  logic [31:0] m_psin_data;
  logic        m_psin_valid;
  logic        m_psin_ready;

  // Kernel Memory Environment
  logic [63:0] m_kernel_data;
  logic [8:0]  m_kernel_addr;
  logic        m_kernel_we;

  // Addin Environment
  logic [63:0] m_addin_data;
  logic [3:0]  m_addin_addr;
  logic        m_addin_we;

  // Computation Environment
  logic [31:0] m_computation_data;
  logic [4:0]  m_computation_addr;
  logic        m_computation_we;

  // Output Buffer Environment
  logic [63:0] m_output_data;
  logic        m_output_valid;
  logic        m_output_ready;

  // Clocking block for synchronous access
  clocking cb @(posedge clk);
    // Control signals
    output start, stop, config_mode, operation_mode, clear_status;
    // Status signals
    input busy, error, done;
    // Interface signals
    inout m_feature_data, m_feature_valid, m_feature_ready;
    inout m_psin_data, m_psin_valid, m_psin_ready;
    inout m_kernel_data, m_kernel_addr, m_kernel_we;
    inout m_addin_data, m_addin_addr, m_addin_we;
    inout m_computation_data, m_computation_addr, m_computation_we;
    inout m_output_data, m_output_valid, m_output_ready;
  endclocking

  initial begin
    start = 1'b0;
    stop = 1'b0;
    config_mode = 1'b0;
    operation_mode = 4'b0000;
    clear_status = 1'b0;
    m_feature_valid = 1'b0;
    m_psin_valid = 1'b0;
    m_kernel_we = 1'b0;
    m_addin_we = 1'b0;
    m_computation_we = 1'b0;
    m_output_valid = 1'b0;
  end

endinterface