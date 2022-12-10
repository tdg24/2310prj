# 2310prj
TOY scheduler system for intergenerational learning

Project is a simulation of a intergeneration learning initiative to get senior and childer interacting. This scenario is for seniors in retirement homes. The facility would also serve as a semi day care. The simulated system would involve everything from registration, to scheduling to drop off and pickup. The attached component is considered a super component of the system because it enumerates and matches children with seniors based on times and interests. It would be a key component to any system that schedules these meetings. Parents, seniors and admins sign in to the portal. Which is a python flask application. This applicaiton communicates with a server/DB through backend gRPC communication. The program is run using the following commands. 

on server machine

  python3 server.py -port <port number>
  
app currently configured to run on same machine just for demo purpose (127.0.0.1 and port 20). Can configure to communicate with server based on ip in app.py. The web port is a different port than previously mentioned. It is already configured to communicate. This port is for the browser connection for the user. Must be 1024 or higher. 

  python3 app.py -port <web port>
  
 Users (seniors/admins/parents) would sign in at the following url. 
  
    http://127.0.0.1:1024
  
 request can be submitted and matches will be provided if there is intersection. 
