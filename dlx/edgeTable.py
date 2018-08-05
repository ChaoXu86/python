from scipy import sparse
import numpy as np
import pandas

class EdgeTable(object):
    """Edge info table
    One sparse matrix is generated from csv format file, it is 
    allowed the value[i,j] doesn't equal value[j,i]
        
    [0 1 0 0 0 0
     1 0 1 1 0 0
     0 1 0 1 1 0
     0 1 1 0 0 1
     0 0 1 0 0 0
     0 0 0 1 0 0]

    """
    def __init__(self, fileName):   
        self.fileName = fileName           
        
    def get_node_id(self, nodeName, create_new = False):
        """
        For given node name, return the internal unique node id.
        If the node name is not found, the function will generate
        one new node id
        """
        node_id = self.node_name_id_dict.get(nodeName)
        is_new  = False
        if node_id is None and create_new == True:
            # node_id not exists and should create new
            node_id = self.node_count
            self.node_id_name_list.append(nodeName)
            self.node_name_id_dict[nodeName] = node_id
            self.node_count += 1
            is_new = True

        return node_id, is_new

    def get_node_count(self):
        return self.node_count

    def get_opt_node_count(self):
        return len(self.node_need_opt_ids)

    def get_node_name(self, nodeId):
        """
        For given node id, return the node name
        """
        return self.node_id_name_list[nodeId]
    
    def get_edge_id(self, nodeId1, nodeId2):
        """
        For given node id1 and id2, return edge id 
        """
        edge = [nodeId1, nodeId2]
        edge.sort()
        edge = tuple(edge)
        if edge in self.edge_id_list:
            return self.edge_id_list.index(edge)
        else:
            return -1

    def get_edge_count(self):
        return self.edge_count

    def get_all_edge_ids(self, nodeId):  
        """
        For given node Id, return all its edge Ids
        """ 
        edge_ids = []
        for edgeid, (nodeid1,nodeid2) in enumerate(self.edge_id_list):
            if nodeId == nodeid1 or nodeId == nodeid2:
                edge_ids.append(edgeid)
        return edge_ids
            #neighbor_node_ids = np.argwhere(self.edge_table[nodeId].toarray().flatten())         
        #return [self.get_edge_id(nodeId,neighbor_node_id) for neighbor_node_id in neighbor_node_ids.flatten()]

    def is_neighbor(self, nodeId1, nodeId2):
        return not self.edge_table[nodeId1, nodeId2] == 0.

    def get_value(self, nodeId1, nodeId2):
        return self.edge_table[nodeId1, nodeId2]

    def print_edge_table(self):
        print(self.edge_table.toarray())

    def print_edge_info(self):
        print(self.edge_id_list)

    def construct_edge_matrix(self, cellInfo):        
        """ parse table info file, should be csv format

        table info file might looks like
        node_name, neighbor_node_name, density
        enb1     , enb2,               0.134
        enb1     , enb3,               0.1145
        enb2     , enb2,               0.091
        ...

        After parsing the file, each node name will be assigned
        one unique node id
        """         
        self.node_id_name_list = []
        self.node_need_opt_ids = [] # [(id1, pci1), (id3, pci3) ...] 
        self.node_dont_opt_ids = [] # [(id2, pci2), (id4, pic4) ...]
        self.node_name_id_dict = {}
        self.node_count        = 0
        self.edge_id_list      = [] # sorted tuple list, [(1,2),(1,3), ...]
        self.edge_count        = 0
        self.edge_table        = None
        self.cellinfo          = cellInfo

        df                 = pandas.read_csv(self.fileName)      
        validcells         = cellInfo["CellId"].values
        lines              = df.values
        sparse_matrix_row  = []
        sparse_matrix_col  = []
        sparse_matrix_data = []
        for line in lines:
            [central_node_name, neighbor_node_name, indenisity] = line
            # central and neighbor node should be both in valid cells or neither
            if central_node_name in validcells:
                assert(neighbor_node_name in validcells)
            else:
                assert(neighbor_node_name not in validcells)
                continue
            
            # from here, central_node and neighbor_node should has
            central_node_id, is_new = self.get_node_id(central_node_name, True)
            if is_new:
                self.__update_node_opt_id_list(central_node_id, central_node_name)
            neighbor_node_id, is_new = self.get_node_id(neighbor_node_name, True)
            if is_new:
                self.__update_node_opt_id_list(neighbor_node_id, neighbor_node_name)

            edge = [central_node_id,neighbor_node_id]
            edge.sort()
            self.edge_id_list.append(tuple(edge))
            sparse_matrix_row.append(central_node_id)
            sparse_matrix_col.append(neighbor_node_id)
            sparse_matrix_data.append(float(indenisity))

        self.edge_id_list = list(set(self.edge_id_list))
        self.edge_id_list.sort()
        self.edge_count = len(self.edge_id_list)

        assert(self.node_count == len(self.node_dont_opt_ids) + len(self.node_need_opt_ids))
        
        matrix=sparse.coo_matrix((sparse_matrix_data,(sparse_matrix_row,sparse_matrix_col)), shape=(self.node_count, self.node_count))
        self.edge_table = matrix.tocsr()
        
    def __update_node_opt_id_list(self, node_id, node_name):
        _,_,pci,_,pflag = self.cellinfo[self.cellinfo['CellId'] == node_name].values[0]
        if pflag == 1:
            self.node_need_opt_ids.append((node_id,pci))
        else:
            self.node_dont_opt_ids.append((node_id,pci))
    
    def calculate_total_density(self,cellinfo=None,debug=False):
        if cellinfo is None:
            cellinfo = self.cellinfo[['CellId','PCI']].values

        total_density = 0
        tmp_cell_info = []
        for [node_name, pci] in cellinfo:
            if type(node_name) == str:
                node_id, _ = self.get_node_id(node_name)
                if node_id is None:
                    continue
            else:
                node_id = node_name
            tmp_cell_info.append([node_id,pci])
        tmp_cell_info.sort()

        for (nodeid1,nodeid2) in self.edge_id_list:
            [id1, pci1] = tmp_cell_info[nodeid1]
            assert(id1 == nodeid1)
            [id2, pci2] = tmp_cell_info[nodeid2]
            assert(id2 == nodeid2)
            if (pci1 % 3) == (pci2 % 3):
                if debug:
                    print("nodeid(name)={}({}),pci={} conflicts nodeid(name)={}({}),pci={}".format(nodeid1,self.get_node_name(nodeid1),pci1,
                                                                          nodeid2,self.get_node_name(nodeid2),pci2)) 
                total_density += self.get_value(id1,id2)

        return total_density

    def get_pci_counts(self):
        # if one node's neighbor's neighbor contains itself,
        # it means these three nodes connected to each other.
        # In this case, at least we need 3 different pci to 
        # make sure they didn't impact each other. This function
        # is to find the least different pci we needed for the 
        # whole network
        neighbor_info = []
        for i in range(self.node_count):
            neighbor_info.append(set())
        
        for (nodeid1,nodeid2) in self.edge_id_list:
            neighbor_info[nodeid1].add(nodeid2)
            neighbor_info[nodeid2].add(nodeid1)
        
        min_pci_counts = 1
        min_pci_nodes = []
        for nodeid in range(self.node_count):
            pci_counts = 1
            pci_nodes  = [nodeid]
            for neighbor_id in neighbor_info[nodeid]:
                for neighbor_neighbor_id in neighbor_info[neighbor_id]:
                    if nodeid in neighbor_info[neighbor_neighbor_id]:
                        pci_counts += 1
                        pci_nodes.append(neighbor_id)
                        break
            if pci_counts > min_pci_counts:
                min_pci_counts = pci_counts
                min_pci_nodes = pci_nodes

        return min_pci_counts,min_pci_nodes
