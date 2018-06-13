import socket
import sys
import os
import subprocess
import select
import requests
import shutil
import time
import threading
import time
import urllib2

RECV_BUFFER_SIZE = 1024

#ssh hidri@gate1.csd.uoc.gr -oHostKeyAlgorithms=+ssh-dss
#reading end-servers list
threads = []
f=open(sys.argv[1],"r")
tm=f.read()
t=tm.split("\n")

#reading relays-list 
ff=open(sys.argv[2],"r")
tmm=ff.read()
tt=tmm.split("\n")  

end_servers_list=list()
relays_list=list()
ping_tracerout_direct=(0.0,0)
ping_tracerout_relay=list()
pings_relay=list()
traceroutes_relay=list()


#extracting information from relays-list 
for i in range(0,len(tt)-1):
        rr=tt[i].split(",")
        relays_list.append(rr)
#del relays_list[len(relays_list)-1]


#taking  the nameservers www.___.__ from file end_servers.txt
for i in range(0,len(t)-1):
	r=t[i].split(",")
	end_servers_list.append(r)
relay_nodes_list=list()

def take_serverNameFromAlias(alias):
	for i in range(0,len(end_servers_list)-1):
	    if alias in end_servers_list[i][1]:
		temp12=end_servers_list[i][0]
		break
        return temp12


def searchEndServerList(serverName):
	for i in range(0,len(end_servers_list)-1):
    		if serverName in end_servers_list[i][1]:
			return True 
    	return False 

def pingIP(ip ,num_pings):
    proc = subprocess.Popen("ping -c %d  %s" % (num_pings, ip), shell=True,
                            stdout=subprocess.PIPE)
    ping_data, b =proc.communicate()
    tmp2=ping_data
    tmp3=tmp2.split("\n")
    if len(tmp3)<7:
        print "packet is loss 100%"
        return 10000
    tmp=ping_data.split("\n")[num_pings+4]
    avg_RTT=tmp.split("/")[4]
#    print ping_data + "\n" + avg_RTT
    return avg_RTT

def tracerouteIP(ip):
    proc = subprocess.Popen("traceroute  %s" % ip, shell=True,
                            stdout=subprocess.PIPE)
    a, b =proc.communicate()
    v=a.split("\n")
    
    number_of_hops=v[len(v)-2].split(" ")
    if number_of_hops[0]=='':
         number_of_hops=v[len(v)-2].split(" ")[1]
    else :
         number_of_hops=v[len(v)-2].split(" ")[0]
    return number_of_hops


def Direct_ping_traceroute(end_server_address,pings):
    print "Starting " ,threading.currentThread().getName()," thread"
    rtt=pingIP(end_server_address,pings)
    hops=tracerouteIP(end_server_address)
    ping_tracerout_direct=(end_server_address,rtt,hops) 
    
def Relay_ping_traceroute(relay_node_address,pings):
    rtt=pingIP(relay_node_address,pings)
    hops=tracerouteIP(relay_node_address)
    return (rtt,hops)



def download_file(url):
    f = open(take_fileName(url), "wb")
    start_time = time.clock()
    f.write(urllib2.urlopen(url).read())
    print "Time need to download Image [",time.clock()-start_time,"] second"
    f.close


def RelayModeStatistic(end_server_address,relay_node_address,port_num,pings_num):
    ping_trac= Relay_ping_traceroute(relay_node_address,int(pings_num))   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_address = (relay_node_address,int(port_num))
    sock.connect(server_address)
    print >> sys.stderr, 'connecting to %s port %s' % server_address
    print "Starting " ,threading.currentThread().getName()," thread"    
    #create a packet for taking statistics to relay-server	
    tmp="-S"+"\n"
    tmp=tmp+end_server_address+"\n"
    tmp=tmp+str(ping_trac[0])+"\n"
    tmp=tmp+str(ping_trac[1])+"\n"
    tmp=tmp+pings_num+"\n"
   
    sock.sendall(tmp)
    amount_received =" "
    while True:#  select.select([sock], [], [], 15)[0]:
        data = sock.recv(RECV_BUFFER_SIZE)
#	print data
        if not data: break
        amount_received += data
    sock.close()
    ss=amount_received.split("\n")
    pings_relay.append(ss[1])
    traceroutes_relay.append(ss[2])
    ping_tracerout_relay.append(ss)
 
    

def makestr(s):#create paket-string from list
    name_server=take_nameserver(s)
    t=s.split("//")[1]
    path=t.split(name_server)[1]
    xy = []
    xy.append("GET %s HTTP/1.0"%path)
    xy.append("Host: %s"%name_server)
    rs = ""
    for x in range(0,len(xy)-1):
            rs+=xy[x]+"\r\n"
    rs+="\r\n"
    return rs

def take_nameserver(x):
    t=x.split("//")[1]
    t1=t.split("/")[0]
    print t1
    return t1

def take_fileName(x):
    tmp=x.split("/")
    k=tmp[len(tmp)-1].split(" ")[0]
    print "\n\n"+k
    return k




def chose_path():
        ping_tracerout_relay.sort(key=lambda tup: tup[1])
	ping_value=ping_tracerout_relay[0][1]
	hops_value=ping_tracerout_relay[0][2]

	if ping_value>ping_tracerout_direct[1]:
		return "DirectDownload"

	if ping_value<ping_tracerout_direct[1]:
		return ping_tracerout_relay[0]

	if ping_value==ping_tracerout_direct[1]:
		if hops_value>ping_tracerout_direct[2]:
			return "DirectDownload"

		if hops_value<ping_tracerout_direct[2]:
			return ping_tracerout_relay[0]

		if hops_value==ping_tracerout_direct[2]:
			lis=list()
			lis.append("DirectDownload")
			lis.append(ping_tracerout_relay[0])
                        return lis[random.randint(0,1)]



def DownloadFromRelayNode(end_server_address,relay_node_address,port_num):   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (relay_node_address,int(port_num))
    sock.connect(server_address)
    nam=take_fileName(end_server_address)
    print "connecting to [%s] port [%s]  for downloading image [%s]" % (server_address[0],server_address[1], nam)
    tmp1="-D"+"\n"
    tmp1=tmp1+end_server_address
    sock.sendall(tmp1)
    f = open(nam,"wb")
    start_time = time.clock()
    while True:
        data = sock.recv(RECV_BUFFER_SIZE)
        if not data: break
        f.write(data)
    sock.close()
    print "Time need to download Image [",time.clock()-start_time,"] second"  
    f.close()





while True:  
	var = raw_input("Please enter alias of server and pings number [alias] [pings]: ") 
	tmp=var.split(" ")
	alias=tmp[0]

	if not searchEndServerList(alias):
		print "[Error] Alias server doesn't exist in end_servers_list"
		print "Give again alias server "		
		continue
	
	nam_serv=take_serverNameFromAlias(alias)

	w = threading.Thread(name='Direct_ping_traceroute', target=Direct_ping_traceroute,args=(nam_serv,int(tmp[1]),))
	w.start()

	t=threading.Thread()
	for j in range(0,len(relays_list)-1):
		t=threading.Thread(name=relays_list[j][1],target=RelayModeStatistic, args=(nam_serv,relays_list[j][1],relays_list[j][2],tmp[1],))
		threads.append(t)
		t.start()
	for t in threads:
        	t.join()      
	w.join()		
	method=chose_path()
	print ping_tracerout_relay,"Pings_traceroute from relay_node"

	var = raw_input("Please enter URL: ")

	if method=="DirectDownload":
		print "Download image directly"
		download_file(var)
	else:
		print "Download Image from relay node"
		DownloadFromRelayNode(var,ping_tracerout_relay[0][3],ping_tracerout_relay[0][4])
	
	del ping_tracerout_relay[:]
	
