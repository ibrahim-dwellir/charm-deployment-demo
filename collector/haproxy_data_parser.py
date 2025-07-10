import re

def extract_backend_names(backends_json):
    return [backend["name"] for backend in backends_json if "name" in backend]

def extract_frontend_names(frontends_json):
    return [frontend["name"] for frontend in frontends_json if "name" in frontend]

def extract_server_ips(servers_json):
    return [server["address"] for server in servers_json if "address" in server]

def extract_destination_servers(http_request_rules_json):
    endpoints = next((item["hdr_format"] for item in http_request_rules_json if "hdr_name" in item and item["hdr_name"] == "X-Destination-Backend" and "cond" not in item), None)
    if not endpoints:
        return None
    return [match.group(1) for match in re.finditer(r'(\d+\.\d+\.\d+\.\d+):\d+', endpoints)] or None

def extract_acls_domains(acls_json):
    return {acl["acl_name"]: acl["value"][10:].split(" || ") for acl in acls_json if acl["value"].startswith("-i -m dom ")}

def extract_backend_switching_rules(rules_json):
    return {rule["cond_test"]: rule["name"] for rule in rules_json if "name" in rule and "cond_test" in rule}
