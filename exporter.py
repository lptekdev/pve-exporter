from proxmoxer import ProxmoxAPI
import json
import yaml
from threading import Thread
from prometheus_client.twisted import MetricsResource
from twisted.web.server import Site
from twisted.internet import reactor
from klein import Klein
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, Gauge
from prometheus_client.registry import Collector




hostName = "0.0.0.0"
serverPort = 8080


nodes_array = []
vms_array = []
collected_metrics = False

class Node:
    def __init__(self, node, cluster, id, online, maxcpu, maxmem, uptime, used_cpu, used_mem, labels):
        self.node = node
        self.cluster = cluster
        self.id = id
        self.online = online
        self.maxcpu = maxcpu
        self.maxmem = maxmem
        self.uptime = uptime
        self.used_cpu = used_cpu
        self.used_mem = used_mem
        self.labels = labels

class VM:
    def __init__(self, name, id, status, memory, cpu, node, labels):
        self.name = name
        self.id = id
        self.status = status
        self.memory = memory
        self.cpu = cpu
        self.node = node
        self.labels = labels

class Prom_metric():
    def __init__(self, metric,name,class_property, object):
        self.metric = metric
        self.name = name
        self.class_property = class_property
        self.object = object


class Proxmox:
    proxmox = ""
    def __init__(self, proxmox_server, username, password):
        self.proxmox_server = proxmox_server
        self.username = username
        self.password = password

    def login(self):
        try:
            print("Logging in to proxmox server: ", self.proxmox_server)
            session = ProxmoxAPI(
                self.proxmox_server, user=self.username, password=self.password, verify_ssl=False
            )
            self.proxmox = session
            return self.proxmox
        
        except Exception as e:
            print("Unable to login")
            print(e)            
            return -1
        

    def GetClusterDetails(self):
        try:
            #print("Getting cluster resources")
            cluster = self.proxmox.cluster.status.get()
            cluster = json.dumps(cluster)
            cluster = json.loads(cluster)

            cluster = [item for item in cluster if item.get('type') == 'cluster']
            nodes = [item for item in cluster if item.get('type') == 'node']
            status = 1
            if (len(cluster)==0):
                status = 0
            return (status,cluster, nodes)

        except Exception as e:
            print("Error in GetClusterDetails: "+str(e))
            return (-1, None, None)
            
    
    def GetResources(self):
        try:
            resources = self.proxmox.cluster.resources.get()
            resources = json.dumps(resources)
            resources = json.loads(resources)
            #print(resources)
            nodes = [item for item in resources if item.get('type') == 'node']
            vms = [item for item in resources if item.get('type') == 'qemu']
            storage = [item for item in resources if item.get('type') == 'storage']
        
            return (nodes, vms, storage)
        
        except Exception as e:
            print("Error in GetResources: "+str(e))
            return (None, None, None)
    
    """
    def GetVMs(self, pve_node):
        global nodes_array
        print("Getting VMs of PVE Node: "+pve_node.name)
        #get the VMs hosted in pve node
        vms = self.proxmox.nodes(pve_node.name).qemu.get()
        #print(vms[0])
        vms_array =[]
        for vm in vms:
            vm_aux = VM(vm["name"],vm["vmid"],vm["status"],["cluster","node","vm"])
            vms_array.append(vm_aux)

        #searches for the node in global array list variable, and update it with the vms array
        index = nodes_array.index(pve_node)
        pve_node.vms =vms_array
        nodes_array[index] = pve_node
        

    def getVMDiskStats(self, vm, node):
        try:
            #json_string = str(proxmox.nodes.pve06.qemu(vm["vmid"]).status.current.get())
            json_string = str(self.proxmox.nodes(node.name).qemu(vm.id).status.current.get())
            data = json.dumps(json_string, indent=4)
            data = json.loads(data)            
            return
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return
    """



def LoadYAMLConfigFile( file):
    try:
        with open('config.yml', 'r') as file:
            config_file = yaml.safe_load(file)
            return(config_file['user'],config_file['password'],config_file['pve'])
        
    except FileNotFoundError:
        print("file not found")
    except FileExistsError:
        print("Bad configuration file")




def CollectMetrics():
    try:
        global collected_metrics
        global nodes_array
        ## read the config file which contains the servers we want query the metrics; with this is possible to create several exporter instances to query different servers to distribute the load
        print("Reading configuration file")
        config_file = LoadYAMLConfigFile("config.yaml")
        
        #define the login credentials, for the first pve on the config yaml file
        username = config_file[0]
        password = config_file[1]
        pve_to_login = config_file[2][0]
        #cluster = config_file[4]
        proxmox = Proxmox(pve_to_login,username,password)

        #login to the server
        session = proxmox.login()

        #if session is valid
        #print(session)
        if session != -1:
            
            #get the cluster details
            print("Get Cluster details if exists")
            cluster_details = proxmox.GetClusterDetails()
            print(cluster_details)
            
            #Get all registered resources
            print("Get Resources details")
            resources=proxmox.GetResources()
            print(resources[0])
            
            node_labels = ["cluster","node"]
            vm_labels = ["cluster","node", "vm"]
            storage_labels = ["cluster","node","storage"]

    
            cluster = None
            print(cluster_details[0])
            if (cluster_details[0] ==1):
                cluster = cluster_details[1][0]["name"]
            
            
            print("Creating NODE object and populating the array")
            for node in resources[0]:
                online = 0
                if(node["status"]=="online"):
                    online = 1
                nodes_array.append(Node(node["node"],cluster,node["id"],online,node["maxcpu"], node["maxmem"], node["uptime"],node["cpu"], node["mem"], node_labels))
                
    except Exception as e:
        print("Error in CollectMetrics: ",str(e))
        


if __name__ == "__main__":  
    # Start an HTTP server on port 8000

    
    metrics_array =[]
    metrics_array.append(Prom_metric(metric=Gauge("pve_node_total_cpu","Total number of CPUs of the PVE node",["cluster","node"]),name="pve_node_total_cpu",class_property="maxcpu",object="node"))
    metrics_array.append(Prom_metric(metric=Gauge("pve_node_status","Status of the PVE node",["cluster","node"]),name="pve_node_status",class_property="online",object="node"))
    metrics_array.append(Prom_metric(metric=Gauge("pve_node_used_memory","Total RAM memory used on PVE node",["cluster","node"]),name="pve_node_used_memory",class_property="used_mem",object="node"))
    metrics_array.append(Prom_metric(metric=Gauge("pve_node_used_cpu","Total CPU usage of the PVE node",["cluster","node"]),name="pve_node_used_cpu",class_property="used_cpu",object="node"))
        
    
    
    app = Klein()
    @app.route("/metrics")
    def metrics(request):
    
        print("COLLECTING METRICS")
        CollectMetrics()

        #clearing the metrics data
        for single_metric in metrics_array:
            single_metric.metric._metrics.clear()
            print("Clearing metrics")
            
    
        print("Get specific node metrics")
        node_metrics = [item for item in metrics_array if item.object == 'node']
        print("SIZE: ",len(node_metrics))
        for node in nodes_array:
            for node_metric in node_metrics:
                #if (node.cluster != None):
                    node_metric.metric.labels(node.cluster, node.id).set(getattr(node,node_metric.class_property))
                #else:
                    #node_metric.metric.remove('cluster','node')                     
                    #node_metric.metric.labels("cluster",node.id).set(getattr(node,node_metric.class_property))
                    

        return MetricsResource() 
        

    factory = Site(app.resource())
    reactor.listenTCP(8000, factory)
    reactor.run()
    
    """
    app = Klein()

    @app.route("/metrics")
    def CollectPVEMetrics(request):
        print(request.uri)
        
        ## read the config file which contains the servers we want query the metrics; with this is possible to create several exporter instances to query different servers to distribute the load
        print("Reading configuration file")
        config_file = LoadYAMLConfigFile("config.yaml")

        #define the login credentials, for the first pve on the config yaml file
        proxmox = Proxmox(config_file[2][0],config_file[0],config_file[1])

        #login to the server
        session = proxmox.login()
        nodes_array=[]

        #if session is valid
        if session != -1:
            #Get all registered resources
            resources = proxmox.GetResources()
            
            #Get the cluster nodes that match with the config file
            proxmox.getClusterNodes(config_file[2], config_file[3])

            resource_nodes = [item for item in resources if item.get('type') == 'node']
            
            print(resources)
            for node in nodes_array:
                print("SERVER: "+node.name)
                resource_vms =  [item for item in resources if (item.get('type') == 'qemu' and item.get("node")==node.name)]
                #getting the VMs on the pve nodes
                
                
        return MetricsResource()
    """

    
    
    """
    factory = Site(app.resource())
    reactor.listenTCP(8000, factory)
    reactor.run()
    """