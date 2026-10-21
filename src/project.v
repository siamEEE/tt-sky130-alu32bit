/*
 * 32-bit 8-operation ALU for Tiny Tapeout SKY26d
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_siameee_alu (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,

    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,

    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // ------------------------------------------------------------
    // Tiny Tapeout interface commands
    //
    // uio_in[2:0]
    // 000 = load one byte of operand A
    // 001 = load one byte of operand B
    // 010 = load ALU opcode from ui_in[2:0]
    // 011 = select result byte
    //
    // uio_in[4:3]
    // 00 = bits  7:0
    // 01 = bits 15:8
    // 10 = bits 23:16
    // 11 = bits 31:24
    // ------------------------------------------------------------

    localparam CMD_LOAD_A  = 3'b000;
    localparam CMD_LOAD_B  = 3'b001;
    localparam CMD_LOAD_OP = 3'b010;
    localparam CMD_SET_OUT = 3'b011;

    reg [31:0] operand_a;
    reg [31:0] operand_b;
    reg [2:0]  opcode;
    reg [1:0]  output_sel;

    wire [31:0] alu_result;

    // ------------------------------------------------------------
    // Tiny Tapeout interface registers
    // ------------------------------------------------------------

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            operand_a  <= 32'b0;
            operand_b  <= 32'b0;
            opcode     <= 3'b000;
            output_sel <= 2'b00;
        end
        else begin
            case (uio_in[2:0])

                CMD_LOAD_A: begin
                    case (uio_in[4:3])
                        2'b00: operand_a[7:0]   <= ui_in;
                        2'b01: operand_a[15:8]  <= ui_in;
                        2'b10: operand_a[23:16] <= ui_in;
                        2'b11: operand_a[31:24] <= ui_in;
                    endcase
                end

                CMD_LOAD_B: begin
                    case (uio_in[4:3])
                        2'b00: operand_b[7:0]   <= ui_in;
                        2'b01: operand_b[15:8]  <= ui_in;
                        2'b10: operand_b[23:16] <= ui_in;
                        2'b11: operand_b[31:24] <= ui_in;
                    endcase
                end

                CMD_LOAD_OP: begin
                    opcode <= ui_in[2:0];
                end

                CMD_SET_OUT: begin
                    output_sel <= uio_in[4:3];
                end

                default: begin
                    // Reserved commands: hold current state
                end
            endcase
        end
    end

    // ------------------------------------------------------------
    // 32-bit combinational ALU
    // ------------------------------------------------------------

    alu_core u_alu (
        .a      (operand_a),
        .b      (operand_b),
        .opcode (opcode),
        .result (alu_result)
    );

    // ------------------------------------------------------------
    // Select one of the four result bytes for the 8-bit TT output
    // ------------------------------------------------------------

    reg [7:0] selected_result_byte;

    always @(*) begin
        case (output_sel)
            2'b00: selected_result_byte = alu_result[7:0];
            2'b01: selected_result_byte = alu_result[15:8];
            2'b10: selected_result_byte = alu_result[23:16];
            2'b11: selected_result_byte = alu_result[31:24];
            default: selected_result_byte = 8'b0;
        endcase
    end

    assign uo_out = selected_result_byte;

    // Bidirectional pins are used only as control inputs.
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // ena is intentionally unused.
    // uio_in[7:5] are reserved.
    wire _unused = &{ena, uio_in[7:5], 1'b0};

endmodule

`default_nettype wire