import unittest
from unittest.mock import patch

from cabot_tools import hostnames


class GetLocalDomainSuffixTests(unittest.TestCase):
    @patch("socket.getfqdn")
    def test_suffix(self, getfqdn):
        getfqdn.return_value = "local.example.com"
        suffix = hostnames._get_local_domain_suffix()
        self.assertEqual(suffix, "example.com")


class IsBareHostnameTests(unittest.TestCase):
    def test_bare_hostname(self):
        self.assertTrue(hostnames.is_bare_hostname("example-server"))

    def test_qualified_domain(self):
        self.assertFalse(hostnames.is_bare_hostname("example.com"))


class AppendLocalDomainSuffixTests(unittest.TestCase):
    @patch("cabot_tools.hostnames._get_local_domain_suffix")
    def test_append(self, _get_local_domain_suffix):
        _get_local_domain_suffix.return_value = "example.com"
        fqdn = hostnames.append_local_domain_suffix("server")
        self.assertEqual(fqdn, "server.example.com")


class GetLocalPartTests(unittest.TestCase):
    def test_fqdn(self):
        local = hostnames.get_local_part("server.example.com")
        self.assertEqual(local, "server")

    def test_bare(self):
        local = hostnames.get_local_part("server")
        self.assertEqual(local, "server")


class ReverseTests(unittest.TestCase):
    def test_fqdn(self):
        local = hostnames.reverse("server.example.com")
        self.assertEqual(local, "com.example.server")

    def test_bare(self):
        local = hostnames.reverse("server")
        self.assertEqual(local, "server")
