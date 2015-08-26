import collections
import configparser


Check = collections.namedtuple("Check", ["cabot_model", "parameters"])


def build_basic_check_parameters(check_name, check_config):
    return {
        "name": check_name,
        "active": True,
        "importance": check_config["importance"],
        "frequency": int(check_config.get("frequency", 5)),
        "debounce": int(check_config.get("debounce", 0)),
    }


def build_graphite_check(check_name, check_config):
    params = build_basic_check_parameters(check_name, check_config)
    params.update({
        "metric": check_config["metric"],
        "check_type": check_config["check_type"],
        "value": float(check_config["value"]),
        "expected_num_hosts": int(check_config.get("expected_num_hosts", 0)),
        "expected_num_metrics": int(check_config.get("expected_num_metrics", 0)),
    })
    return Check("graphite", params)


def build_http_check(check_name, check_config):
    params = build_basic_check_parameters(check_name, check_config)
    verify_ssl_certificate = check_config.get("verify_ssl_certificate", "true"),
    params.update({
        "endpoint": check_config["endpoint"],
        "username": check_config.get("username", ""),
        "password": check_config.get("password", ""),
        "text_match": check_config.get("text_match", ""),
        "status_code": int(check_config.get("status_code", 200)),
        "timeout": int(check_config.get("timeout", 30)),
        "verify_ssl_certificate": configparser.ConfigParser.BOOLEAN_STATES[verify_ssl_certificate],
    })
    return Check("http", params)


def build_icmp_check(check_name, check_config):
    params = build_basic_check_parameters(check_name, check_config)
    return Check("icmp", params)


def build_jenkins_check(check_name, check_config):
    params = build_basic_check_parameters(check_name, check_config)
    params.update({
        "max_queued_build_time": int(check_config.get("max_queued_build_time", 0)),
    })
    return Check("jenkins", params)


class TemplatedCheckBuilder(object):
    def __init__(self, factory, template):
        self.factory = factory
        self.template = template

    def __call__(self, check_name, template_config):
        check_config = {key: self.template.get(key, vars=template_config)
                        for key in self.template.keys()}
        check_config.update(template_config)
        check_config["class"] = self.template["class"]
        return self.factory.build_check(check_name, check_config)


class CheckFactory(object):
    def __init__(self, template_filename):
        self.builders_by_class = {
            "graphite": build_graphite_check,
            "http": build_http_check,
            "jenkins": build_jenkins_check,
            "icmp": build_icmp_check,
        }

        template_parser = configparser.ConfigParser()
        with open(template_filename) as f:
            template_parser.read_file(f)

        for template_name, template in template_parser.items():
            if template_name == "DEFAULT":
                continue

            check = TemplatedCheckBuilder(self, template)
            self.builders_by_class[template_name] = check

    def build_check(self, check_name, check_config):
        check_class = check_config["class"]
        builder = self.builders_by_class[check_class]
        return builder(check_name, check_config)

    def load_checks(self, checkfiles, variables):
        parser = configparser.ConfigParser(defaults=variables)
        parser.read(checkfiles)

        checks = []
        for check_name, check_config in parser.items():
            if check_name == "DEFAULT":
                continue
            check = self.build_check(check_name, check_config)
            checks.append(check)
        return checks
