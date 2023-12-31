## Prometheus exporter ##

### Instructions ###
Use the config_copy.yaml file to set the environment. \
Change the name of the **config_copy.yaml** file to **config.yaml** (system is still in developing and has hardcoded the name of the file to load the Proxmox configurations). \
Currently, system collects only the following metrics for the Proxmox nodes: 

- Total number of CPUs of the PVE node (number)
- Status of the PVE node (1 if online, 0 for offline)
- Total RAM memory used on PVE node (bytes)
- Total CPU usage of the PVE node (seconds)

\
Exporter can retrieve metrics from all nodes within the cluster, adding the necessary label value regarding this. \
When is only a single Proxmox node, the value for the label "cluster" is "", which means is required to remove it manually on the Prometheus job definition in relabel_config or (like also read in internet), labels without value are removed automatically by Prometheus. \
The Exporter is developed taking in consideration that:

- A cluster contains 1 or more PVE nodes
- A PVE node contains 0 or more VMs
- A PVE node contains 1 or more storage systems

Labels include this hierarchy for easy querying.
Updates will be provided.


## Building docker image ##
Use the provided Dockerfile in this repository. \
Run:  **docker build -t pve:latest .** 

You may use the docker-compose.yml file to create the container.


### Running and testing ###
**Locally** \
python exporter.py \
Open browser at localhost:8000/metrics to populate the metrics.

**Container** \
Open browser at docker_host_ip_address_ordns_name:8000/metrics to populate the metrics.


