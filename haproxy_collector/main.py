import json
import os
import logging
from haproxy_service import HAProxyService

haproxy_url = os.getenv("HAPROXY_URL")
auth_username = os.getenv("HAPROXY_USERNAME")
auth_password = os.getenv("HAPROXY_PASSWORD")

if not haproxy_url or not auth_username or not auth_password:
    logging.error("Environment variables HAPROXY_URL, HAPROXY_USERNAME, and HAPROXY_PASSWORD must be set.")
    exit(1)

try:
    haproxy_service = HAProxyService(haproxy_url, auth_username, auth_password)
    backend_servers = haproxy_service.get_domains_to_ips()
    print (json.dumps(backend_servers, indent=2))
except Exception as e:
    logging.error(f"Failed to fetch backend servers: {e}")
    exit(1)

