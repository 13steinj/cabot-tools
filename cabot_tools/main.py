"""
Given the name of a service in Cabot and the hostname of an instance, this
tool looks at all of the puppet modules included for the host and compiles
their cabot-checks.ini checklists into a single master list and then
creates an instance, adds those checks to it, and adds the instance to the
specified service.

Checks can take advantage of templates in cabot-check-templates.ini in the
puppet root.  These are intended to reduce repetition for common check
patterns.

If the hostname is not fully qualified, the domain suffix of the server
this script is running on is appended.

By default, if no classes are specified, it will ask Puppet to compile
manifests for the node and then will look for checklists in each of the
classes included in the node's manifests.

WARNING: at the moment, no attempt to reconcile pre-existing instances or
checks is made.  If you rerun this script multiple times you will end up
with multiple copies of the same instance in Cabot.

"""
import argparse
import configparser
import os
import sys

from . import cabot_api, checks, hostnames, puppet


def load_configuration():
    parser = configparser.ConfigParser()
    with open("/etc/cabot_checks.ini") as f:
        parser.read_file(f)
    return parser


def parse_arguments():
    arg_parser = argparse.ArgumentParser(
        description="Add Cabot checks for an instance.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    arg_parser.add_argument(
        "service",
        help="name of a service in Cabot to add this instance to",
        metavar="SERVICE",
    )

    arg_parser.add_argument(
        "host",
        help="hostname or FQDN of instance to add",
        metavar="HOST",
    )

    arg_parser.add_argument(
        "--classes",
        help="override list of puppet classes to get checks from",
        nargs="+",
        metavar="CLASS",
        default=None,
    )

    return arg_parser.parse_args()


def main():
    try:
        configuration = load_configuration()
        args = parse_arguments()

        if hostnames.is_bare_hostname(args.host):
            args.host = hostnames.append_local_domain_suffix(args.host)
        print("Beginning Cabot check configuration for {}.".format(args.host))

        # validate the service exists
        cabot_url = configuration["cabot"]["url"]
        cabot = cabot_api.Cabot(
            cabot_url,
            configuration["cabot"]["username"],
        )

        print("Looking up service...")
        services = cabot.services.query(name=args.service)
        if not services:
            raise ValueError("could not find a service called {!r}".format(args.service))
        elif len(services) > 1:
            raise ValueError("there are multiple services called {!r}".format(args.service))

        if not args.classes:
            print("Auto-discovering Puppet classes...")
            args.classes = puppet.classes_by_node(args.host)
        print("Loaded {:d} puppet classes.".format(len(args.classes)))

        puppet_root = configuration["puppet"]["root"]
        checkfiles = puppet.checkfiles_for_classes(
            puppet_root, args.classes)

        variables = {
            "fqdn": args.host,
            "fqdn_rev": hostnames.reverse(args.host),
            "hostname": hostnames.get_local_part(args.host),
        }

        print("Loading checks...")
        template_filename = configuration["checks"]["template-file"]
        factory = checks.CheckFactory(template_filename)
        checks_for_instance = factory.load_checks(checkfiles, variables)

        if checks_for_instance:
            print("Loaded {:d} checks.".format(len(checks_for_instance)))
        else:
            print("No checks found. Bailing out.")
            sys.exit(0)

        # add all the checks
        print("Creating checks in Cabot...")
        check_ids = []
        for check in checks_for_instance:
            print("  - {}".format(check.parameters["name"]))
            resource = cabot.check_resource(check.cabot_model)
            check = resource.create(check.parameters)
            check_ids.append(check.id)

        # create or update the instance with the checks
        print("Creating instance in Cabot...")
        instance = cabot.instances.create({
            "name": variables["hostname"],
            "address": args.host,
            "alerts_enabled": True,
            "status_checks": check_ids,
            "alerts": [],
            "hackpad_id": "",
        })

        print("Adding instance to service...")
        services = cabot.services.query(name=args.service)
        assert len(services) == 1
        service = services[0]
        service.instances.append(instance.id)
        service.patch(["instances"])

        print()
        cabot_vanity_url = configuration["cabot"]["vanity-url"]
        print("Checks created. See: {}/instance/{:d}/".format(
            cabot_vanity_url, instance.id))
    except Exception as e:
        progname = os.path.basename(sys.argv[0])
        print("{}: ERROR: {}".format(progname, e), file=sys.stderr)
        sys.exit(1)
