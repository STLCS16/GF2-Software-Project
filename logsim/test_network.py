import pytest

from names import Names
from devices import Devices
from network import Network


@pytest.fixture
def new_network():
    new_names = Names()
    new_devices = Devices(new_names)
    return Network(new_names, new_devices)


@pytest.fixture
def network_with_devices():
    new_names = Names()
    new_devices = Devices(new_names)
    new_network = Network(new_names, new_devices)

    [SW1_ID, SW2_ID, OR1_ID] = new_names.lookup(["Sw1", "Sw2", "Or1"])

    new_devices.make_device(SW1_ID, new_devices.SWITCH, 0)
    new_devices.make_device(SW2_ID, new_devices.SWITCH, 0)
    new_devices.make_device(OR1_ID, new_devices.OR, 2)

    return new_network


def test_get_connected_output(network_with_devices):
    network = network_with_devices
    devices = network.devices
    names = devices.names

    [SW1_ID, SW2_ID, OR1_ID, I1, I2] = names.lookup(
        ["Sw1", "Sw2", "Or1", "I1", "I2"])

    assert network.get_connected_output(OR1_ID, I1) is None
    assert network.get_connected_output(OR1_ID, I2) is None

    network.make_connection(SW1_ID, None, OR1_ID, I1)
    network.make_connection(SW2_ID, None, OR1_ID, I2)

    assert network.get_connected_output(OR1_ID, I1) == (SW1_ID, None)
    assert network.get_connected_output(OR1_ID, I2) == (SW2_ID, None)

    assert network.get_connected_output(SW1_ID, I2) is None


def test_get_input_signal(network_with_devices):
    network = network_with_devices
    devices = network.devices
    names = devices.names

    [SW1_ID, SW2_ID, OR1_ID, I1, I2] = names.lookup(
        ["Sw1", "Sw2", "Or1", "I1", "I2"])

    assert network.get_input_signal(OR1_ID, I1) is None
    assert network.get_input_signal(OR1_ID, I2) is None

    network.make_connection(SW1_ID, None, OR1_ID, I1)
    network.make_connection(SW2_ID, None, OR1_ID, I2)

    switch2 = devices.get_device(SW2_ID)
    switch2.outputs[None] = devices.HIGH

    assert network.get_input_signal(OR1_ID, I1) == devices.LOW
    assert network.get_input_signal(OR1_ID, I2) == devices.HIGH


def test_get_output_signal(network_with_devices):
    network = network_with_devices
    devices = network.devices
    names = devices.names

    [OR1_ID] = names.lookup(["Or1"])

    assert network.get_output_signal(OR1_ID, None) == devices.LOW

    or1 = devices.get_device(OR1_ID)
    or1.outputs[None] = devices.HIGH

    assert network.get_output_signal(OR1_ID, None) == devices.HIGH


def test_check_network(network_with_devices):
    network = network_with_devices
    devices = network.devices
    names = devices.names

    [SW1_ID, SW2_ID, OR1_ID, I1, I2] = names.lookup(
        ["Sw1", "Sw2", "Or1", "I1", "I2"])

    assert not network.check_network()

    network.make_connection(SW1_ID, None, OR1_ID, I1)
    network.make_connection(SW2_ID, None, OR1_ID, I2)

    assert network.check_network()


def test_make_connection(network_with_devices):
    network = network_with_devices
    devices = network.devices
    names = devices.names

    [SW1_ID, SW2_ID, OR1_ID, I1, I2] = names.lookup(
        ["Sw1", "Sw2", "Or1", "I1", "I2"])

    or1 = devices.get_device(OR1_ID)

    assert or1.inputs == {I1: None, I2: None}

    network.make_connection(SW1_ID, None, OR1_ID, I1)
    network.make_connection(SW2_ID, None, OR1_ID, I2)

    assert or1.inputs == {I1: (SW1_ID, None), I2: (SW2_ID, None)}


@pytest.mark.parametrize("function_args, error", [
    ("(I1, I1, OR1_ID, I2)", "network.DEVICE_ABSENT"),

    # Change this line from INPUT_TO_INPUT to RECURSIVE
    ("(OR1_ID, I2, OR1_ID, I2)", "network.RECURSIVE"),

    ("(SW1_ID, None, OR1_ID, None)", "network.OUTPUT_TO_OUTPUT"),
    ("(SW1_ID, I1, OR1_ID, I2)", "network.PORT_ABSENT"),
    ("(SW2_ID, None, OR1_ID, I2)", "network.NO_ERROR"),
    ("(OR1_ID, I2, SW2_ID, None)", "network.NO_ERROR"),
    ("(SW1_ID, None, OR1_ID, I1)", "network.INPUT_CONNECTED"),
])
def test_make_connection_gives_error(
        network_with_devices,
        function_args,
        error):
    network = network_with_devices
    devices = network.devices
    names = devices.names

    [SW1_ID, SW2_ID, OR1_ID, I1, I2] = names.lookup(
        ["Sw1", "Sw2", "Or1", "I1", "I2"])

    network.make_connection(SW1_ID, None, OR1_ID, I1)

    left_expression = eval("".join(["network.make_connection", function_args]))
    right_expression = eval(error)

    if isinstance(left_expression, tuple):
        assert left_expression[0] == right_expression
    else:
        assert left_expression == right_expression


def test_execute_xor(new_network):
    network = new_network
    devices = network.devices
    names = devices.names

    [SW1_ID, SW2_ID, XOR1_ID, I1, I2] = names.lookup(
        ["Sw1", "Sw2", "Xor1", "I1", "I2"])

    devices.make_device(XOR1_ID, devices.XOR)
    devices.make_device(SW1_ID, devices.SWITCH, 0)
    devices.make_device(SW2_ID, devices.SWITCH, 0)

    network.make_connection(SW1_ID, None, XOR1_ID, I1)
    network.make_connection(SW2_ID, None, XOR1_ID, I2)

    network.execute_network()
    assert new_network.get_output_signal(XOR1_ID, None) == devices.LOW

    devices.set_switch(SW1_ID, devices.HIGH)
    network.execute_network()
    assert network.get_output_signal(XOR1_ID, None) == devices.HIGH

    devices.set_switch(SW2_ID, devices.HIGH)
    network.execute_network()
    assert network.get_output_signal(XOR1_ID, None) == devices.LOW


@pytest.mark.parametrize("gate_id, switch_outputs, gate_output, gate_kind", [
    ("AND1_ID", ["LOW", "HIGH", "LOW"], "LOW", "devices.AND"),
    ("AND1_ID", ["HIGH", "HIGH", "HIGH"], "HIGH", "devices.AND"),
    ("NAND1_ID", ["HIGH", "HIGH", "HIGH"], "LOW", "devices.NAND"),
    ("NAND1_ID", ["HIGH", "HIGH", "LOW"], "HIGH", "devices.NAND"),
    ("OR1_ID", ["LOW", "LOW", "LOW"], "LOW", "devices.OR"),
    ("OR1_ID", ["LOW", "HIGH", "HIGH"], "HIGH", "devices.OR"),
    ("NOR1_ID", ["HIGH", "LOW", "HIGH"], "LOW", "devices.NOR"),
    ("NOR1_ID", ["LOW", "LOW", "LOW"], "HIGH", "devices.NOR"),
])
def test_execute_non_xor_gates(
        new_network,
        gate_id,
        switch_outputs,
        gate_output,
        gate_kind):
    network = new_network
    devices = network.devices
    names = devices.names

    [AND1_ID, OR1_ID, NAND1_ID, NOR1_ID,
     SW1_ID, SW2_ID, SW3_ID, I1, I2, I3] = names.lookup(
        ["And1", "Or1", "Nand1", "Nor1",
         "Sw1", "Sw2", "Sw3", "I1", "I2", "I3"])

    LOW = devices.LOW
    HIGH = devices.HIGH

    gate_id = eval(gate_id)
    gate_kind = eval(gate_kind)
    devices.make_device(gate_id, gate_kind, 3)
    devices.make_device(SW1_ID, devices.SWITCH, 0)
    devices.make_device(SW2_ID, devices.SWITCH, 0)
    devices.make_device(SW3_ID, devices.SWITCH, 0)

    network.make_connection(SW1_ID, None, gate_id, I1)
    network.make_connection(SW2_ID, None, gate_id, I2)
    network.make_connection(SW3_ID, None, gate_id, I3)

    switches = [SW1_ID, SW2_ID, SW3_ID]
    for i, switch_output in enumerate(switch_outputs):
        devices.set_switch(switches[i], eval(switch_output))

    network.execute_network()
    assert network.get_output_signal(gate_id, None) == eval(gate_output)


def test_execute_non_gates(new_network):
    network = new_network
    devices = network.devices
    names = devices.names

    LOW = devices.LOW
    HIGH = devices.HIGH

    [SW1_ID, SW2_ID, SW3_ID, CL_ID, D_ID] = names.lookup(
        ["Sw1", "Sw2", "Sw3", "Clock1", "D1"])
    devices.make_device(SW1_ID, devices.SWITCH, 1)
    devices.make_device(SW2_ID, devices.SWITCH, 0)
    devices.make_device(SW3_ID, devices.SWITCH, 0)
    devices.make_device(CL_ID, devices.CLOCK, 1)
    devices.make_device(D_ID, devices.D_TYPE)

    network.make_connection(SW1_ID, None, D_ID, devices.DATA_ID)
    network.make_connection(CL_ID, None, D_ID, devices.CLK_ID)
    network.make_connection(SW2_ID, None, D_ID, devices.SET_ID)
    network.make_connection(SW3_ID, None, D_ID, devices.CLEAR_ID)

    sw1_output = "network.get_output_signal(SW1_ID, None)"
    sw2_output = "network.get_output_signal(SW2_ID, None)"
    sw3_output = "network.get_output_signal(SW3_ID, None)"
    clock_output = "network.get_output_signal(CL_ID, None)"
    dtype_Q = "network.get_output_signal(D_ID, devices.Q_ID)"
    dtype_QBAR = "network.get_output_signal(D_ID, devices.QBAR_ID)"

    clock_device = devices.get_device(CL_ID)
    network.execute_network()
    while clock_device.clock_counter != 1 or eval(clock_output) != LOW:
        network.execute_network()

    assert [
        eval(sw1_output),
        eval(sw2_output),
        eval(sw3_output),
        eval(clock_output)] == [
        HIGH,
        LOW,
        LOW,
        LOW]
    assert eval(dtype_Q) in [HIGH, LOW]
    assert eval(dtype_QBAR) == network.invert_signal(eval(dtype_Q))

    network.execute_network()

    assert [
        eval(sw1_output),
        eval(sw2_output),
        eval(sw3_output),
        eval(clock_output),
        eval(dtype_Q),
        eval(dtype_QBAR)] == [
        HIGH,
        LOW,
        LOW,
        HIGH,
        HIGH,
        LOW]

    devices.set_switch(SW1_ID, LOW)
    devices.set_switch(SW2_ID, HIGH)
    network.execute_network()
    network.execute_network()

    assert [
        eval(sw1_output),
        eval(sw2_output),
        eval(sw3_output),
        eval(clock_output),
        eval(dtype_Q),
        eval(dtype_QBAR)] == [
        LOW,
        HIGH,
        LOW,
        HIGH,
        HIGH,
        LOW]

    devices.set_switch(SW1_ID, HIGH)
    devices.set_switch(SW2_ID, LOW)
    devices.set_switch(SW3_ID, HIGH)
    network.execute_network()
    network.execute_network()

    assert [
        eval(sw1_output),
        eval(sw2_output),
        eval(sw3_output),
        eval(clock_output),
        eval(dtype_Q),
        eval(dtype_QBAR)] == [
        HIGH,
        LOW,
        HIGH,
        HIGH,
        LOW,
        HIGH]


def test_oscillating_network(new_network):
    network = new_network
    devices = network.devices
    names = devices.names

    [NOR1, I1] = names.lookup(["Nor1", "I1"])

    devices.make_device(NOR1, devices.NOR, 1)
    network.make_connection(NOR1, None, NOR1, I1)

    assert not network.execute_network()


def test_execute_rc(new_network):
    network = new_network
    devices = network.devices
    names = devices.names

    [RC1_ID] = names.lookup(["Rc1"])

    devices.make_device(RC1_ID, devices.RC, 2)
    rc_device = devices.get_device(RC1_ID)
    rc_device.outputs[None] = devices.HIGH

    network.execute_network(cycle_num=1)
    assert network.get_output_signal(RC1_ID, None) == devices.HIGH

    network.execute_network(cycle_num=2)
    assert network.get_output_signal(RC1_ID, None) == devices.HIGH

    network.execute_network(cycle_num=3)
    assert network.get_output_signal(RC1_ID, None) == devices.LOW
