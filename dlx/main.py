from edgeTable import EdgeTable
from dlx import DLXOptimizer
from cellInfo import CellInfo

import time

# fcn and pci
fcn = 37900
pci = 15
#fcn = 38400
#pci = 9

# read file
start_ts = time.clock()
cellinfo = CellInfo("data/eRANO_CellInfo_data1.csv")
tab = EdgeTable("data/eRANO_IntTabInfo_data1.csv")

#cellinfo = CellInfo("data/neighbor_cell.txt")
#tab = EdgeTable("data/neighbor1.txt")

cell = cellinfo.get_fcn(fcn)
tab.construct_edge_matrix(cell)
minpci,minnodes = tab.get_pci_counts()
assert(pci >= minpci)
print("orignal indensity is {}".format(tab.calculate_total_density()))
init_ts = time.clock()
print("init cost {} seconds".format(init_ts - start_ts))

dlx = DLXOptimizer(tab,pci)
dlx.print_info()
dlx.print_matrix('dlx_matrix_fcn{}_pci{}.csv'.format(fcn,pci))
dlx.find_answers()

opt_ts = time.clock()
dlx.save_answers("output/cell_fcn{}".format(fcn))

print("opt cost {} seconds".format(opt_ts - init_ts))
