import zmq
import mysql.connector # pip install mysql-connector-python
import struct
from time import sleep

class Subscriber_Database:
    
    def __init__(self, topicfilters):
        self.port = "5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        for topic in topicfilters:
            self.socket.setsockopt(zmq.SUBSCRIBE, bytes([topic]))
        self.socket.connect ("tcp://localhost:%s" % self.port)
        
        self.db = mysql.connector.connect(      
            host="localhost",
            user="benusr",
            password="testpw_Y^GgmjDlH~C1TYPn&LH",
            database="tinyIPFIX_database"
        )
        
        self.cursor = self.db.cursor()
        
    def subscribe(self):
            while True:
                string = self.socket.recv()
                
                values = []
                source_of_value = string[1:3]
                source_of_value = struct.unpack('>H', source_of_value)[0]
                values.append(source_of_value)
                temperature = string[3:7]
                temperature = struct.unpack('>f', temperature)[0]
                values.append(temperature)
                datetime = string[7:26]
                datetime = datetime.decode('utf-8')
                values.append(datetime)
                
                column_names = ["source_of_value", "temperature", "datetime"]
                
                self.insert_into_db(column_names, values)
                print("saved {} in the database".format(string))
                  
    def insert_into_db(self, column_names, values):  
        sql = "INSERT INTO data_128 ("
        for column_name in column_names:
            sql += column_name
            sql += ", "
        sql = sql[:-2]
        sql += ") VALUES ("
        for val in values:
            sql += "%s"
            sql += ", "
        sql = sql[:-2]
        sql += ")"
        self.cursor.execute(sql, values)
        
        self.db.commit()
        
          
               
sub = Subscriber_Database([128, 129])	
sub.subscribe()

