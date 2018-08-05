import pandas as pd

class CellInfo(object):
     def __init__(self, fileName, delimiter=','):
         self.fcn_data = {}
         self.raw_info = self.__parse_cell_info(fileName)
   
     def get_fcn(self, fcn):
         return self.fcn_data.get(fcn)
    
     def __parse_cell_info(self, fileName):
         df = pd.read_csv(fileName)

         # strip column name         
         df.columns   = [column.strip() for column in df.columns]

         # seperate data by fcn
         for fcn in set(df['EARFCN']):
             self.fcn_data[fcn] = df[df['EARFCN'] == fcn]

         return df