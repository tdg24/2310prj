import grpc
import time
import sys
import datetime

from concurrent import futures

import chat_pb2_grpc
import chat_pb2

import psycopg2

# dbHost = 'localhost'
# database = '2310prj'
# username = 'postgres'
# pwd = 'admin'
# dbPort = 5432

# dbConn = psycopg2.connect(
#         host = dbHost,
#         dbname = database,
#         user = username,
#         password = pwd,
#         port = dbPort
#     )

class ChatServer(chat_pb2_grpc.ChatServerServicer):
    def __init__(self):
        self.chats = []
        self.nameList = []
        self.interests = {}
        #self.parentsNoMatchYet = []
        #self.seniors = []
        self.requests = dict()
        self.events = []
        self.scheduled = []
        self.adminViewRequests = []

    def OpenRequests(self, requestor, context):
        for day in self.requests:
            for each in self.requests[day]:
                if each.name == requestor.name:
                    yield each


    def ChatStream(self, request_iterator, context):
        userLen = 0
        if request_iterator.name in self.interests:
            userLen = len(self.interests[request_iterator.name])
        eventInd = request_iterator.value
        schedInd = request_iterator.value
        adminReqInd = request_iterator.value
        while True:
            # Check if there are any new messages
            while len(self.events) > eventInd:
                event = self.events[eventInd]
                eventInd += 1
                #include logic for if message is x from me terminate thread
                yield event
            
            while len(self.scheduled) > schedInd:
                match = self.scheduled[schedInd]
                schedInd += 1
                #include logic for if message is x from me terminate thread
                yield match


            #if len(self.interests[request_iterator.name]) > userLen:
            #    userLen = len(self.interests[request_iterator.name])
            #    eventInd = 0
    
    def EventCheck(self, request_iterator, context):
        eventInd = 0
        arrAct = request_iterator.name.split(',')
        msgSet = set(arrAct)
        while len(self.events) > eventInd:
            event = self.events[eventInd]
            eventInd += 1
            eventAct = event.activities.split(',')
            eventSet = set(eventAct)
            if eventSet & msgSet:
                yield event
        
        return
    
    def SendMssg(self, request: chat_pb2.Mssg, context):
        print("SERVER SIDE [{}] {} - {} - {} - {}".format(request.name, 
                request.userType, request.date, request.timeSlots, request.activities ))
        if request.userType == 'event':
            self.events.append(request)
        else:
            #if match add to self.scheduled else add to self.requests

            if request.date in self.requests:
                # print('\n\ndate match\n\n')
                #flag = 0
                #turn request time & duration into set of times
                requestTimeSet = set(request.timeSlots.split(','))
                requestActSet = set(request.activities.split(','))
                
                i = 0
                length = len(self.requests[request.date])
                #for i in range(len(self.requests[request.date])):
                while i < length:

                    deleteFlag = 0

                    each = self.requests[request.date][i]

                    if len(requestTimeSet) <= 0:
                            break

                    if each.userType != request.userType:
                        eachTimeSet = set(each.timeSlots.split(','))
                        eachActSet = set(each.activities.split(','))

                        if len(requestTimeSet.intersection(eachTimeSet)) > 0 and len(requestActSet.intersection(eachActSet)) > 0:
                            match = chat_pb2.Mssg()
                            match.name = request.name
                            match.other = each.name
                            match.date = request.date

                            print('\n\n{} \nr {} \n ss {}\n'.format(request.name, requestTimeSet, eachTimeSet))

                            match.activities = ','.join(requestActSet.intersection(eachActSet))
                            match.timeSlots = ','.join(requestTimeSet.intersection(eachTimeSet))

                            #rTempAct = requestActSet
                            rTempTime = requestTimeSet
                            #requestActSet = requestActSet - eachActSet
                            requestTimeSet = requestTimeSet - eachTimeSet
                            #eachActSet = eachActSet - rTempAct
                            eachTimeSet = eachTimeSet - rTempTime

                            #each.activities = ','.join(eachActSet)
                            each.timeSlots = ','.join(eachTimeSet)

                            #check empty
                            if len(eachTimeSet) <= 0:
                                #remove old request
                                self.requests[request.date].pop(i)
                                length = len(self.requests[request.date])
                                deleteFlag = 1
                                
                            else:
                                #put back with updated info
                                self.requests[request.date][i] = each

                            match.eventType = 'scheduled'
                            self.scheduled.append(match)
                            
                    if deleteFlag == 0:
                        i += 1
            
                if len(requestTimeSet) > 0:
                    #request.activities = ','.join(requestActSet)
                    request.timeSlots = ','.join(requestTimeSet)
                    self.requests[request.date].append(request)
        
            else:
                self.requests[request.date] = []
                self.requests[request.date].append(request)

            if request.name in self.interests:
                setActivities = set(request.activities.split(','))
                self.interests[request.name] = self.interests[request.name].union(setActivities)

        print('list of active requests {}'.format(self.requests))

        received = chat_pb2.Response()
        received.message = 'Scheduler is processing request'
        #self.chats.append(request)
        return received

    def RequestAccess(self, request: chat_pb2.Mssg , context):
        print(request.name)
        if request.name not in self.interests:
            #self.nameList.append(request.name)
            self.interests[request.name] = set()
            request.message = "yes"
            return request
        elif request.name in self.interests:
            request.message = "yes"
            #print(self.interests[request.name])
            request.activities = ','.join(self.interests[request.name])
            return request

def printUsage():
    print("Usage: python3 server.py -port <port>")
    sys.exit()

def usage ( arglist ):
    if len(arglist) != 3:
        print("not correct args {}".format(len(arglist)))
        print(arglist)
        printUsage()
    
    if(arglist[1] != '-port'):
        print(arglist[1])
        print(arglist[3])
        printUsage()

if __name__ == '__main__':

    usage( sys.argv )

    port = int(sys.argv[2])  
    #names = sys.argv[2].split(',')
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  
    chat_pb2_grpc.add_ChatServerServicer_to_server(ChatServer(), server) 

    print('Starting server. Listening on port ... ' + str(port))
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    
    try:
        while True:
            time.sleep(64 * 64 * 100)
    except KeyboardInterrupt:
        server.stop(1)
        dbConn.close()
        sys.exit()
