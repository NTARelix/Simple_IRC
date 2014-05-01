# Author:     Kevin Koshiol
# Filename:   irc_server.py
# Date:       3/10/2013
# Class:      440

'''
This file contains my IRCServer class which extends my Server class. It
overrides all Server methods necessary handling the various events which an
event-driven server puts out.
'''
import logging

from select_tcpserver import *

class IRCServer(Server):
   '''
   IRCServer extends Server to work as a custom Internet Relay Chat server.
   Clients connect to the server and messages sent from one client are sent to
   all other connected clients.
   Three methods from the inherited class, Server, are overridden:
   -newClient(self)
   -received(self)
   -disconnected(self)
   '''
   PORT_NUMBER = 164
   FRAGMENT_SIZE = 256
   
   def __init__(self, portOffset=0, interface="0.0.0.0"):
      '''
      Constructor: Sets up server.
      Arguments:
      -portOffset[int](optional): offset from default port number; default is
      no offset
      -interface[string](optional): Bind to this interface address; default
      is all interfaces
      '''
      self.__portOffset = portOffset
      self.__interface = interface
      Server.__init__(self, "IRC Server", self.getPortNumber(), interface)
      logging.info("IRC Server Started on (" + interface + "," +
         str(self.getPortNumber()) + ")")
      self.__clientIDs = {} # key: Client ID; Value: Client Name
      self.__msgBuffer = {} # key: Client ID; Value: Receved data
      
   def getPortNumber(self):
      '''
      Returns the actual port number (IRC port number + port offset)
      '''
      return self.PORT_NUMBER + self.__portOffset
   
   def newClient(self):
      '''
      Server.newClient(self) override; Called when new client connects.
      Asks for client's name.
      '''
      clientID = Server.getClientID(self)
      addr = (Server.getClientIPAddress(self), Server.getClientPortNumber(self))
      self.__clientIDs[clientID] = ""
      self.__msgBuffer[clientID] = ""
      self.sendTo(clientID, "Hello, what's your name?")
      logging.info("New Client: " + str(addr))
   
   def received(self):
      '''
      Server.received(self) override; Called when message received.
      If client doesn't have name: message is name.
      If client has name: message is relayed to all clients with names.
      '''
      # Gathers info about received data
      clientID = Server.getClientID(self)
      name = self.__clientIDs[clientID]
      data = Server.recvAmount(self, IRCServer.FRAGMENT_SIZE)
      
      # Get message from
      self.__msgBuffer[clientID] += data
      message = self.getMessage(clientID).strip()
      
      # While the client still has messages to send...
      while message:
         # If they have no name, the message should be the name
         if not self.__clientIDs[clientID]:
            # Take up to 8 characters for name, remaining characters discarded
            if len(message) > 8:
               name = message[:8]
            else:
               name = message
            if not self.nameExists(name):
               self.__clientIDs[clientID] = name.strip()
               # Tell everyone about the new user
               addr = Server.getClientAddress(self)
               ip = addr[0]
               port = addr[1]
               msg = ':'.join([name,ip,str(port) + " Connected"])
               logging.info("Client at " + str(addr) + " took name '" + name + "'")
               self.sendAll(msg)
            else:
               self.sendTo(clientID, "Someone is already using that name.")
               self.sendTo(clientID, "What's your name?")
         else: # Client has name so the message should be relayed
            name = self.__clientIDs[clientID]
            ip = ""
            msg = ':'.join([name,ip,message])
            self.sendAll(msg)
         # Update message with data from buffer
         message = self.getMessage(clientID).strip()
   
   def nameExists(self, name):
      '''
      Returns whether a name has been taken already (case insensitive).
         True if name has been taken
         False otherwise
      '''
      for clientName in self.__clientIDs.values():
         if clientName.lower() == name.lower():
            return True
      return False
   
   def getMessage(self, clientID):
      '''Pops message from buffer and returns popped message.'''
      message = ""
      # If client has finished a message, extract the message
      buf = self.__msgBuffer[clientID]
      if '\n' in buf:
         index = buf.find('\n')
         message = buf[:index + 1]
         self.__msgBuffer[clientID] = buf[index + 1:]
      # If client's message is too big, send a portion of it
      elif len(buf) >= IRCServer.FRAGMENT_SIZE:
         message = buf[:IRCServer.FRAGMENT_SIZE].strip()
         self.__msgBuffer[clientID] = buf[IRCServer.FRAGMENT_SIZE:]
      return message.strip()
   
   def disconnected(self):
      '''
      Server.disconnected(self) override; Called when client disconnects.
      Relays message to all users that a client has disconnected.
      '''
      clientID = Server.getClientID(self)
      name = self.__clientIDs[clientID]
      del self.__clientIDs[clientID]
      
      addr = Server.getClientAddress(self)
      ip = addr[0]
      if name:
         self.sendAll(name + ":" + ip + " disconnected")
         logging.info(name + " disconnected")
      else:
         logging.info(str(addr) + " disconnected")
   
   def sendAll(self, message):
      '''
      Sends a message to all clients which are fully connected (must have
         name to be connected). Appends newline character to message.
      Argument message[string]: Message to be sent.
      '''
      if message.strip():
         for client in self.__clientIDs.keys(): # every client
            if self.__clientIDs[client]: # if client has name
               self.sendTo(client, message)
   
   def sendTo(self, clientID, message):
      '''
      Sends a message to a client. Appends newline character to message.
      Arguments:
      -clientID[int]: Client ID to which message will be sent.
      -message[string]: Message to send.
      '''
      if message.strip():
         Server.sendTo(self, clientID, message.strip() + "\n")

if __name__ == "__main__":
   myServer = IRCServer(35000)
   myServer.setDaemonize(False)
   myServer.start()