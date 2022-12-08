from flask import Flask, render_template, send_file, request, flash, redirect, url_for
import threading
import sys
import datetime
import time
import grpc
import chat_pb2_grpc
import chat_pb2




class webClient:
    def __init__(self, ipadd : str, port : int):
        self.port = port
        self.serverPort = 20
        self.utype = dict()
        self.conn = dict()
        self.listener = dict()
        self.interests = dict()
        self.messages = dict()
        self.sent = dict()

        #app attributes
        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.login , methods=["POST", "GET"])
        self.app.add_url_rule('/account/<utype>/<uname>', view_func=self.account , methods=["POST", "GET"])
    
    def startClient(self, uname: str, utype: str, ipadd : str, port : int):
        channel = grpc.insecure_channel(ipadd + ':' + str(port))
        self.conn[uname] = chat_pb2_grpc.ChatServerStub(channel)
        self.utype[uname] = utype
        #print('startclient error {}'.format(self.interests[uname]))
        self.interests[uname] = set()
        self.messages[uname] = {}

        self.listener[uname] = threading.Thread(target=self.listenMssg, args=(uname, utype,), daemon=True)
        
        rqst = chat_pb2.Mssg()  
        rqst.name = uname 
        rqst.message = 'requesting access'

        response = self.conn[uname].RequestAccess(rqst)
        if len(response.activities) > 0:
            setActivities = set(response.activities.split(','))
            self.interests[uname] = self.interests[uname].union(setActivities)
            #print('start client if response.activities {}'.format(self.interests[uname]))

        if response.message == 'no':
            print('you were rejected from group')
            self.username = 'go away'
        elif response.message == 'yes':
            print('{} joined'.format(uname))
            self.listener[uname].start()

    def createEvent(self, title, eventtype, date, timeslots, activities):
        arr = [int(n) for n in timeslots.split(',')]
        arr.sort()
        print('{} {}'.format(title, arr))
        d = {}
        # if eventtype == 'request':
        #     for i in range(len(arr)):
        #         s = int(arr[i])
        #         e = s+100
        #         s = str(s)
        #         e = str(e)

        #         if len(s) == 3:
        #             s = 'T0{}:00:00'.format(s[0])
        #         else:
        #             s = 'T{}:00:00'.format(s[0:2])
                
        #         if len(e) == 3:
        #             e = 'T0{}:00:00'.format(e[0])
        #         else:
        #             e = 'T{}:00:00'.format(e[0:2])
        #         start = '{}{}'.format(date,s)
        #         end = '{}{}'.format(date,e)
        #         event = {
        #             'title' : title,
        #             'eventtype' : eventtype,
        #             'start' : start,
        #             'end'   : end,
        #             'description' : activities
        #         }
        #         d[start] = event
        if eventtype == 'scheduled' or eventtype == 'request':
            i = 0
            while i < len(arr):
                s = int(arr[i])

                i += 1
                nxt = s+100
                while i < len(arr) and int(arr[i]) == nxt:
                    i += 1
                    nxt += 100

                e = int(nxt)
                s = str(s)
                e = str(e)

                if len(s) == 3:
                    s = 'T0{}:00:00'.format(s[0])
                else:
                    s = 'T{}:00:00'.format(s[0:2])
                
                if len(e) == 3:
                    e = 'T0{}:00:00'.format(e[0])
                else:
                    e = 'T{}:00:00'.format(e[0:2])
                start = '{}{}'.format(date,s)
                end = '{}{}'.format(date,e)
                event = {
                    'title' : title,
                    'eventtype' : eventtype,
                    'start' : start,
                    'end'   : end,
                    'description' : activities
                }
                d['{} {}'.format(title,start)] = event
                print(event)
        
        else:
            s = int(arr[0])
            e = int(arr[-1])+100
            s = str(s)
            e = str(e)

            if len(s) == 3:
                s = 'T0{}:00:00'.format(s[0])
            else:
                s = 'T{}:00:00'.format(s[0:2])
            
            if len(e) == 3:
                e = 'T0{}:00:00'.format(e[0])
            else:
                e = 'T{}:00:00'.format(e[0:2])
            start = '{}{}'.format(date,s)
            end = '{}{}'.format(date,e)
            event = {
                'title' : title,
                'eventtype' : eventtype,
                'start' : start,
                'end'   : end,
                'description' : activities
            }
            d[start] = event

        return d


    def listenMssg(self, uname, utype):
        starter = chat_pb2.Number()
        starter.value = 0
        starter.name = uname
        for msg in self.conn[uname].ChatStream(starter): 
            arrAct = msg.activities.split(',')
            msgSet = set(arrAct)
            #print("cheat {} - {} - {} - {} - {} - {}".format(uname, msg.name , msg.date , msg.timeSlots , msg.activities , msg.other))  

            if msg.name == uname and utype != 'event' and msg.eventType == 'scheduled':
                str1 = "scheduled1 {} - {} - {} - {} - {}".format(uname, msg.date , msg.timeSlots , msg.activities , msg.other)  
                title = '{} - {}'.format(uname, msg.other)
                print(str1)
                self.messages[uname].update(self.createEvent(title, msg.eventType, msg.date, msg.timeSlots, msg.activities))
            elif msg.other == uname and utype != 'event' and msg.eventType == 'scheduled':
                str1 = "scheduled2 {} - {} - {} - {} - {}".format(uname, msg.date , msg.timeSlots , msg.activities , msg.name)
                print(str1)  
                title = '{} - {}'.format(uname, msg.name)
                self.messages[uname].update(self.createEvent(title, msg.eventType, msg.date, msg.timeSlots, msg.activities))
            elif utype != 'event' and msg.userType == 'event' and msg.name != uname and msgSet.intersection(self.interests[uname]):
                str1 = "event1 {} - {} - {} - {} - {}".format(uname, msg.name, msg.date , msg.timeSlots , msg.activities)
                print(str1) 
                self.messages[uname].update(self.createEvent(msg.name, msg.userType, msg.date, msg.timeSlots, msg.activities)) 
            elif utype == 'event' and msg.userType == 'event':
                str1 = "event2 {} - {} - {} - {}".format(msg.name, msg.date , msg.timeSlots , msg.activities)
                print(str1)     
                self.messages[uname].update(self.createEvent(msg.name, msg.userType, msg.date, msg.timeSlots, msg.activities)) 
            elif utype == 'event' and msg.userType != 'event': #event admin view of scheduled
                str1 = "Sched {} - {} - {} - {}".format(msg.name, msg.date , msg.timeSlots , msg.activities)
                print(str1) 
                title = '{} - {}'.format(msg.name, msg.other) 
                self.messages[uname].update(self.createEvent(title, 'scheduled', msg.date, msg.timeSlots, msg.activities)) 
                #self.messages[uname].add(str1)  

    def sendToServer(self, msg, uname, utype):
        #message = msg
        if msg != '':
            n = chat_pb2.Mssg()  
            n.name = uname  
            arr = msg.split()
            #n.message = message 
            n.userType = utype
            n.eventType = arr[0]
            n.date = arr[1]

            n.timeSlots = arr[2]
            
            # intTime = int(arr[2])
            # if int(arr[3]) > 0:
            #     for i in range(int(arr[3])-1):
            #         intTime = (intTime + 100) %2400
            #         n.timeSlots += ',' + str(intTime)
            # print('n.timeslots {}'.format(n.timeSlots))
            n.activities = arr[3]

            #add sent activities to self.interests
            #doesnt currently notify of existing events matching new request activities until re-instantiated session
            setActivities = set(n.activities.split(','))
            
            #print('send set activities {}'.format(setActivities))
            newActivities = setActivities - self.interests[uname]
            #print('send new activities {}'.format(newActivities))
            if len(newActivities) > 0:
                acts = ','.join(s for s in newActivities)
                check = chat_pb2.Number()
                check.value = 0
                check.name = acts
                for msg in self.conn[uname].EventCheck(check):
                    arrAct = msg.activities.split(',')
                    msgSet = set(arrAct)
                    if msgSet.intersection(newActivities):
                        print("new act event {} - {} - {} - {} - {}".format(uname, msg.name, msg.date , msg.timeSlots , msg.activities))  
                        self.messages[uname].update(self.createEvent(msg.name, 'event', msg.date, msg.timeSlots, msg.activities)) 
            
            self.interests[uname] = self.interests[uname].union(setActivities)
            print('{}\'s interests {}'.format(uname, self.interests[uname]))

            response = self.conn[uname].SendMssg(n)

            # return response

    def login(self):     
        #conn = Client(uname, utype, '0.0.0.0' , '20')
        if request.method == "POST":
            uname = request.form["uname"]
            utype = request.form["userType"]

            self.startClient(uname, utype, '0.0.0.0', self.serverPort)
            time.sleep(1)
            return redirect(url_for("account", utype=utype, uname=uname))

        else:
            return render_template("login.html")
        
        #return redirect(url_for("account", uname=uname , utype=utype))
        #return render_template("login.html")
    
    def account(self, utype, uname):
        #q = request.args.to_dict()

        eventList = []

        if request.method == "POST":
            date = request.form["date1"]
            time1 = request.form["dropTime"]
            ptime = request.form["pickUpTime"]
            actList = request.form.getlist("checkboxes")
            print('{} {} {} {} {}'.format(uname, utype, date, type(time1), actList))
            
            time1 = time1.replace(":", "")
            temptime = int(time1)//100
            ptime = ptime.replace(":", "")
            ptime = int(ptime)//100

            dur = ptime - temptime

            actStr = ','.join(actList)

            timeSlots = time1
            intTime = int(time1)
            if int(dur) > 0:
                for i in range(int(dur)-1):
                    intTime = (intTime + 100) %2400
                    if len(str(intTime)) < 4:
                        timeSlots += ',' + '0{}'.format(str(intTime))
                    else:
                        timeSlots += ',' + str(intTime)
            
            sendStr = ''
            if utype == 'event':
                sendStr = 'event {} {} {} \n'.format(date, timeSlots, actStr)
            else:
                sendStr = 'request {} {} {} \n'.format(date, timeSlots, actStr)

            time.sleep(.5)
            #self.messages[uname].add(sendStr)
            response = self.sendToServer(sendStr, uname, utype)
            
            #return render_template("acct2.html", user_name=uname, user_type=utype , eventList=list(self.messages[uname].values()),  sent_msg='Post')
            return redirect(url_for("account", utype=utype, uname=uname))
        else:
            print('{} {}'.format(uname, utype))
            eventsToSend = []
            requestList = []
            rqst = chat_pb2.Number()  
            rqst.value = 0
            rqst.name = uname
            if utype != 'event':
                for msg in self.conn[uname].OpenRequests(rqst):
                    requestList += self.createEvent(uname, 'request', msg.date, msg.timeSlots, msg.activities).values()
                eventsToSend = (requestList + list(self.messages[uname].values()))
            else:
                eventsToSend = list(self.messages[uname].values())
            #print('\n\n {} \n'.format(requestList))
            print('{} {}'.format(uname, self.messages[uname]))
            return render_template("acct2.html", user_name=uname, user_type=utype, eventList=eventsToSend, sent_msg='Get')


def usage ( arglist ):
    if len(arglist) != 3:
        print("not enough arguments %d of 2" %(len(arglist)))
        print(arglist)
        print('python3 app.py -port <port>')
    if  int(arglist[2]) < 1023:
        print('port needs to be higher than 1023')

if __name__ == "__main__":
    usage(sys.argv)
    userPort = int(sys.argv[2])

    wc = webClient('0.0.0.0', userPort)
    wc.app.run(host="127.0.0.1", port=userPort, debug=True, threaded=True)