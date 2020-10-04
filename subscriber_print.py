import zmq

class Subscriber_Print:
    
    def __init__(self, topicfilters):
        self.port = "5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        for topic in topicfilters:
            self.socket.setsockopt(zmq.SUBSCRIBE, bytes([topic]))
        self.socket.connect ("tcp://localhost:%s" % self.port)
                

    def subscribe(self):
            while True:
                string = self.socket.recv()
                print (string)
        
        
sub = Subscriber_Print([128, 129])
sub.subscribe()
