import json
import os
import subprocess


def classes_by_node(fqdn):
    catalog_json = subprocess.check_output([
        "/usr/bin/sudo",
        "/usr/bin/puppet",
        "catalog",
        "--render-as", "json",
        "find",
        fqdn,
    ]).decode("utf-8")

    # get rid of puppet's stupid colorized warning messages that come via stdout
    catalog_json = "\n".join(
        line for line in catalog_json.splitlines() if not line.startswith("\x1b"))

    catalog = json.loads(catalog_json)
    return catalog["data"]["classes"]


def _checkfile_for_class(root, puppet_class):
    assert "." not in puppet_class and "/" not in puppet_class
    remapped = puppet_class.replace("::", "/")
    return os.path.join(root, "modules", remapped, "cabot-checks.ini")


def checkfiles_for_classes(root, classes):
    return [_checkfile_for_class(root, puppet_class) for puppet_class in classes]
