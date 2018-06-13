import socket
import sys
import os
import subprocess
import select
import requests
import shutil
import urllib2

RECV_BUFFER_SIZE = 1024 

# Create a TCP/IP socket

addr=sys.argv[1]
port_n=sys.argv[2]

def take_nameserver(x):
    t=x.split("//")[1]
    t1=t.split("/")[0]
    print t1
    return t1

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
    print ping_data + "\n" + avg_RTT
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
    rtt=pingIP(end_server_address,pings)
    hops=tracerouteIP(end_server_address)
    return (rtt,hops)


def send1(url):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    name=take_nameserver(url)
    s.connect((name, 80))  
    s.send(data)

    recvd=""
    while True:
        data = s.recv(1024)
        if not data: print " Done "; break
        recvd += data
    data = recvd.split("image/jpeg")[1]
    data = recvd.split("\r\n\r\n", 1)[1]
    s.close()
    return data

def sendServer():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to the port
#By setting the host name to the empty string, it tells the bind() method to fill in the address of the current machine.
	server_address = (addr,int(port_n))
	print >>sys.stderr, 'starting up on %s port %s' % server_address
	sock.bind(server_address)
# Listen for incoming connections
	sock.listen(1)
	while True:
    # Wait for a connection
    			print >>sys.stderr, 'waiting for a connection'
    			connection, client_address = sock.accept()
        		print >>sys.stderr, 'connection from', client_address
			amount_received =b''
        # Receive the data in small chunks 1KB
	        	while True:
        	    		data = connection.recv(RECV_BUFFER_SIZE)
            			print >>sys.stderr, 'received "%s"' % data
				if data:
					amount_received += data
					d=amount_received.split("\n")
                                        print d[0]
                                        if d[0]=="-S":
                                                ss=Direct_ping_traceroute(d[1],int(d[4]))
                                                overall_ping_rtt=float(d[2])+float(ss[0])
                                                overall_hops=int(d[3])+int(ss[1])
                                                data=d[1]+"\n"+str(overall_ping_rtt)+"\n"+str(overall_hops)+"\n"+addr+"\n"+port_n+"\n"
                                                print data
                                                connection.sendall(data)
                                                break
                                        if d[0]=="-D":
                                                response=urllib2.urlopen(d[1])
                                                ss=response.read()
                                                connection.sendall((ss))
                                                break
	
            			else:
                			print >>sys.stderr, 'no more data from',client_address
#					d=amount_received.split("\n")
#                                        print d[0]
#					if d[0]=="-S":
 #                                       	ss=Direct_ping_traceroute(d[1],int(d[4]))
  #                                      	overall_ping_rtt=float(d[1])+float(ss[0])
#                                        	overall_hops=int(d[3])+int(ss[1])
#                                        	data=d[1]+"\n"+str(overall_ping_rtt)+"\n"+str(overall_hops)+"\n"
#                                        	print data
#                                 		connection.sendall(data)
#                        	                break
# 			            	if d[0]=="-D":
#						response=urllib2.urlopen(amount_received)
#                                		ss=response.read()
#                                		connection.sendall((ss))       
                               		break
	                connection.close()
		


sendServer()
