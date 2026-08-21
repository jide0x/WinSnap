import unittest

from winsnap.collectors.network_listeners import _ipv4_to_str, _ipv6_to_str, _port_to_int


class NativeNetworkHelpersTests(unittest.TestCase):
    def test_ipv4_loopback(self):
        self.assertEqual(_ipv4_to_str(0x0100007F), "127.0.0.1")

    def test_ipv4_any(self):
        self.assertEqual(_ipv4_to_str(0), "0.0.0.0")

    def test_ipv4_private(self):
        self.assertEqual(_ipv4_to_str(0xB501A8C0), "192.168.1.181")

    def test_ipv6_any(self):
        self.assertEqual(_ipv6_to_str(bytes(16)), "::")

    def test_ipv6_with_scope(self):
        addr = bytes.fromhex("fe800000000000000000000000000001")
        self.assertEqual(_ipv6_to_str(addr, 17), "fe80::1%17")

    def test_ipv6_without_scope(self):
        addr = bytes.fromhex("fe800000000000000000000000000001")
        self.assertEqual(_ipv6_to_str(addr, 0), "fe80::1")

    def test_port_network_byte_order(self):
        self.assertEqual(_port_to_int(0x00008700), 135)
        self.assertEqual(_port_to_int(0x0000B013), 5040)


if __name__ == "__main__":
    unittest.main()
