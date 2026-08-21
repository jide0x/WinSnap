import unittest

from winsnap.collectors.firewall_rules import (
    _action,
    _direction,
    _enabled,
    _local_port,
    _named_port,
    _parse_rule,
    _profiles,
    _protocol,
    _remote_port,
)


class FirewallRuleParseTests(unittest.TestCase):
    def test_parse_rule_collects_repeated_keys(self):
        pairs = _parse_rule("v2.33|Action=Allow|Profile=Domain|Profile=Private")
        self.assertEqual(pairs["Action"], ["Allow"])
        self.assertEqual(pairs["Profile"], ["Domain", "Private"])

    def test_direction(self):
        self.assertEqual(_direction(_parse_rule("Dir=In")), "Inbound")
        self.assertEqual(_direction(_parse_rule("Dir=Out")), "Outbound")

    def test_action(self):
        self.assertEqual(_action(_parse_rule("Action=Block")), "Block")

    def test_enabled(self):
        self.assertTrue(_enabled(_parse_rule("Active=TRUE")))
        self.assertFalse(_enabled(_parse_rule("Active=FALSE")))

    def test_protocol_names(self):
        self.assertEqual(_protocol(_parse_rule("Protocol=6")), "TCP")
        self.assertEqual(_protocol(_parse_rule("Protocol=17")), "UDP")
        self.assertEqual(_protocol(_parse_rule("Protocol=58")), "ICMPv6")
        self.assertEqual(_protocol(_parse_rule("Protocol=47")), "47")
        self.assertEqual(_protocol(_parse_rule("Action=Allow")), "Any")

    def test_named_port_mapping(self):
        self.assertEqual(_named_port("RPC-EPMap"), "RPCEPMap")
        self.assertEqual(_named_port("Ply2Disc"), "PlayToDiscovery")
        self.assertEqual(_named_port("5353"), "5353")

    def test_local_port_repeated_joins(self):
        pairs = _parse_rule("LPort=23554|LPort=23555|LPort=23556")
        self.assertEqual(_local_port(pairs), "23554,23555,23556")

    def test_local_port_named(self):
        pairs = _parse_rule("LPort=RPC-EPMap")
        self.assertEqual(_local_port(pairs), "RPCEPMap")

    def test_local_port_lport2(self):
        pairs = _parse_rule("LPort2_10=8081-8112")
        self.assertEqual(_local_port(pairs), "8081-8112")

    def test_local_port_icmp(self):
        self.assertEqual(_local_port(_parse_rule("ICMP6=134:*")), "RPC")
        self.assertEqual(_local_port(_parse_rule("Action=Allow")), "Any")

    def test_remote_port(self):
        self.assertEqual(_remote_port(_parse_rule("RPort=443")), "443")
        self.assertEqual(_remote_port(_parse_rule("Action=Allow")), "Any")

    def test_profiles(self):
        self.assertEqual(_profiles(_parse_rule("Profile=Domain|Profile=Private")), "Domain, Private")
        self.assertEqual(_profiles(_parse_rule("Profile=Public|Profile=Domain")), "Domain, Public")
        self.assertEqual(_profiles(_parse_rule("Action=Allow")), "Any")


if __name__ == "__main__":
    unittest.main()
