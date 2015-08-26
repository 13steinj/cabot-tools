import socket


def _get_local_domain_suffix():
    local_fqdn = socket.getfqdn()
    return ".".join(local_fqdn.split(".")[1:])


def is_bare_hostname(hostname):
    return "." not in hostname


def append_local_domain_suffix(hostname):
    return hostname + "." + _get_local_domain_suffix()


def get_local_part(fqdn):
    return fqdn.split(".")[0]


def reverse(fqdn):
    return ".".join(reversed(fqdn.split(".")))
