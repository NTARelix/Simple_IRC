# Author:     Kevin Koshiol
# Filename:   irc_gui.py
# Date:       3/6/2013
# Class:      440

'''
This file contains my IRC Client GUI. Uses PyGTK for GUI.
Majority of window dedicated displaying messages. Bottom of window used for
user interaction: Entry box allows text to be entered, send sends 
'''

import pygtk
import gtk
import sys
import socket
import gobject

class IRCGUI:
   '''IRCGUI provides a user interface for my IRC Client'''
   
   def __init__(self):
      '''Constructor: Sets up all widgets, window, and socket'''
      
      # Connection Window
      self.connectWindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
      
      self.connectIPBox = gtk.Entry(0)
      self.connectIPBox.set_text("")
      self.connectPortBox = gtk.Entry(0)
      self.connectPortBox.set_text("")
      self.connectButton = gtk.Button("Connect")
      self.connectButton.set_sensitive(False)
      
      self.connectIPBox.show()
      self.connectPortBox.show()
      self.connectButton.show()
      
      self.ipLabel = gtk.Label("IP")
      self.portLabel = gtk.Label("Port")
      
      self.ipLabel.show()
      self.portLabel.show()
      
      self.connectTable = gtk.Table(2,3)
      self.connectTable.attach(self.ipLabel, 0, 1, 0, 1)
      self.connectTable.attach(self.portLabel, 0, 1, 1, 2)
      self.connectTable.attach(self.connectIPBox, 1, 2, 0, 1)
      self.connectTable.attach(self.connectPortBox, 1, 2, 1, 2)
      self.connectTable.attach(self.connectButton, 2, 3, 0, 2)
      self.connectTable.set_focus_chain((self.connectIPBox, self.connectPortBox, self.connectButton))
      self.connectTable.show()
      
      self.connectWindow.add(self.connectTable)
      self.connectWindow.show()
      
      self.connectIPBox.connect("activate", self.makeConnection)
      self.connectPortBox.connect("activate", self.makeConnection)
      self.connectButton.connect("clicked", self.makeConnection)
      self.connectWindow.connect("delete_event", self.delete_event)
      self.connectWindow.connect("destroy", self.destroy)
      self.connectIPBox.connect("changed", self.changedText)
      self.connectPortBox.connect("changed", self.changedText)
      
      # IRC Window
      self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
      self.window.set_size_request(300,200)
      self.window.set_title("IRC Client")
      
      self.scrollbox = gtk.ScrolledWindow()
      self.scrollbox.show()
      
      self.windowBox = gtk.VBox(False, 0)
      self.windowBox.show()
      
      self.messages = gtk.VBox(False, 0)
      self.messages.show()
      
      self.scrollbox.add_with_viewport(self.messages)
      
      self.editBox = gtk.HBox(False, 0)
      self.editBox.show()
      
      self.windowBox.pack_start(self.scrollbox, True, True, 0)
      self.windowBox.pack_end(self.editBox ,False, False, 0)
      
      self.entry = gtk.Entry(0)
      self.entry.show()
      
      self.sendButton = gtk.Button("Send")
      self.sendButton.show()
      
      self.editBox.pack_start(self.entry, True, True, 0)
      self.editBox.pack_end(self.sendButton, False, False, 0)
      self.editBox.show()
      
      self.entry.connect("activate", self.send)
      self.sendButton.connect("clicked", self.send)
      self.window.connect("delete_event", self.delete_event)
      self.window.connect("destroy", self.destroy)
      
      self.window.add(self.windowBox)
      #self.window.show()
      
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.dataBuffer = ""
   
   def makeConnection(self, widget, data=None):
      '''
      Takes data from IP and Port fields and attempts to make a connection to
      the server specified in these fields.
      '''
      ip = ""
      try:
         ip = socket.gethostbyname(self.connectIPBox.get_text())
      except Exception as e:
         fail = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            "Failed to resolve host\n" + str(e))
         fail.run()
         fail.destroy()
         return
      port = int(self.connectPortBox.get_text())
      self.connectTo((ip, port))
   
   def changedText(self, widget, data=None):
      sensitive = len(self.connectIPBox.get_text()) > 0 and \
         len(self.connectPortBox.get_text()) > 0 and \
         self.connectPortBox.get_text().isdigit() and \
         int(self.connectPortBox.get_text()) > 0
      self.connectButton.set_sensitive(sensitive)
   
   def connectTo(self, addr):
      try:
         self.socket.settimeout(1)
         self.socket.connect(addr)
      except Exception as e:
         fail = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            "Failed to connect\n" + str(e))
         fail.run()
         fail.destroy()
         return
      self.connectWindow.hide()
      self.window.show()
      self.entry.grab_focus()
      self.socket.setblocking(False)
      gobject.io_add_watch (self.socket.fileno(), gobject.IO_IN, self.read)
      gobject.io_add_watch (self.socket.fileno(), gobject.IO_ERR, self.disconnect)
      gobject.io_add_watch (self.socket.fileno(), gobject.IO_HUP, self.disconnect)
   
   def disconnect(self, source=None, condition=None):
      dia = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            "Lost connection to server")
      dia.run()
      dia.destroy()
      sys.exit(0)
   
   def send(self, widget, data=None):
      message = self.entry.get_text()
      self.entry.set_text("")
      self.entry.grab_focus()
      if message.strip():
         self.socket.sendall(message + "\n")
   
   def read(self, source, condition):
      data = self.socket.recv(256)
      if not data:
         self.disconnect()
      self.dataBuffer += data
      
      message = self.getNextMessage()
      while message:
         self.add_message(message)
         message = self.getNextMessage()
      return True
   
   def getNextMessage(self):
      msg = ""
      if '\n' in self.dataBuffer:
         index = self.dataBuffer.find('\n')
         msg = self.dataBuffer[:index + 1]
         self.dataBuffer = self.dataBuffer[index + 1:]
      return msg.strip()
   
   def add_message(self, message):
      if (not message):
         return
      tbox = gtk.HBox(False, 0)
      tbox.set_border_width(5)
      tbox.show()
      
      text = gtk.Label(message)
      text.set_line_wrap(True)
      tbox.pack_start(text, False, True, 0)
      text.show()
      
      self.messages.pack_start(tbox, False, True, 0)
      adj = self.scrollbox.get_vadjustment()
      adj.set_value(adj.get_upper())
   
   def delete_event(self, widget, event, data=None):
      return False
   
   def destroy(self, widget, data=None):
      #TODO: Cleanup
      gtk.main_quit()
   
   def main(self):
      gtk.main()

if __name__ == "__main__":
   base = IRCGUI()
   base.main()
