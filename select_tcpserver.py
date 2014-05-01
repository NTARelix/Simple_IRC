# Author:     Kevin Koshiol
# Filename:   select_tcpserver.py
# Date:       3/10/2013
# Class:      440

'''This file contains my base class for a custom event-driven server.'''

import os
import sys
import socket
import logging
import select

import daemon

class Server:
   '''
   Server is a base class for implementing a single threaded/processed,
   concurrent, event-driven server.
   Server must be extended and three methods must be overridden:
   -newClient(self)
   -received(self)
   -disconnected(self)
   Details about overriding each method is included in the documentation of
   each method.
   '''
   
   def __init__(self, name, port, interface="0.0.0.0"):
      '''
      Constructor: Sets up server properties.
      Arguments:
      -name[string]: Name of server; used for logging
      -port[int]: Bind to this port number
      -interface[string](optional): Bind to this interface address; default
      is all interfaces
      '''
      self.__MAX = 65535
      self.__serverPort = int(port)
      self.__interface = interface
      self.__name = name
      self.__passiveSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.__daemonize = False
      self.__backlog = 5
      self.__loggingLevel = logging.INFO
      self.__reuseAddr = True
      self.__clientID = -1 # Current client ID (ID=Socket File Descriptor)
      self.__clientAddr = {}
      self.__sockets = {}
      self.__responses = {}
      logging.basicConfig(level=logging.INFO,
         format="%(asctime)s > %(levelname)s > %(message)s",
         datefmt='%Y-%m-%d %I:%M:%S')
      self.__passiveSocket.setblocking(False)

   def start(self):
      '''
      After initializing server, this is called to begin listening. This method
      blocks until the server completes execution.
      '''
      if self.__reuseAddr:
         self.__passiveSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.__passiveSocket.bind((self.__interface,self.__serverPort))
      self.__passiveSocket.listen(self.__backlog)
      self.__sockets[self.__passiveSocket.fileno()]  = self.__passiveSocket
      poll = select.poll()
      poll.register(self.__passiveSocket, select.POLLIN)
      if not os.path.exists(self.getLogDirectory()):
         os.makedirs(self.getLogDirectory())
      if self.__daemonize:
         daemon.daemonize([self.__passiveSocket.fileno()])
      while True:
         for fd, event in poll.poll():
            self.__clientID = fd # Client being served
            sock = self.__sockets[fd]
            # Removed closed sockets from our list.
            if event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
               poll.unregister(fd)
               del self.__sockets[fd]
               self.__responses.pop(sock, None)
               self.disconnected()
               del self.__clientAddr[fd]
            
            # Accept connections from new sockets.
            elif sock is self.__passiveSocket:
               newsock, sockname = sock.accept()
               newsock.setblocking(False)
               fd = newsock.fileno()
               self.__clientID = fd # Client being served
               self.__clientAddr[fd] = newsock.getpeername()
               self.__sockets[fd] = newsock
               poll.register(fd, select.POLLIN)
               self.newClient()
            
            # Collect incoming data until newline character found.
            elif event & select.POLLIN:
               self.received()
            
            # Don't know how to handle it.
            else:
               logging.warning("Don't know how to handle event:")
               logging.warning("   " + str(fd) + ": " + str(event))
            
            self.__clientID = -1 # -1 indicates no client being served
    
   def disconnected(self):
      '''
      Must be overridden. Called when a connected socket has disconnected.
      Call self.getClientID() for ID of disconnected client.
      '''
      raise NotImplementedError("Must override Server.disconnected(self)")
    
   def received(self):
      '''
      Must be overridden. Called when data has been received from a client.
      Call self.getClientID() for ID of client from which to read.
      '''
      raise NotImplementedError("Must override Server.received(self)")
    
   def newClient(self):
      '''
      Must be overridden. Called when a new client has connected.
      Call self.getClientID() for ID of new client.
      '''
      raise NotImplementedError("Must override Server.newClient(self)")
   
   def recvAmount(self, size):
      '''
      Receives up to a certain number of bytes from current client.
      Argument size[int]: (Max) Number of bytes to receive
      Returns [string]: Received message
      '''
      sock = self.__sockets[self.getClientID()]
      message = sock.recv(size)
      if not message:
         sock.close()
      return message
   
   def recvUntil(self, suffix):
      '''
      Receives data from current client until a suffix is found.
      Argument suffix[string]: terminal string (suffix)
      Returns [string]: Received message without suffix
      '''
      sock = sockets[clientID]
      message = ''
      while not message.endswith(suffix):
         data = sock.recv(4096)
         if not data:
            break
         message += data
      return message
   
   def sendTo(self, clientID, message):
      '''
      Sends a message to a client.
      Arguments:
      -clientID[int]: ID of client
      -message[string]: message to be sent
      '''
      sock = self.__sockets[clientID]
      if sock:
         sock.sendall(message)
    
   def getLogFileName(self):
      '''Returns the server's log file name'''
      return self.__name + ".log"
   
   def getLogDirectory(self):
      '''Returns the server's log directory'''
      return os.path.expanduser("~") + "/logs/"
   
   def getLogFullName(self):
      '''Returns the server's log directory and path as one string'''
      return self.getLogDirectory() + self.getLogFileName()

   def getServerName(self):
      '''Returns the server's name'''
      return self.__name
   
   def setDaemonize(self, daemonize):
      '''
      Sets the daemonize property: whether to daemonize server or not.
      Argument daemonize[bool]: true to daemonize, false otherwise
      '''
      self.__daemonize = daemonize
   
   def getClientID(self):
      '''Returns current client's ID while handling an event'''
      return self.__clientID
   
   def getClientAddress(self, clientID=-1):
      '''
      Returns client's address (ipAddr, port)
      Argument clientID[int](optional): Client ID
         If no argument is given, the current client's address is returned.
      '''
      if clientID == -1:
         return self.__clientAddr[self.getClientID()]
      else:
         sock = self.__sockets[clientID]
         addr = sock.getpeername()
         return addr
   
   def getClientIPAddress(self, clientID=-1):
      '''
      Returns client's ip address
      Argument clientID[int](optional): Client ID
         If no argument is given, the current client's ip address is returned.
      '''
      return self.getClientAddress(clientID)[0]
   
   def getClientPortNumber(self, clientID=-1):
      '''
      Returns client's port number
      Argument clientID[int](optional): Client ID
         If no argument is given, the current client's port number is returned.
      '''
      return self.getClientAddress(clientID)[1]

if __name__ == "__main__":
   myserver = Server("uppercase", 35013)
   myserver.Start() # Should raise error on client connect
