import json
import urllib.parse

import requests


class Cabot(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = (username, password)
        self.session = requests.Session()

    def _make_request(self, method, path, data=None, **kwargs):
        url = urllib.parse.urljoin(self.base_url, path)

        if data:
            data = json.dumps(data)

        resp = self.session.request(
            method, url,
            auth=self.auth,
            headers={
                "Content-Type": "application/json",
            },
            data=data,
            **kwargs
        )
        resp.raise_for_status()
        return json.loads(resp.text)

    @property
    def services(self):
        return ResourceProxy(self, "services")

    @property
    def instances(self):
        return ResourceProxy(self, "instances")

    def check_resource(self, name):
        return ResourceProxy(self, "{}_checks".format(name))


class ResourceProxy(object):
    def __init__(self, cabot, name):
        self.cabot = cabot
        self.name = name

    def _url_for_id(self, id):
        return "/api/{}/{:d}/".format(self.name, id)

    def query(self, **query):
        content = self.cabot._make_request(
            "GET", "/api/{}/".format(self.name), params=query)
        return [ObjectProxy(self, blob) for blob in content]

    def create(self, data):
        content = self.cabot._make_request(
            "POST", "/api/{}/".format(self.name), data=data)
        return ObjectProxy(self, content)


class ObjectProxy(object):
    __slots__ = ("resource", "data", "dirties")

    def __init__(self, resource, data):
        self.resource = resource
        self.data = data

    def __getattr__(self, key):
        try:
            return self.data[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self.__slots__:
            object.__setattr__(self, key, value)
            return

        if key not in self.data or self.data[key] != value:
            self.data[key] = value

    def patch(self, properties):
        url = self.resource._url_for_id(self.id)
        changes = {key: self.data[key] for key in properties}
        response = self.resource.cabot._make_request(
            "PATCH", url, data=changes)
        self.data = response
