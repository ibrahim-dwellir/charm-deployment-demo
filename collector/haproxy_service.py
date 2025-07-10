from haproxy_api_client import HAProxyAPIClient
from haproxy_data_parser import (
    extract_backend_names,
    extract_server_ips,
    extract_destination_servers,
    extract_acls_domains,
    extract_backend_switching_rules,
    extract_frontend_names
)

class HAProxyService:
    def __init__(self, haproxy_url: str, auth_username: str, auth_password: str):
        self.api_client = HAProxyAPIClient(haproxy_url, auth_username, auth_password)
    
    def get_domains_to_ips(self) -> list[tuple[str, str]]:
        """
        Fetches the list of domains and their corresponding IP addresses from HAProxy.
        This method retrieves backend names, destination servers, and applies any backend switching rules
        to map domains to their respective servers.

        :return: A list of (domain, server_ip) tuples.
        """
        backends_json = self.api_client.get_backends()
        backends = extract_backend_names(backends_json)
        backend_switches = self._get_backend_switches()
        backend_servers = []
        for backend in backends:
            # Skip backends that are not in the backend_switches or do not end with ".dwellir.com"
            # This is to avoid processing backends that are not relevant for the current context.
            if backend_switches and backend not in backend_switches and not backend.endswith(".dwellir.com"):
                continue
            dest_servers_json = self.api_client.get_backend_http_request_rules(backend)
            servers = extract_destination_servers(dest_servers_json) or \
                    extract_server_ips(self.api_client.get_backend_servers(backend))
            
            # If there is a backend switching rule, use it to get the domains
            # Otherwise, use the backend name as the domain.
            domains = backend_switches.get(backend, [backend])

            for server in servers:
                for domain in domains:
                    backend_servers.append((domain, server))
        return backend_servers

    def _get_backend_switches(self) -> dict:
        frontend_json = self.api_client.get_frontends()
        frontend_names = extract_frontend_names(frontend_json)
        # If no frontends are found, return an empty dictionary
        if not frontend_names:
            return {}
        
        backend_switches = {}
        for frontend_name in frontend_names:
            # Fetch ACLs for each frontend
            acls_json = self.api_client.get_acls(frontend_name)
            if not acls_json:
                continue
            
            # Extract domains from ACLs
            acls_domains = extract_acls_domains(acls_json)
            if not acls_domains:
                continue
            
            # Fetch backend switching rules for each frontend
            rules_json = self.api_client.get_backend_switching_rules(frontend_name)
            if not rules_json:
                continue
            
            backend_switching_rules = extract_backend_switching_rules(rules_json)
            if not backend_switching_rules:
                continue
            backend_switch = {backend_switching_rules.get(backend, backend): domains for backend, domains in acls_domains.items()}
            backend_switches.update(backend_switch)
        
        return backend_switches
