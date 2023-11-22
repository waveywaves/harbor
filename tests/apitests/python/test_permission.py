import json
import random
import requests
import urllib3
import os
from urllib.parse import urlsplit


user_name = os.environ.get("USER_NAME")
password = os.environ.get("PASSWORD")
admin_user_name = os.environ.get("ADMIN_USER_NAME")
admin_password = os.environ.get("ADMIN_PASSWORD")
harbor_base_url = os.environ.get("HARBOR_BASE_URL")
resource = os.environ.get("RESOURCE")
ID_PLACEHOLDER = "(id)"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Permission:


    def __init__(self, url, method, expect_status_code, payload=None, res_id_field=None, payload_id_field=None, id_from_header=False):
        self.url = url
        self.method = method
        self.expect_status_code = expect_status_code
        self.payload = payload
        self.res_id_field = res_id_field
        self.payload_id_field = payload_id_field if payload_id_field else res_id_field
        self.id_from_header = id_from_header


    def call(self):
        if ID_PLACEHOLDER in self.url:
            self.url = self.url.replace(ID_PLACEHOLDER, str(self.payload.get(self.payload_id_field)))
        response = requests.request(self.method, self.url, data=json.dumps(self.payload), verify=False, auth=(user_name, password), headers={"Content-Type": "application/json"})
        assert response.status_code == self.expect_status_code, "Failed to call the {} {}, expected status code is {}, but got {}, error msg is {}".format(self.method, self.url, self.expect_status_code, response.status_code, response.text)
        if self.res_id_field and self.payload_id_field and self.id_from_header == False:
            self.payload[self.payload_id_field] = int(json.loads(response.text)[self.res_id_field])
        elif self.res_id_field and self.payload_id_field and self.id_from_header == True:
            self.payload[self.payload_id_field] = int(response.headers["Location"].split("/")[-1])


resource_permissions = {}
# audit logs permissions start
list_audit_logs = Permission("{}/audit-logs".format(harbor_base_url), "GET", 200)
audit_log = [ list_audit_logs ]
resource_permissions["audit-log"] = audit_log
# audit logs permissions end

# preheat instance permissions start
preheat_instance_payload = {
    "name": "preheat_instance-{}".format(random.randint(1000, 9999)),
    "endpoint": "http://{}".format(random.randint(1000, 9999)),
    "enabled": False,
    "vendor": "dragonfly",
    "auth_mode": "NONE",
    "insecure": True
}
create_preheat_instance = Permission("{}/p2p/preheat/instances".format(harbor_base_url), "POST", 201, preheat_instance_payload)
list_preheat_instance = Permission("{}/p2p/preheat/instances".format(harbor_base_url), "GET", 200, preheat_instance_payload)
read_preheat_instance = Permission("{}/p2p/preheat/instances/{}".format(harbor_base_url, preheat_instance_payload["name"]), "GET", 200, preheat_instance_payload, "id")
update_preheat_instance = Permission("{}/p2p/preheat/instances/{}".format(harbor_base_url, preheat_instance_payload["name"]), "PUT", 200, preheat_instance_payload)
delete_preheat_instance = Permission("{}/p2p/preheat/instances/{}".format(harbor_base_url, preheat_instance_payload["name"]), "DELETE", 200, preheat_instance_payload)
ping_preheat_instance = Permission("{}/p2p/preheat/instances/ping".format(harbor_base_url), "POST", 500, preheat_instance_payload)
preheat_instances = [ create_preheat_instance, list_preheat_instance, read_preheat_instance, update_preheat_instance, delete_preheat_instance ]
resource_permissions["preheat-instance"] = preheat_instances
# preheat instance permissions end

# project permissions start
project_payload = {
	"metadata": {
		"public": "false"
	},
	"project_name": "project-{}".format(random.randint(1000, 9999)),
	"storage_limit": -1
}
create_project = Permission("{}/projects".format(harbor_base_url), "POST", 201, project_payload)
list_project = Permission("{}/projects".format(harbor_base_url), "GET", 200, project_payload)
project = [ create_project, list_project ]
resource_permissions["project"] = project
# project permissions end

# registry permissions start
registry_payload = {
    "insecure": False,
    "name": "registry-{}".format(random.randint(1000, 9999)),
    "type": "docker-hub",
    "url": "https://hub.docker.com"
}
create_registry = Permission("{}/registries".format(harbor_base_url), "POST", 201, registry_payload, "id", id_from_header=True)
list_registry = Permission("{}/registries".format(harbor_base_url), "GET", 200, registry_payload)
read_registry = Permission("{}/registries/{}".format(harbor_base_url, ID_PLACEHOLDER), "GET", 200, registry_payload, payload_id_field="id")
info_registry = Permission("{}/registries/{}/info".format(harbor_base_url, ID_PLACEHOLDER), "GET", 200, registry_payload, payload_id_field="id")
update_registry = Permission("{}/registries/{}".format(harbor_base_url, ID_PLACEHOLDER), "PUT", 200, registry_payload, payload_id_field="id")
delete_registry = Permission("{}/registries/{}".format(harbor_base_url, ID_PLACEHOLDER), "DELETE", 200, registry_payload, payload_id_field="id")
registry_ping_payload = {
    "insecure": False,
    "name": "registry-{}".format(random.randint(1000, 9999)),
    "type": "docker-hub",
    "url": "https://hub.docker.com"
}
ping_registry = Permission("{}/registries/ping".format(harbor_base_url), "POST", 200, registry_ping_payload)
registry = [ create_registry, list_registry, read_registry, info_registry, update_registry, delete_registry, ping_registry ]
resource_permissions["registry"] = registry
# registry permissions end

# replication-adapter permissions start
list_replication_adapters = Permission("{}/replication/adapters".format(harbor_base_url), "GET", 200)
list_replication_adapterinfos = Permission("{}/replication/adapterinfos".format(harbor_base_url), "GET", 200)
replication_adapter = [ list_replication_adapters, list_replication_adapterinfos ]
resource_permissions["replication-adapter"] = replication_adapter
# replication-adapter permissions end

# replication policy  permissions start
replication_registry_id = None
replication_registry_name = "replication-registry-{}".format(random.randint(1000, 9999))
if resource == "replication-policy":
    result = urlsplit(harbor_base_url)
    endpoint_URL = "{}://{}".format(result.scheme, result.netloc)
    replication_registry_payload = {
        "credential": {
            "access_key": admin_user_name,
            "access_secret": admin_password,
            "type": "basic"
        },
        "description": "",
        "insecure": True,
        "name": replication_registry_name,
        "type": "harbor",
        "url": endpoint_URL
    }
    response = requests.post("{}/registries".format(harbor_base_url), data=json.dumps(replication_registry_payload), verify=False, auth=(admin_user_name, admin_password), headers={"Content-Type": "application/json"})
    replication_registry_id = int(response.headers["Location"].split("/")[-1])
replication_policy_payload = {
    "name": "replication_policy_{}".format(random.randint(1000, 9999)),
    "src_registry": None,
    "dest_registry": {
        "id": replication_registry_id
    },
    "dest_namespace": "library",
    "dest_namespace_replace_count": 1,
    "trigger": {
        "type": "manual",
        "trigger_settings": {
            "cron": ""
        }
    },
    "filters": [
        {
            "type": "name",
            "value": "library/**"
        }
    ],
    "enabled": True,
    "deletion": False,
    "override": True,
    "speed": -1,
    "copy_by_chunk": False
}
create_replication_policy = Permission("{}/replication/policies".format(harbor_base_url), "POST", 201, replication_policy_payload, "id", id_from_header=True)
list_replication_policy = Permission("{}/replication/policies".format(harbor_base_url), "GET", 200, replication_policy_payload)
read_replication_policy = Permission("{}/replication/policies/{}".format(harbor_base_url, ID_PLACEHOLDER), "GET", 200, replication_policy_payload, payload_id_field="id")
update_replication_policy = Permission("{}/replication/policies/{}".format(harbor_base_url, ID_PLACEHOLDER), "PUT", 200, replication_policy_payload, payload_id_field="id")
delete_replication_policy = Permission("{}/replication/policies/{}".format(harbor_base_url, ID_PLACEHOLDER), "DELETE", 200, replication_policy_payload, payload_id_field="id")
replication_and_policy = [ create_replication_policy, list_replication_policy, read_replication_policy, update_replication_policy, delete_replication_policy ]
resource_permissions["replication-policy"] = replication_and_policy
# replication policy  permissions end

# replication permissions start
replication_policy_id = None
replication_policy_name = "replication-policy-{}".format(random.randint(1000, 9999))
result = urlsplit(harbor_base_url)
endpoint_URL = "{}://{}".format(result.scheme, result.netloc)
if resource == "replication":
    replication_registry_payload = {
        "credential": {
            "access_key": admin_user_name,
            "access_secret": admin_password,
            "type": "basic"
        },
        "description": "",
        "insecure": True,
        "name": "replication-registry-{}".format(random.randint(1000, 9999)),
        "type": "harbor",
        "url": endpoint_URL
    }
    response = requests.post("{}/registries".format(harbor_base_url), data=json.dumps(replication_registry_payload), verify=False, auth=(admin_user_name, admin_password), headers={"Content-Type": "application/json"})
    replication_registry_id = int(response.headers["Location"].split("/")[-1])
    replication_policy_payload = {
        "name": replication_policy_name,
        "src_registry": None,
        "dest_registry": {
            "id": replication_registry_id
        },
        "dest_namespace": "library",
        "dest_namespace_replace_count": 1,
        "trigger": {
            "type": "manual",
            "trigger_settings": {
                "cron": ""
            }
        },
        "filters": [
            {
                "type": "name",
                "value": "library/**"
            }
        ],
        "enabled": True,
        "deletion": False,
        "override": True,
        "speed": -1,
        "copy_by_chunk": False
    }
    response = requests.post("{}/replication/policies".format(harbor_base_url), data=json.dumps(replication_policy_payload), verify=False, auth=(admin_user_name, admin_password), headers={"Content-Type": "application/json"})
    replication_policy_id = int(response.headers["Location"].split("/")[-1])
replication_execution_payload = {
    "policy_id": replication_policy_id
}
create_replication_execution = Permission("{}/replication/executions".format(harbor_base_url), "POST", 201, replication_execution_payload, "id", id_from_header=True)
list_replication_execution = Permission("{}/replication/executions".format(harbor_base_url), "GET", 200, replication_execution_payload)
read_replication_execution = Permission("{}/replication/executions/{}".format(harbor_base_url, ID_PLACEHOLDER), "GET", 200, replication_execution_payload, payload_id_field="id")
stop_replication_execution = Permission("{}/replication/executions/{}".format(harbor_base_url, ID_PLACEHOLDER), "PUT", 200, replication_execution_payload, payload_id_field="id")
list_replication_execution_tasks = Permission("{}/replication/executions/{}/tasks".format(harbor_base_url, ID_PLACEHOLDER), "GET", 200, replication_execution_payload, payload_id_field="id")
read_replication_execution_task = Permission("{}/replication/executions/{}/tasks/{}".format(harbor_base_url, ID_PLACEHOLDER, 1), "GET", 404, replication_execution_payload, payload_id_field="id")
replication = [ create_replication_execution, list_replication_execution, read_replication_execution, stop_replication_execution, list_replication_execution_tasks, read_replication_execution_task ]
resource_permissions["replication"] = replication
# replication permissions end

# scan all permissions start
scan_all_weekly_schedule_payload = {
    "schedule": {
        "type": "Weekly",
        "cron": "0 0 0 * * 0"
    }
}
scan_all_reset_schedule_payload = {
    "schedule": {
        "type": "None",
        "cron": ""
    }
}
create_scan_all_schedule = Permission("{}/system/scanAll/schedule".format(harbor_base_url), "POST", 201, scan_all_weekly_schedule_payload)
update_scan_all_schedule = Permission("{}/system/scanAll/schedule".format(harbor_base_url), "PUT", 200, scan_all_reset_schedule_payload)
stop_scan_all = Permission("{}/system/scanAll/stop".format(harbor_base_url), "POST", 202)
scan_all_metrics = Permission("{}/scans/all/metrics".format(harbor_base_url), "GET", 200)
scan_all_schedule_metrics = Permission("{}/scans/schedule/metrics".format(harbor_base_url), "GET", 200)
scan_all = [ create_scan_all_schedule, update_scan_all_schedule, stop_scan_all, scan_all_metrics, scan_all_schedule_metrics ]
resource_permissions["scan-all"] = scan_all
# scan all permissions end

# system volumes permissions start
read_system_volumes = Permission("{}/systeminfo/volumes".format(harbor_base_url), "GET", 200)
system_volumes = [ read_system_volumes ]
resource_permissions["system-volumes"] = system_volumes
# system volumes permissions end

# jobservice monitor permissions start
list_jobservice_pool = Permission("{}/jobservice/pools".format(harbor_base_url), "GET", 200)
list_jobservice_pool_worker = Permission("{}/jobservice/pools/{}/workers".format(harbor_base_url, "88888888"), "GET", 200)
stop_jobservice_job = Permission("{}/jobservice/jobs/{}".format(harbor_base_url, "88888888"), "PUT", 200)
get_jobservice_job_log = Permission("{}/jobservice/jobs/{}/log".format(harbor_base_url, "88888888"), "GET", 500)
list_jobservice_queue = Permission("{}/jobservice/queues".format(harbor_base_url), "GET", 200)
stop_jobservice = Permission("{}/jobservice/queues/{}".format(harbor_base_url, "88888888"), "PUT", 200, payload={ "action": "stop" })
jobservice_monitor = [ list_jobservice_pool, list_jobservice_pool_worker, stop_jobservice_job, get_jobservice_job_log, list_jobservice_queue, stop_jobservice ]
resource_permissions["jobservice-monitor"] = jobservice_monitor
# jobservice monitor permissions end

# scanner permissions start
scanner_payload = {
    "name": "scanner-{}".format(random.randint(1000, 9999)),
    "url": "https://{}".format(random.randint(1000, 9999)),
    "description": None,
    "auth": "",
    "skip_certVerify": False,
    "use_internal_addr": False
}
list_scanner = Permission("{}/scanners".format(harbor_base_url), "GET", 200)
create_scanner = Permission("{}/scanners".format(harbor_base_url), "POST", 500, payload=scanner_payload)
ping_scanner = Permission("{}/scanners/ping".format(harbor_base_url), "POST", 500, payload=scanner_payload)
read_scanner = Permission("{}/scanners/{}".format(harbor_base_url, "88888888"), "GET", 404)
update_scanner = Permission("{}/scanners/{}".format(harbor_base_url, "88888888"), "PUT", 404, payload=scanner_payload)
delete_scanner = Permission("{}/scanners/{}".format(harbor_base_url, "88888888"), "DELETE", 404)
set_default_scanner = Permission("{}/scanners/{}".format(harbor_base_url, "88888888"), "PATCH", 404, payload={ "is_default": True })
get_scanner_metadata = Permission("{}/scanners/{}/metadata".format(harbor_base_url, "88888888"), "GET", 404)
scanner = [ list_scanner, create_scanner, ping_scanner, read_scanner, update_scanner, delete_scanner, set_default_scanner, get_scanner_metadata ]
resource_permissions["scanner"] = scanner
# scanner permissions end

# system label permissions start
label_payload = {
    "name": "label-{}".format(random.randint(1000, 9999)),
    "description": "",
    "color": "",
    "scope": "g",
    "project_id": 0
}
create_label = Permission("{}/labels".format(harbor_base_url), "POST", 201, label_payload, "id", id_from_header=True)
read_label = Permission("{}/labels/{}".format(harbor_base_url, ID_PLACEHOLDER), "GET", 200, payload=label_payload, payload_id_field="id")
update_label = Permission("{}/labels/{}".format(harbor_base_url, ID_PLACEHOLDER), "PUT", 200, payload=label_payload, payload_id_field="id")
delete_label = Permission("{}/labels/{}".format(harbor_base_url, ID_PLACEHOLDER), "DELETE", 200, payload=label_payload, payload_id_field="id")
label = [ create_label, read_label, update_label, delete_label ]
resource_permissions["label"] = label
# system label permissions end

# security hub permissions start
read_summary = Permission("{}/security/summary".format(harbor_base_url), "GET", 200)
list_vul = Permission("{}/security/vul".format(harbor_base_url), "GET", 200)
security_hub = [ read_summary, list_vul ]
resource_permissions["security-hub"] = security_hub
# security hub permissions end

# catalog permissions start
read_catalog = Permission("{}/v2/_catalog".format(endpoint_URL), "GET", 200)
catalog = [ read_catalog ]
resource_permissions["catalog"] = catalog
# catalog permissions end


def main():
    for permission in resource_permissions[resource]:
        print("=================================================")
        print("call: {} {}".format(permission.method, permission.url))
        print("payload: {}".format(json.dumps(permission.payload)))
        print("=================================================\n")
        permission.call()


if __name__ == "__main__":
    main()
