## Prometheus exporter ##

Use the config_copy.yaml file to set the environment \
Change the name of the config file to config.yaml (system is still in developing and has hardcoded the name of the file to load the Proxmox configurations) \
Currently, system collects on the following metrics for the Proxmox nodes: \

- Total number of CPUs of the PVE node
- Status of the PVE node
- Total RAM memory used on PVE node
- Total CPU usage of the PVE node

\
Exporter can retrieve metrics from all nodes within the cluster, adding the necessary label value regarding this. \
When is only a single Proxmox node, the value for the label "cluster" is "", which means is required to remove it manually on the Prometheus job definition in relabel_config or (like also read in internet), labels without value are removed automatically by Prometheus. \
The Exporter is developed taking in consideration that:

- A cluster contains 1 or more PVE nodes
- A PVE node contains 0 or more VMs
- A PVE node contains 1 or more storage systems

Labels include this hierarchy for easy querying.
Updates will be provided. \



### Running and testing ###
python exporter.py

Open browser at localhost:8000/metrics to populate the metrics




