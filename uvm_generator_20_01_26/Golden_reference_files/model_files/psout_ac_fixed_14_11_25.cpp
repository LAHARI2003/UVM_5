// psout_ac_fixed.cpp

// C++ port of psout_patched.c using Algorithmic C fixed-point (ac_fixed).

// Keeps the same I/O and mode behavior; math is done in ac_fixed with saturation.

// Adds PS_FIRST/PS_MODE/PS_LAST controls and SOUT generation.



#include <cstdio>

#include <cstdlib>

#include <cstdint>

#include <cstring>

#include <cinttypes>

#include <string>

#include <stdexcept>

#include <sys/types.h>

#include <sys/stat.h>

#include "ac_fixed.h"   // <-- ensure your include path points to this



// ---- Constants ----------------------------------------------------------------

#define MAX_KERNELS     32

#define MAX_VECTOR_BITS 1024

#define MAX_ELEMS       1024



static int g_acc[MAX_KERNELS];

// ---- Helpers ------------------------------------------------------------------

static void strip_eol(char *s) {

if (!s) return;

s[strcspn(s, "\r\n")] = '\0';

}

static bool is_space(char c) {

return c == ' ' || c == '\t' || c == '\r' || c == '\n';

}

static bool line_has_non_ws(const char *s) {

if (!s) return false;

for (const char *p = s; *p; ++p) if (!is_space(*p)) return true;

return false;

}

static int hex_val(char c) {

if (c >= '0' && c <= '9') return c - '0';

if (c >= 'A' && c <= 'F') return c - 'A' + 10;

if (c >= 'a' && c <= 'f') return c - 'a' + 10;

return -1;

}

static int sanitize_hex_line(const char *in, char *out, size_t out_cap) {

if (!in || !out || out_cap == 0) return -1;

char tmp[2048];

size_t k = 0;

for (const char *p = in; *p; ++p) {

if (*p == '\r' || *p == '\n') break;

if (*p == ' ' || *p == '\t') continue;

if (k + 1 >= sizeof(tmp)) return -1;

tmp[k++] = *p;

}

tmp[k] = '\0';

size_t start = (k >= 2 && tmp[0] == '0' && (tmp[1] == 'x' || tmp[1] == 'X')) ? 2 : 0;

size_t out_len = 0;

for (size_t i = start; i < k; ++i) {

int hv = hex_val(tmp[i]);

if (hv < 0) return -1;

if (out_len + 1 >= out_cap) return -1;

out[out_len++] = tmp[i];

}

if (out_len == 0) return -1;

out[out_len] = '\0';

return (int)out_len;

}

static void hex_to_bits(const char *hex_str_sanitized, int *bits, int bit_len) {

int idx = 0;

for (int i = 0; hex_str_sanitized[i] != '\0' && idx < bit_len; ++i) {

int val = hex_val(hex_str_sanitized[i]);

if (val < 0) { std::fprintf(stderr, "Invalid hex char '%c'\n", hex_str_sanitized[i]); std::exit(EXIT_FAILURE); }

for (int j = 3; j >= 0; --j) bits[idx++] = (val >> j) & 1;

}

if (idx != bit_len) {

std::fprintf(stderr, "Internal error: produced %d bits, expected %d\n", idx, bit_len);

std::exit(EXIT_FAILURE);

}

}

static int bits_to_signed_int(const int *bits, int bit_width) {

int val = 0;

for (int i = 0; i < bit_width; ++i) val = (val << 1) | (bits[i] & 1);

int sign_bit = 1 << (bit_width - 1);

if (val & sign_bit) val -= (1 << bit_width);

return val;

}

static int bits_to_unsigned_int(const int *bits, int bit_width) {

int val = 0;

for (int i = 0; i < bit_width; ++i) val = (val << 1) | (bits[i] & 1);

return val;

}



// Vector loading

static void load_vectors_hex(const char *filename, int expected_lines, int vector_length_bits,

int vectors[][MAX_VECTOR_BITS]) {

FILE *file = std::fopen(filename, "r");

if (!file) { std::perror("Error opening kernel file"); std::exit(EXIT_FAILURE); }

char line[4096];

int lines_read = 0;

while (lines_read < expected_lines) {

if (!std::fgets(line, sizeof(line), file)) {

std::fprintf(stderr, "Expected %d non-empty lines in %s, got fewer.\n", expected_lines, filename);

std::exit(EXIT_FAILURE);

}

strip_eol(line);

if (!line_has_non_ws(line)) continue;

char hex_clean[2048];

int hex_len = sanitize_hex_line(line, hex_clean, sizeof(hex_clean));

if (hex_len < 0) {

std::fprintf(stderr, "%s: invalid hex content on line %d\n", filename, lines_read + 1);

std::exit(EXIT_FAILURE);

}

if (hex_len * 4 != vector_length_bits) {

std::fprintf(stderr, "%s: line %d: expected %d bits (%d hex), got %d bits (%d hex)\n",

filename, lines_read + 1, vector_length_bits, vector_length_bits / 4, hex_len * 4, hex_len);

std::exit(EXIT_FAILURE);

}

hex_to_bits(hex_clean, vectors[lines_read], vector_length_bits);

++lines_read;

}

while (std::fgets(line, sizeof(line), file)) {

if (line_has_non_ws(line)) {

std::fprintf(stderr, "%s: extra data after expected %d lines\n", filename, expected_lines);

std::fclose(file);

std::exit(EXIT_FAILURE);

}

}

std::fclose(file);

}

static void load_single_vector_hex(const char *filename, int vector_length_bits, int *bits) {

FILE *file = std::fopen(filename, "r");

if (!file) { std::perror("Error opening feature file"); std::exit(EXIT_FAILURE); }

char line[4096];

while (1) {

if (!std::fgets(line, sizeof(line), file)) {

std::fprintf(stderr, "%s: expected 1 non-empty line, got 0\n", filename);

std::exit(EXIT_FAILURE);

}

strip_eol(line);

if (line_has_non_ws(line)) break;

}

char hex_clean[2048];

int hex_len = sanitize_hex_line(line, hex_clean, sizeof(hex_clean));

if (hex_len < 0) { std::fprintf(stderr, "%s: invalid hex content\n", filename); std::exit(EXIT_FAILURE); }

if (hex_len * 4 != vector_length_bits) {

std::fprintf(stderr, "%s: expected %d bits (%d hex), got %d bits (%d hex)\n",

filename, vector_length_bits, vector_length_bits / 4, hex_len * 4, hex_len);

std::exit(EXIT_FAILURE);

}

hex_to_bits(hex_clean, bits, vector_length_bits);

while (std::fgets(line, sizeof(line), file)) {

if (line_has_non_ws(line)) {

std::fprintf(stderr, "%s: extra data after first vector line\n", filename);

std::fclose(file);

std::exit(EXIT_FAILURE);

}

}

std::fclose(file);

}

static int32_t parse_hex32_to_int(const char *hex_clean, bool enforce8) {

size_t n = std::strlen(hex_clean);

if (n == 0 || n > 8) {

std::fprintf(stderr, "Invalid 32-bit hex length (%zu). Expected %s8 hex digits.\n", n, enforce8 ? "exactly " : "1..");

std::exit(EXIT_FAILURE);

}

if (enforce8 && n != 8) {

std::fprintf(stderr, "Expected exactly 8 hex digits, got %zu.\n", n);

std::exit(EXIT_FAILURE);

}

unsigned long long val = 0;

for (size_t i = 0; i < n; ++i) {

int hv = hex_val(hex_clean[i]);

if (hv < 0) { std::fprintf(stderr, "Invalid hex char '%c' in 32-bit value\n", hex_clean[i]); std::exit(EXIT_FAILURE); }

val = (val << 4) | (unsigned)hv;

}

val &= 0xFFFFFFFFULL;

if (val & 0x80000000ULL) return (int32_t)(val - 0x100000000ULL);

else return (int32_t)val;

}

static void load_int_vector_hex32(const char *filename, int expected_length, int *vec, bool enforce8) {

FILE *file = std::fopen(filename, "r");

if (!file) { std::perror("Error opening int vector (hex32) file"); std::exit(EXIT_FAILURE); }

char line[1024];

int count = 0;

while (count < expected_length) {

if (!std::fgets(line, sizeof(line), file)) {

std::fprintf(stderr, "Expected %d non-empty hex lines in %s, got fewer.\n", expected_length, filename);

std::exit(EXIT_FAILURE);

}

strip_eol(line);

if (!line_has_non_ws(line)) continue;

char hex_clean[64];

int hex_len = sanitize_hex_line(line, hex_clean, sizeof(hex_clean));

if (hex_len < 0) { std::fprintf(stderr, "%s: line %d: invalid hex32 content\n", filename, count + 1); std::exit(EXIT_FAILURE); }

int32_t v = parse_hex32_to_int(hex_clean, enforce8);

vec[count++] = (int)v;

}

while (std::fgets(line, sizeof(line), file)) {

if (line_has_non_ws(line)) {

std::fprintf(stderr, "%s: extra data after expected %d lines\n", filename, expected_length);

std::fclose(file); std::exit(EXIT_FAILURE);

}

}

std::fclose(file);

}



static void ensure_dir_exists(const char *dirname) {

struct stat st;

if (stat(dirname, &st) == 0 && S_ISDIR(st.st_mode)) return;

if (mkdir(dirname, 0755) != 0) {

std::perror("mkdir hex_outputs");

std::exit(EXIT_FAILURE);

}

}

static std::string path_strip_ext(const char *path) {

std::string s(path);

size_t slash = s.find_last_of('/');

size_t dot = s.find_last_of('.');

if (dot != std::string::npos && (slash == std::string::npos || dot > slash)) {

return s.substr(0, dot);

}

return s;

}

static std::string path_basename_no_dir(const char *path) {

const char *p = std::strrchr(path, '/');

return p ? std::string(p + 1) : std::string(path);

}

static void write_hex32_list(const char *filename, const int *vec) {

FILE *f = std::fopen(filename, "w");

if (!f) { std::perror("Error writing hex32 file"); std::exit(EXIT_FAILURE); }

for (int i = 0; i < MAX_KERNELS; ++i) {

uint32_t u = (uint32_t)((int32_t)vec[i]); // normalize to 32-bit two’s complement

std::fprintf(f, "%08x\n", u);

}

std::fclose(f);

}

static void write_hex8_list(const char *filename, const int *vec) {

FILE *f = std::fopen(filename, "w");

if (!f) { std::perror("Error writing hex8 file"); std::exit(EXIT_FAILURE); }

for (int i = 0; i < MAX_KERNELS; ++i) {

int v = vec[i];

if (v < 0) v = 0;          // safety clamp; SOUT mapping already non-negative

if (v > 255) v = 255;      // safety

uint8_t u8 = (uint8_t)v;   // 8-bit

std::fprintf(f, "%02x\n", (unsigned)u8);

}

std::fclose(f);

}

static void write_binary8_list(const char *filename, const int *vec) {
FILE *f = std::fopen(filename, "w");
if (!f) { std::perror("Error writing binary file"); std::exit(EXIT_FAILURE); }
for (int i = 0; i < MAX_KERNELS; ++i) {
int v = vec[i];
if (v < 0) v = 0;          // safety clamp
if (v > 255) v = 255;      // safety
uint8_t u8 = (uint8_t)v;   // 8-bit
// Write as 8-bit binary string
for (int bit = 7; bit >= 0; --bit) {
std::fprintf(f, "%d", (u8 >> bit) & 1);
}
std::fprintf(f, "\n");
}
std::fclose(f);
}



static void write_sout_modified(const char *filename, const int *sout, const char *mode) {
FILE *f = std::fopen(filename, "w");
if (!f) { std::perror("Error writing sout_modified file"); std::exit(EXIT_FAILURE); }

std::string full_bits;  // Accumulate all bits

if (std::strcmp(mode, "00") == 0) {
// Mode 00: 1 bit per kernel -> 32 bits total, single line
for (int i = 0; i < MAX_KERNELS; ++i) {
int v = sout[i];
if (v < 0) v = 0;
if (v > 255) v = 255;
uint8_t u8 = (uint8_t)v;
// Take last 1 bit
full_bits += (u8 & 1) ? '1' : '0';
}
if (full_bits.length() < 64) {
        full_bits = std::string(64 - full_bits.length(), '0') + full_bits;
    }

std::fprintf(f, "%s\n", full_bits.c_str());

} else if (std::strcmp(mode, "01") == 0) {
// Mode 01: 2 bits per kernel -> 64 bits total, single line
for (int i = 0; i < MAX_KERNELS; ++i) {
int v = sout[i];
if (v < 0) v = 0;
if (v > 255) v = 255;
uint8_t u8 = (uint8_t)v;
// Take last 2 bits
for (int bit = 1; bit >= 0; --bit) {
full_bits += ((u8 >> bit) & 1) ? '1' : '0';
}
}
std::fprintf(f, "%s\n", full_bits.c_str());

} else if (std::strcmp(mode, "10") == 0) {
// Mode 10: 4 bits per kernel -> 128 bits total, break into 2 lines of 64 bits
for (int i = 0; i < MAX_KERNELS; ++i) {
int v = sout[i];
if (v < 0) v = 0;
if (v > 255) v = 255;
uint8_t u8 = (uint8_t)v;
// Take last 4 bits
for (int bit = 3; bit >= 0; --bit) {
full_bits += ((u8 >> bit) & 1) ? '1' : '0';
}
}
// Write in chunks of 64 bits
for (size_t i = 0; i < full_bits.length(); i += 64) {
std::string chunk = full_bits.substr(i, 64);
std::fprintf(f, "%s\n", chunk.c_str());
}

} else if (std::strcmp(mode, "11") == 0) {
// Mode 11: 8 bits per kernel -> 256 bits total, break into 4 lines of 64 bits
for (int i = 0; i < MAX_KERNELS; ++i) {
int v = sout[i];
if (v < 0) v = 0;
if (v > 255) v = 255;
uint8_t u8 = (uint8_t)v;
// Take all 8 bits
for (int bit = 7; bit >= 0; --bit) {
full_bits += ((u8 >> bit) & 1) ? '1' : '0';
}
}
// Write in chunks of 64 bits
for (size_t i = 0; i < full_bits.length(); i += 64) {
std::string chunk = full_bits.substr(i, 64);
std::fprintf(f, "%s\n", chunk.c_str());
}

} else {
std::fprintf(stderr, "Invalid mode for sout_modified output.\n");
std::fclose(f);
std::exit(EXIT_FAILURE);
}

std::fclose(f);
}





// ---- Fixed-point extraction & compute ----------------------------------------

template<int W, bool SIGNED>

static inline void extract_elements_fx(const int *bits, int elem_count, ac_fixed<W, W, SIGNED> *out) {

for (int i = 0; i < elem_count; ++i) {

const int *elem_bits = &bits[i * W];

int v = SIGNED ? bits_to_signed_int(elem_bits, W) : bits_to_unsigned_int(elem_bits, W);

out[i] = v; // integer -> ac_fixed<W,W,SIGNED>

}

}



template<int W, bool SK, bool SF>

static void compute_psout_mode(const int kernels[][MAX_VECTOR_BITS],

const int *feature,

const int *psin,

const int *addin,

bool ps_first, bool ps_mode, bool ps_last,

int *psout) {

static_assert(W == 1 || W == 2 || W == 4 || W == 8, "W must be 1,2,4,8");

constexpr int E = 1024 / W; // elements per vector



using k_t      = ac_fixed<W,  W,  SK>;

using f_t      = ac_fixed<W,  W,  SF>;

using acc_wide = ac_fixed<24, 24, true,AC_TRN,AC_SAT>;

using sum_wide = ac_fixed<40, 40, true>;

using out32_t  = ac_fixed<32, 32, true, AC_TRN, AC_SAT>; // INT32 clamp



// Decompose bit-vectors into element arrays

k_t k_elems[MAX_KERNELS][E];

f_t f_elems[E];



for (int i = 0; i < MAX_KERNELS; ++i) {

extract_elements_fx<W, SK>(kernels[i], E, k_elems[i]);

}

extract_elements_fx<W, SF>(feature, E, f_elems);



for (int i = 0; i < MAX_KERNELS; ++i) {

acc_wide acc = 0;

for (int j = 0; j < E; ++j) {

if (W == 1) {

if ( (acc_wide(k_elems[i][j]) == 0 && acc_wide(f_elems[j]) == 1) || (acc_wide(k_elems[i][j]) == 1 && acc_wide(f_elems[j]) == 0) ) {

acc += -1;

} else if ( (acc_wide(k_elems[i][j]) == 0 && acc_wide(f_elems[j]) == 0) || (acc_wide(k_elems[i][j]) == 1 && acc_wide(f_elems[j]) == 1) ){

 acc += 1;

//acc += acc_wide(k_elems[i][j]) * acc_wide(f_elems[j]);

}

} else {

acc += acc_wide(k_elems[i][j]) * acc_wide(f_elems[j]);

}

}



g_acc[i]= acc.to_int();



// Choose what to add based on PS flags

sum_wide s = sum_wide(acc);

if (ps_mode || ps_last) s += sum_wide(psin[i]);

if (ps_last)            s += sum_wide(addin[i]);



out32_t o32 = s;   // saturates to INT32 range

psout[i] = o32.to_int();

}

}



static void compute_psout_ac(const int kernels[][MAX_VECTOR_BITS], const int *feature,

const int *psin, const int *addin,

const char *mode, const char *sign_8b,

bool ps_first, bool ps_mode, bool ps_last,

int *psout) {

if (std::strcmp(mode, "00") == 0) {

compute_psout_mode<1, false, false>(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

} else if (std::strcmp(mode, "01") == 0) {

compute_psout_mode<2, true,  true >(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

} else if (std::strcmp(mode, "10") == 0) {

compute_psout_mode<4, true,  true >(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

} else if (std::strcmp(mode, "11") == 0) {

if (!sign_8b || std::strlen(sign_8b) != 2 ||

(sign_8b[0] != '0' && sign_8b[0] != '1') ||

(sign_8b[1] != '0' && sign_8b[1] != '1')) {

std::fprintf(stderr, "sign_8b must be two chars '0' or '1', e.g.\n");

std::exit(EXIT_FAILURE);

}

//const bool SK = (sign_8b[1] == '1');

//const bool SF = (sign_8b[0] == '1');



const bool SK = (sign_8b[0] == '1');

const bool SF = (sign_8b[1] == '1');

if      ( SK &&  SF) compute_psout_mode<8, true , true >(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

else if ( SK && !SF) compute_psout_mode<8, true , false>(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

else if (!SK &&  SF) compute_psout_mode<8, false, true >(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

else                 compute_psout_mode<8, false, false>(kernels, feature, psin, addin, ps_first, ps_mode, ps_last, psout);

} else {

std::fprintf(stderr, "Invalid mode. Expected one of: 00, 01, 10, 11.\n");

std::exit(EXIT_FAILURE);

}

}



// ---- SOUT mapping -------------------------------------------------------------



static void compute_sout(const char *mode, const int *psout, int *sout) {

if (std::strcmp(mode, "00") == 0) {

// 1-bit: psout >= 1 -> 1, else 0

for (int i = 0; i < MAX_KERNELS; ++i) sout[i] = (psout[i] >= 1) ? 1 : 0;

} else if (std::strcmp(mode, "01") == 0) {

// 2-bit: psout > 1 -> 1, else 0  (per spec provided)

for (int i = 0; i < MAX_KERNELS; ++i){

    if      (psout[i] < 0) sout[i] = 0;

    else if (psout[i] > 1) sout[i] = 1;

    else  sout[i] = psout[i];  // 0 or 1



}

} else if (std::strcmp(mode, "10") == 0) {

// 4-bit (signed-style clamp): 0..7

for (int i = 0; i < MAX_KERNELS; ++i) {

if      (psout[i] >= 7) sout[i] = 7;

else if (psout[i] <= 0) sout[i] = 0;

else                    sout[i] = psout[i]; // 1..6

}

} else if (std::strcmp(mode, "11") == 0) {

// 8-bit (signed-style clamp): 0..127

for (int i = 0; i < MAX_KERNELS; ++i) {

if      (psout[i] >= 127) sout[i] = 127;

else if (psout[i] <= 0)   sout[i] = 0;

else                      sout[i] = psout[i]; // 1..126

}

} else {

std::fprintf(stderr, "Invalid mode for SOUT mapping.\n");

std::exit(EXIT_FAILURE);

}

}



// ---- I/O ----------------------------------------------------------------------

static void write_output(const char *filename, const int *vec) {

FILE *file = std::fopen(filename, "w");

if (!file) { std::perror("Error writing output file"); std::exit(EXIT_FAILURE); }

for (int i = 0; i < MAX_KERNELS; ++i) std::fprintf(file, "%d\n", vec[i]);

std::fclose(file);

}



static int parse_0_or_1(const char *s, const char *name) {

if (!s || (s[0] != '0' && s[0] != '1') || s[1] != '\0') {

std::fprintf(stderr, "%s must be '0' or '1'\n", name);

std::exit(EXIT_FAILURE);

}

return (s[0] == '1') ? 1 : 0;

}



int main(int argc, char *argv[]) {

// argv:

// 1 kernel_file

// 2 feature_file

// 3 psin_hex32_file

// 4 addin_hex32_file

// 5 output_file

// 6 mode

// 7 sign_8b

// 8 PS_FIRST

// 9 PS_MODE

// 10 PS_LAST

if (argc != 11) {

std::fprintf(stderr, "Usage: %s kernel_file feature_file psin_hex32_file addin_hex32_file output_file mode sign_8b PS_FIRST PS_MODE PS_LAST\n", argv[0]);

return EXIT_FAILURE;

}

const char *kernel_file = argv[1];

const char *feature_file= argv[2];

const char *psin_file   = argv[3];

const char *addin_file  = argv[4];

const char *output_file = argv[5];

const char *mode        = argv[6];

const char *sign_8b     = argv[7];



const int PS_FIRST = parse_0_or_1(argv[8],  "PS_FIRST");

const int PS_MODE  = parse_0_or_1(argv[9],  "PS_MODE");

const int PS_LAST  = parse_0_or_1(argv[10], "PS_LAST");



if ((PS_FIRST + PS_MODE + PS_LAST) != 1) {

std::fprintf(stderr, "Exactly one of PS_FIRST, PS_MODE, PS_LAST must be 1.\n");

return EXIT_FAILURE;

}



int kernels[MAX_KERNELS][MAX_VECTOR_BITS];

int feature[MAX_VECTOR_BITS];

int psin[MAX_KERNELS];

int addin[MAX_KERNELS];

int psout[MAX_KERNELS];

int sout[MAX_KERNELS];



load_vectors_hex(kernel_file, MAX_KERNELS, MAX_VECTOR_BITS, kernels);    // 32 lines × 1024 bits

load_single_vector_hex(feature_file, MAX_VECTOR_BITS, feature);          // 1 line × 1024 bits

load_int_vector_hex32(psin_file,  MAX_KERNELS, psin,  true);             // 32 lines × 8 hex chars

load_int_vector_hex32(addin_file, MAX_KERNELS, addin, true);             // 32 lines × 8 hex chars



// Fixed-point compute with PS flags

compute_psout_ac(kernels, feature, psin, addin, mode, sign_8b,

PS_FIRST != 0, PS_MODE != 0, PS_LAST != 0,

psout);



// Create SOUT from PSOUT

compute_sout(mode, psout, sout);



// Build base path without extension to avoid double dots

std::string base_no_ext = path_strip_ext(output_file);



// Text outputs

if (PS_LAST) {

// In SOUT mode, write both PSOUT and SOUT to separate files next to output_file

std::string psout_txt = base_no_ext + "_psout.txt";

std::string sout_txt  = base_no_ext + "_sout.txt";

write_output(psout_txt.c_str(), psout);

write_output(sout_txt.c_str(),  sout);

std::printf("PSOUT written to %s\n", psout_txt.c_str());

std::printf("SOUT  written to %s\n", sout_txt.c_str());

std::string sout_hex  = base_no_ext + "_sout_hex.txt";
write_hex8_list (sout_hex.c_str(),  sout);  // 8-bit hex (2 chars)
std::printf("SOUT  hex written to %s\n",  sout_hex.c_str());

std::string sout_binary = base_no_ext + "_sout_binary.txt";
write_binary8_list(sout_binary.c_str(), sout);  // 8-bit binary strings
std::printf("SOUT  binary written to %s\n", sout_binary.c_str());

std::string sout_modified = base_no_ext + "_sout_modified.txt";
write_sout_modified(sout_modified.c_str(), sout, mode);
std::printf("SOUT  modified written to %s\n", sout_modified.c_str());


} else {

// Non-SOUT mode: keep original behavior

write_output(output_file, psout);

std::printf("PSOUT written to %s\n", output_file);

}



write_output("accu.txt", g_acc);

std::printf("ACCU  written to %s\n", "accu.txt");



std::string accu_hex = base_no_ext + "_accu_hex.txt";

write_hex32_list(accu_hex.c_str(), g_acc);

std::printf("ACCU  hex written to %s\n", accu_hex.c_str());



// Hex outputs in the same directory as output_file, with underscores (no extra dots)

std::string psout_hex = base_no_ext + "_psout_hex.txt";


write_hex32_list(psout_hex.c_str(), psout); // 32-bit hex (8 chars)



std::printf("PSOUT hex written to %s\n", psout_hex.c_str());






return EXIT_SUCCESS;

}