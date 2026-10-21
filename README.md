# 32-bit 8-Operation ALU for Tiny Tapeout SKY26d
 
[![gds](https://github.com/siamEEE/tt-sky130-alu32bit/actions/workflows/gds.yaml/badge.svg)](https://github.com/siamEEE/tt-sky130-alu32bit/actions/workflows/gds.yaml)
[![docs](https://github.com/siamEEE/tt-sky130-alu32bit/actions/workflows/docs.yaml/badge.svg)](https://github.com/siamEEE/tt-sky130-alu32bit/actions/workflows/docs.yaml)
[![test](https://github.com/siamEEE/tt-sky130-alu32bit/actions/workflows/test.yaml/badge.svg)](https://github.com/siamEEE/tt-sky130-alu32bit/actions/workflows/test.yaml)
 
A 32-bit arithmetic and logic unit written in Verilog for Tiny Tapeout SKY26d on the SkyWater SKY130 process. The project uses a byte-oriented external interface to transfer 32-bit operands through Tiny Tapeout's 8-bit dedicated input and output buses.
 
## Design summary
 
| Item | Value |
|---|---|
| Internal datapath | 32 bit |
| ALU opcode | 3 bit |
| Operations | ADD, SUB, INC, DEC, AND, OR, XOR, NOT |
| External data width | 8 bit |
| Target tile | 1x1 |
| Configured clock target | 50 MHz (20 ns period) |
| HDL | Verilog |
| Technology | SkyWater SKY130A |
| Physical-design flow | Tiny Tapeout / LibreLane / OpenROAD |
 
## Architecture
 
The design is intentionally divided into two RTL modules.
 
- `src/alu_core.v` describes only the combinational 32-bit ALU.
- `src/project.v` implements the Tiny Tapeout top-level interface and contains the operand registers, opcode register, output-byte selector, and byte multiplexer.
 
This separation keeps the arithmetic datapath independent of the external bus protocol.
 
## ALU operations
 
| Opcode | Operation | Definition |
|---|---|---|
| `000` | ADD | `A + B` |
| `001` | SUB | `A - B` |
| `010` | INC | `A + 1` |
| `011` | DEC | `A - 1` |
| `100` | AND | `A & B` |
| `101` | OR | `A \| B` |
| `110` | XOR | `A ^ B` |
| `111` | NOT | `~A` |
 
## Tiny Tapeout interface
 
`ui_in[7:0]` carries the input data byte. `uio_in[2:0]` selects the wrapper command, `uio_in[4:3]` selects the byte position, and `uo_out[7:0]` carries the selected byte of the 32-bit result. The bidirectional pins are used only as control inputs.
 
| Command | Meaning |
|---|---|
| `000` | Load one byte of operand A |
| `001` | Load one byte of operand B |
| `010` | Load ALU opcode |
| `011` | Select result byte |
| `100`-`111` | Reserved |
 
A 32-bit operand is loaded as four addressed bytes. For example, `0x12345678` is written as byte 0 = `0x78`, byte 1 = `0x56`, byte 2 = `0x34`, and byte 3 = `0x12`.
 
## Example
 
For
 
```text
A      = 0x12345678
B      = 0x01020304
opcode = 000   (ADD)
```
 
the ALU result is
 
```text
0x1336597C
```
 
The result is read from `uo_out[7:0]` one byte at a time: `0x7C`, `0x59`, `0x36`, and `0x13` for byte selections 0 through 3.
 
## Verification
 
The repository includes a Cocotb testbench driven by Icarus Verilog. Directed tests cover zero, all-ones values, arithmetic wraparound, alternating bit patterns, and representative 32-bit operands. Deterministic randomized tests exercise all eight opcodes.
 
The Tiny Tapeout SKY26d workflow subsequently performs physical implementation, the official precheck, and gate-level simulation using the generated netlist. The workflow badges at the top of this page show the current repository status.
 
## Project structure
 
```text
src/
  alu_core.v       32-bit combinational ALU
  project.v        Tiny Tapeout wrapper
  config.json      physical-design configuration
 
test/
  tb.v             simulation harness
  test.py          Cocotb verification
  Makefile         simulation build rules
 
docs/
  info.md          Tiny Tapeout datasheet text
 
info.yaml          project metadata and pinout
```
 
## Scope
 
This tapeout version is intentionally small and auditable. It does not include UART logic, processor instruction decoding, status flags, clock gating, operand isolation, multiplication, division, or a hand-structured adder. The goal is a clear 32-bit ALU that can be verified from RTL through physical implementation and later exercised on fabricated silicon.
 
## Tiny Tapeout documentation
 
The shuttle datasheet text is maintained in [`docs/info.md`](docs/info.md).
 
## License
 
Apache-2.0
