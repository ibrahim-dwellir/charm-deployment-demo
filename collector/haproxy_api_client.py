import httpx

class HAProxyAPIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = httpx.BasicAuth(username=username, password=password)
        self.client = httpx.Client(auth=self.auth)

    def get_backends(self):
        resp = self.client.get(f"{self.base_url}/v3/services/haproxy/configuration/backends")
        resp.raise_for_status()
        return resp.json()

    def get_backend_servers(self, backend_name: str):
        resp = self.client.get(f"{self.base_url}/v3/services/haproxy/configuration/backends/{backend_name}/servers")
        resp.raise_for_status()
        return resp.json()

    def get_backend_http_request_rules(self, backend_name: str):
        resp = self.client.get(f"{self.base_url}/v3/services/haproxy/configuration/backends/{backend_name}/http_request_rules")
        resp.raise_for_status()
        return resp.json()
    
    def get_frontends(self):
        resp = self.client.get(f"{self.base_url}/v3/services/haproxy/configuration/frontends")
        resp.raise_for_status()
        return resp.json()

    def get_acls(self, frontend_name: str):
        resp = self.client.get(f"{self.base_url}/v3/services/haproxy/configuration/frontends/{frontend_name}/acls")
        resp.raise_for_status()
        return resp.json()

    def get_backend_switching_rules(self, frontend_name: str):
        resp = self.client.get(f"{self.base_url}/v3/services/haproxy/configuration/frontends/{frontend_name}/backend_switching_rules")
        resp.raise_for_status()
        return resp.json()
