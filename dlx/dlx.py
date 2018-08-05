import numpy as np
import copy
import pandas as pd

class Node(object):
    """
    Dlx link node
    """
    def __init__(self, left=None, right=None, 
                 up=None, down=None, 
                 col_header = None, row_header=None):
        self.left  = left  or self
        self.right = right or self
        self.up    = up    or self
        self.down  = down  or self

        self.col_header = col_header
        self.row_header = row_header

class DLXOptimizer(object):
    """
    Dlx Optimizer is to optimize following matrix

      Col  0    1    2    3   4    5    6    7     8    9   10  ...
                                 |<-                 MaxPci * EdgeCount                    ->|
   Row  |<-    NodeId          ->|<-  MaxPci  ->|<-  MaxPci  ->|...                          |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   0.   |  1 |    |    |    |    |  1 |    |    |    |    |    |... |    |    |    |    |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   1.   |    |  1 |    |    |    |  1 |    |    |  1 |    |    |... |    |    |    |    |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   2.   |    |  1 |    |    |    |    |  1 |    |    | 1  |    |... |    |    |    |    |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   3.   |    |  1 |    |    |    |    |    |  1 |    |    | 1  |... |    |    |    |    |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   4.   |    |    |  1 |    |    |    |    |    |  1 |    |    |... |    |    |  1 |    |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   5.   |    |    |  1 |    |    |    |    |    |    | 1  |    |... |    |    |    |  1 |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   6.   |    |    |  1 |    |    |    |    |    |    |    | 1  |... |    |    |    |    |  1 |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
   7.   |    |    |    |  1 |    |    |    |    |    |    |    |... |    |    |    |    |    |
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
        column_number             = nodecount + maxpci * edgecount
        row_number                = no_opt_nodecount + opt_nodecount * maxpci
        exact_cover_column_number = nodecount 

    assume MaxPci = 3, EdgeCount = 10, NodeId = 4
    Row0: node0, pci 1, has edge 1     node0 is no opt node. i.e. only could only use pci=1
    Row1: node1, pci 1, has edge 1, 2
    Row2: node1, pci 2, has edge 1, 2
    Row3: node1, pci 3, has edge 1, 2
    ...
    Row6: node2, pci 3, has edge 2,10

    Col10: indicates conflict between node 1 and node2 when both node choose pci 3

    The optimizer is to find all possible combination of rows to make column 1 to column NodeId
    is covered all covered and only covered by one row.

    """
    def __init__(self, edgeTab, maxpci):
        # basic info
        self.edgeTab          = edgeTab        
        self.maxpci           = maxpci 
        self.nodecount        = edgeTab.get_node_count()
        self.edgecount        = edgeTab.get_edge_count()
        self.opt_nodecount    = edgeTab.get_opt_node_count()
        self.opt_nodes        = edgeTab.node_need_opt_ids
        self.no_opt_nodecount = self.nodecount - self.opt_nodecount 
        self.no_opt_nodes     = edgeTab.node_dont_opt_ids

        # dlx matrix parameters
        self.num_columns      = self.nodecount + self.maxpci * self.edgecount
        self.num_rows         = self.no_opt_nodecount + self.opt_nodecount * self.maxpci
        self.col_headers      = []
        self.col_size         = [0] * self.num_columns

        # answer info
        self.answer           = [-1] * self.nodecount
        self.solutions        = []      # [(indensity, [[nodeid,pci],...])]
        self.num_solution     = 10      # keep 10 best solutions
        self.max_iter_no_new  = 5000    # if no better solution after 100000 iteration, stop 
        self.curr_iter        = 0

        # construct dlx matrix
        self.construct_matrix()

    def construct_matrix(self):        
        self.root = Node()

        # construct column headers
        for i in range(self.num_columns):
            # append new column header to the tail of double link
            new_col_header = Node(left=self.root.left, right=self.root)
            self.root.left.right = new_col_header
            self.root.left       = new_col_header

            new_col_header.col_header = i
            new_col_header.row_header = -1
            self.col_headers.append(new_col_header)

        # insert each node into matrix, no opt ids must be insert first
        for i,(nodeid, pci) in enumerate(self.edgeTab.node_dont_opt_ids):
            self.add_rows(i, self.edgeTab.get_all_edge_ids(nodeid),pci,opt=False)
        for i,(nodeid, pci) in enumerate(self.edgeTab.node_need_opt_ids):
            self.add_rows(i + self.no_opt_nodecount, self.edgeTab.get_all_edge_ids(nodeid),pci)

    def add_rows(self, node_col_id, edgeids, origpci, opt=True):
        """
        Add rows to the matrix        
        """
        if opt:
            for pci in range(self.maxpci):
                self.add_row(node_col_id, pci, edgeids)
        else:
            self.add_row(node_col_id, origpci % self.maxpci, edgeids)

    def add_row(self, node_col_id, pci, edgeids):
        assert(pci<=self.maxpci)
        # insert first node
        col_header_node = self.col_headers[node_col_id]
        if node_col_id < self.no_opt_nodecount:
            row_id = node_col_id
        else:
            row_id = self.no_opt_nodecount + (node_col_id - self.no_opt_nodecount) * self.maxpci + pci
        
        row_first_node = Node(up         = col_header_node.up,
                              down       = col_header_node.up.down,
                              row_header = row_id,
                              col_header = node_col_id
                              )
        col_header_node.up.down = row_first_node
        col_header_node.up      = row_first_node

        self.col_size[node_col_id] += 1

        # insert rest node in row
        for edgeid in edgeids:            
            col_id = self.nodecount + edgeid * self.maxpci + pci
            col_header_node = self.col_headers[col_id]
            new_node = Node(left       = row_first_node.left,
                            right      = row_first_node,
                            up         = col_header_node.up,
                            down       = col_header_node.up.down,
                            row_header = row_id,
                            col_header = col_id
                            )            
            col_header_node.up.down   = new_node
            col_header_node.up        = new_node
            row_first_node.left.right = new_node
            row_first_node.left       = new_node

            self.col_size[col_id] += 1

    def find_answers(self):
        self.dlx_search(level = 0)

        if len(self.solutions) == 0:
            print("No answer found")
        else:            
            self.print_solutions(detailed=True)
                 
    def dlx_search(self, level):
        # find all possible combination of row indices to make
        # the first self.nodecount columns to be covered.
    
        # no better answer found for max iteration, return True
        # and popup current solutions
        if self.curr_iter == self.max_iter_no_new:
            return True

        # check if we already found result
        if level == self.nodecount:
            # We must already found result, record the answer
            self.curr_iter += 1
            tot_indensity, answer_list = self.answer_to_solution(self.answer)
            if self.solutions == []:
                self.solutions.append((tot_indensity,answer_list))
                self.curr_iter = 0
            elif tot_indensity < self.solutions[-1][0]:
                self.solutions.insert(0,(tot_indensity,answer_list))
                self.solutions.sort()
                self.solutions = self.solutions[:self.num_solution]
                # better answer has been found
                self.curr_iter = 0
            if self.curr_iter == self.max_iter_no_new:
                print("not better solution found after {} iteration".format(self.max_iter_no_new))
            return True                
        node_start = self.root.right
        if node_start.col_header > self.nodecount: 
            # possible? The column is removed by mistake?                        
            return False
        elif self.col_size[node_start.col_header] == 0:
            # no candicates left in column
            return False
        
        # start withs the column with least number of items
        node_remove = node_start
        min_size    = self.col_size[node_start.col_header]        
        while node_start.col_header < self.nodecount - level:                    
            if self.col_size[node_start.col_header] == 0:
                # the column has no solution
                return False
            if self.col_size[node_start.col_header] < min_size:
                min_size    = self.col_size[node_start.col_header]
                node_remove = node_start
            node_start = node_start.right       

        # remove nodes of chosen columns from matrix
        # the rows which contains any chosen nodes are also removed from matrix
        self.remove(node_remove)

        # try find answers
        node_down = node_remove.down
        while node_down != node_remove:
            # record current choice of row id
            self.answer[level] = node_down.row_header
            
            # remove nodes which conflict with current chosen node
            node_right = node_down.right
            while node_right != node_down:
                self.remove(self.col_headers[node_right.col_header])
                node_right = node_right.right

            # continue next level            
            if self.dlx_search(level + 1):
                self.answer[level] = -1                             

            # recover removed nodes
            node_left = node_down.left
            while node_left != node_down:
                self.recover(self.col_headers[node_left.col_header])
                node_left = node_left.left

            node_down = node_down.down

        # previous recover failed, restore original
        self.recover(node_remove)
            
    def remove(self, column_header):
        # remove column
        column_header.left.right = column_header.right
        column_header.right.left = column_header.left

        node_down = column_header.down

        # move downwards vertically node by node, 
        while node_down != column_header:
            node_right = node_down.right

            # remove this row vertically
            while node_right != node_down:
                node_right.down.up = node_right.up
                node_right.up.down = node_right.down

                # decreament the corresponding column size counter
                self.col_size[node_right.col_header] -= 1
                # move to next node at the right side
                node_right = node_right.right

            # move to next node at the down side
            node_down = node_down.down

    def recover(self, column_header):
        # restore this column
        column_header.right.left = column_header
        column_header.left.right = column_header

        node_up = column_header.up

        # move upwards vertically node by node
        while node_up != column_header:
            node_left = node_up.left

            while node_left != node_up:
                # restore this row vertically
                node_left.down.up = node_left
                node_left.up.down = node_left

                # increament the corresponding column size counter
                self.col_size[node_left.col_header] += 1
                # move on the the left node
                node_left = node_left.left

            # move on to the up node
            node_up = node_up.up

    def print_solutions(self, detailed=False):
        if detailed:            
            if len(self.solutions) > 5:
                print("too much solutions, only 5 best will be showed")
            for i, (indensity, cellinfo) in enumerate(self.solutions[:5]):                
                print("=========== solution {0:3d} indensity {1:10f} ===========".format(i,indensity))
                for [node_id, pci] in cellinfo:
                    node_name = self.edgeTab.get_node_name(node_id)
                    print("{0:20s}:{1:5d}".format(node_name,pci))                            
        else:
            print("{} possible solutions".format(len(self.answers)))

    def answer_to_solution(self, answer):
        answer_list = []
        for row_id in answer:
            node_id,pci = self.row_to_nodeid_pci(row_id)
            node_name = self.edgeTab.get_node_name(node_id)
            pci = pci % self.maxpci
            answer_list.append([node_id,pci])
        return self.edgeTab.calculate_total_density(cellinfo=answer_list), answer_list

    def row_to_nodeid_pci(self, row_id):       
        if row_id < self.no_opt_nodecount:
            (nodeid, pci) = self.no_opt_nodes[row_id]
        else:
            row_id -= self.no_opt_nodecount
            opt_node_id = row_id // self.maxpci
            (nodeid, _) = self.opt_nodes[opt_node_id]
            pci         = row_id % self.maxpci
        return nodeid,pci

    def print_matrix(self, file=None):
        printable_mat = np.zeros((self.num_rows,self.num_columns))
        for col_header in self.col_headers:
            self.__fillmatrix(printable_mat, col_header)        
        if file is None:
            np.set_printoptions(threshold=np.inf)
            print(printable_mat)
        else:
            np.savetxt(file,printable_mat,fmt="%s",delimiter=',')

    def save_answers(self,baseFileName):
        for i, (indensity, cellinfo) in enumerate(self.solutions):
            fileName = baseFileName + 'sol{}_ind{}.csv'.format(i, int(indensity*10000))
            newcellinfo = [[self.edgeTab.get_node_name(node_id), pci % 3] for [node_id, pci] in cellinfo]
            df = pd.DataFrame(newcellinfo)
            df.columns= ['CellId','PSS']
            df.to_csv(fileName,index=None)       
        
    def print_info(self):
        print("maxpci: ",self.maxpci)
        print("nodecount: ",self.nodecount)        
        print("edgecount: ",self.edgecount) 
        print("num_columns: ",self.num_columns)
        print("num_rows: ",self.num_rows)
        
    def __fillmatrix(self, matrix, col_header):
        node = col_header.down
        while(node != col_header):
            matrix[node.row_header][node.col_header] = 1
            node = node.down
