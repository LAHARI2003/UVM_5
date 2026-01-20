// This istream_directed_write_sequence generated istream_seq_item 16 times
// and pass it to the istream_sequencer 
// This reads the input frame from the file istream_data_unique_64x16.txt and
// saves it into the istream_data_ip of two dimensional array of 16 rows and 64
// columns
// This stores istream_data_ip row gets driven to req.istream_data field
class istream_directed_write_sequence #(int DATA_WIDTH = 32) extends uvm_sequence #(istream_seq_item);

  `uvm_object_utils(istream_directed_write_sequence#(DATA_WIDTH))
  //`uvm_param_utils(feature_directed_write_sequence#(DATA_WIDTH))

  function new(string name = "istream_directed_write_sequence");
    super.new(name);
  endfunction

  //logic [63:0] feat_data_ip [0:15];
  logic [DATA_WIDTH-1:0] istream_data_ip [];
  int i;
  int size;

  string file_path;

  istream_seq_item#(DATA_WIDTH) req;

  task body();
   begin
   // file_path = "./input_data/feature_data_unique_64x16.txt";
   // $readmemh("./input_data/feature_data_unique_64x16.txt", feat_data_ip) ;
    
    istream_data_ip = new[size];

    $readmemh(file_path, istream_data_ip) ;
    
    for(i = 0; i<size; i++)
      begin : istream_wr

        req = istream_seq_item#(DATA_WIDTH)::type_id::create("req");
        //assert(req.randomize());
        
       
        req.istream_valid = 1'b1;
        req.istream_data  = istream_data_ip[i];
        
        //req.print();

       // `uvm_do_with(req,{req.feat_valid==1'b1;req.feat_data  == feat_data_ip[i];});
        start_item(req);

        finish_item(req);
    
     end : istream_wr

 // Disabling feature buffer
        req.istream_valid = 1'b0;
        req.istream_data  = 64'h0;

        //`uvm_do_with(req,{req.feat_valid==1'b0;req.feat_data  == 64'h0;});

       //`uvm_do(req);
        start_item(req);
        finish_item(req);

    end
  endtask

endclass
