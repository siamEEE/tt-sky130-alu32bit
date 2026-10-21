import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge


CMD_LOAD_A  = 0b000
CMD_LOAD_B  = 0b001
CMD_LOAD_OP = 0b010
CMD_SET_OUT = 0b011

MASK32 = 0xFFFFFFFF


def reference_alu(a, b, opcode):
    if opcode == 0b000:
        return (a + b) & MASK32

    if opcode == 0b001:
        return (a - b) & MASK32

    if opcode == 0b010:
        return (a + 1) & MASK32

    if opcode == 0b011:
        return (a - 1) & MASK32

    if opcode == 0b100:
        return a & b

    if opcode == 0b101:
        return a | b

    if opcode == 0b110:
        return a ^ b

    if opcode == 0b111:
        return (~a) & MASK32

    return 0


async def issue_command(dut, command, data=0, byte_index=0):
    """
    Apply one Tiny Tapeout wrapper command.

    uio_in[2:0] = command
    uio_in[4:3] = byte index
    ui_in[7:0]  = data
    """

    dut.ui_in.value = data & 0xFF

    dut.uio_in.value = (
        (command & 0x7)
        | ((byte_index & 0x3) << 3)
    )

    await RisingEdge(dut.clk)


async def load_operand(dut, command, value):
    for byte_index in range(4):

        byte_value = (
            value >> (8 * byte_index)
        ) & 0xFF

        await issue_command(
            dut,
            command,
            data=byte_value,
            byte_index=byte_index
        )


async def load_opcode(dut, opcode):
    await issue_command(
        dut,
        CMD_LOAD_OP,
        data=opcode & 0x7
    )


async def read_result(dut):
    result = 0

    for byte_index in range(4):

        await issue_command(
            dut,
            CMD_SET_OUT,
            byte_index=byte_index
        )

        # Important:
        # wait until the opposite clock edge before reading.
        # This gives the gate-level netlist enough time to propagate.
        await FallingEdge(dut.clk)

        result_byte = int(dut.uo_out.value)

        result |= result_byte << (8 * byte_index)

    return result & MASK32


async def run_alu_case(dut, a, b, opcode):

    await load_operand(
        dut,
        CMD_LOAD_A,
        a
    )

    await load_operand(
        dut,
        CMD_LOAD_B,
        b
    )

    await load_opcode(
        dut,
        opcode
    )

    actual = await read_result(dut)

    expected = reference_alu(
        a,
        b,
        opcode
    )

    assert actual == expected, (
        f"FAIL: "
        f"opcode={opcode:03b}, "
        f"A=0x{a:08X}, "
        f"B=0x{b:08X}, "
        f"expected=0x{expected:08X}, "
        f"actual=0x{actual:08X}"
    )


@cocotb.test()
async def test_alu(dut):

    # 50 MHz clock -> 20 ns period
    clock = Clock(
        dut.clk,
        20,
        unit="ns"
    )

    cocotb.start_soon(
        clock.start()
    )

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    dut.rst_n.value = 0

    await ClockCycles(
        dut.clk,
        4
    )

    dut.rst_n.value = 1

    await ClockCycles(
        dut.clk,
        2
    )

    # ---------------------------------------------------------
    # Directed corner cases
    # ---------------------------------------------------------

    directed_inputs = [
        (0x00000000, 0x00000000),
        (0x00000001, 0x00000001),
        (0xFFFFFFFF, 0x00000001),
        (0x00000000, 0x00000001),
        (0x7FFFFFFF, 0x00000001),
        (0x80000000, 0xFFFFFFFF),
        (0x12345678, 0x01020304),
        (0xAAAAAAAA, 0x55555555),
        (0xFFFFFFFF, 0xFFFFFFFF),
    ]

    # Test all 8 operations
    for opcode in range(8):

        for a, b in directed_inputs:

            await run_alu_case(
                dut,
                a,
                b,
                opcode
            )

    # ---------------------------------------------------------
    # Randomized verification
    # ---------------------------------------------------------

    random.seed(26)

    for _ in range(100):

        a = random.getrandbits(32)
        b = random.getrandbits(32)
        opcode = random.randrange(8)

        await run_alu_case(
            dut,
            a,
            b,
            opcode
        )

    dut._log.info(
        "All 8 ALU operations passed directed and randomized tests."
    )