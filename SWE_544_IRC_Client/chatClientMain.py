import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
#Above libraries are required by the Qt section
import socket
import threading
import Queue
import time


class ReadThread (threading.Thread):

	def __init__(self, name, csoc, threadQueue, screenQueue):
		threading.Thread.__init__(self)
		self.name = name
		self.csoc = csoc
		self.nickname = ""
		self.threadQueue = threadQueue
		self.screenQueue = screenQueue

	def incoming_parser(self, data):
	
		# Handle empty message from server
		if len(data) == 0:
			return
		
		# Handle message with first word longer than 3 letters
		elif len(data) > 3 and not data[3] == " ":
			response = "ERR"
			self.csoc.send(response)
			return
		
		else:
			rest = data[4:]
			
			if data[0:3] == "BYE":
				username = rest.strip()
				msg = "Goodbye " + username + ", we hope to see you again!"
			
			elif data[0:3] == "ERL":
				msg = "You need to login to do that. Login command: USR <username>"
			
			elif data[0:3] == "HEL":
				username = rest.strip()
				msg = "Login successful. Hello " + username
			
			elif data[0:3] == "REJ":
				username = rest.strip()
				msg = "Username " + username + " already exists in the system. Please login with a different username."
			
			elif data[0:3] == "MNO":
				username = rest.strip()
				msg = "User " + username + " could not be found. Message was not delivered."
			
			elif data[0:3] == "MSG":
				splitted = rest.split(":")
				username = splitted[0]
				message = splitted[1]
				msg = username + " <private> : " + message
			
			elif data[0:3] == "SAY":
				msg = "Someone says " + rest[0]
			
			elif data[0:3] == "SYS":
				msg = "<SYSTEM MESSAGE> : " + rest[0]
			
			elif data[0:3] == "LSA":
				splitted = rest.split(":")
				msg = "-Server- Registered nicks: "
				for i in splitted:
					msg += i + ","
				msg = msg[:-1]
			
			elif data[0:3] == "TOC":
				msg = "TOC!"
			
			elif data[0:3] == "SOK":
				msg = "Message sent to everyone."
			
			elif data[0:3] == "MOK":
				msg = "Private message delivered to user."
			
			elif data[0:3] == "ERR":
				msg = "Invalid command."
			
			else:
				response = "ERR"
				self.csoc.send(response)
				return

		
			#self.app.cprint(msg)
			self.screenQueue.put(msg)

	def run(self):
		while True:
			data = self.csoc.recv(1024)
			self.incoming_parser(data)
			#...
			#...


class WriteThread (threading.Thread):

	def __init__(self, name, csoc, threadQueue):
		threading.Thread.__init__(self)
		self.name = name
		self.csoc = csoc
		self.threadQueue = threadQueue

	def run(self):
		#...
		#...
		while True:
			if self.threadQueue.qsize() > 0:
				queue_message = self.threadQueue.get()
				#...
				#...
				#...
				self.csoc.send(queue_message)
				try:
					self.csoc.send(queue_message)
				except socket.error:
					self.csoc.close()
					break


class ClientDialog(QDialog):

	''' An example application for PyQt. Instantiate
	and call the run method to run. '''

	def __init__(self, threadQueue, screenQueue):
		self.threadQueue = threadQueue
		self.screenQueue = screenQueue
		
		# create a Qt application --- every PyQt app needs one
		self.qt_app = QApplication(sys.argv)
		
		# Call the parent constructor on the current object
		QDialog.__init__(self, None)
		
		# Set up the window
		self.setWindowTitle('IRC Client')
		self.setMinimumSize(500, 200)
		self.resize(640, 480)
		
		# Add a vertical layout
		self.vbox = QVBoxLayout()
		self.vbox.setGeometry(QRect(10, 10, 621, 461))
		
		# Add a horizontal layout
		self.hbox = QHBoxLayout()
		
		# The sender textbox
		self.sender = QLineEdit("", self)
		
		# The channel region
		self.channel = QTextBrowser()
		self.channel.setMinimumSize(QSize(480, 0))
		
		# The send button
		self.send_button = QPushButton('&Send')
		
		# The users' section
		self.userList = QListView()
		
		# Connect the Go button to its callback
		self.send_button.clicked.connect(self.outgoing_parser)
		
		# Add the controls to the vertical layout
		self.vbox.addLayout(self.hbox)
		self.vbox.addWidget(self.sender)
		self.vbox.addWidget(self.send_button)
		self.hbox.addWidget(self.channel)
		self.hbox.addWidget(self.userList)
		
		# start timer
		self.timer = QTimer()
		self.timer.timeout.connect(self.updateChannelWindow)
		
		# update every 10 ms
		self.timer.start(1000)
		
		# Use the vertical layout for the current window
		self.setLayout(self.vbox)

	def cprint(self, data):
		#...
		#...
		#...
		self.channel.append(data)

	def updateChannelWindow(self):
		if self.screenQueue.qsize() > 0:
			queue_message = self.screenQueue.get()
			#...
			#...
			#...
			self.channel.append(queue_message)

	def outgoing_parser(self):
		data = self.sender.text()
		
		# Handle empty input from user
		if len(data) == 0:
			return
		
		# Valid user messages start with a "/"
		if data[0] == "/":
			theCommandText = ''.join(data[1:])
			theCommandList = theCommandText.split()
			command = theCommandList[0]
			delta = theCommandList[1:]
			delta = ':'.join(delta)
			
			if command == "nick":
				self.threadQueue.put("USR " + delta)
			
			if command == "list":
				self.threadQueue.put("LSQ")
			
			elif command == "quit":
				self.threadQueue.put("QUI")
			
			elif command == "msg":
				self.threadQueue.put("MSG " + delta)
			
			else:
				self.cprint("Local: Command Error.")
		
		else:
			self.threadQueue.put("SAY " + data)
		
		self.sender.clear()

	def run(self):
	
		''' Run the app and show the main form. '''
		
		self.show()
		self.qt_app.exec_()




# connect to the server
s = socket.socket()
connectString = sys.argv[1]
connectParams = connectString.split(":")
host = connectParams[0]
port = int(connectParams[1])
s.connect((host,port))

sendQueue = Queue.Queue()
screenQueue = Queue.Queue()

app = ClientDialog(sendQueue, screenQueue)

# start threads
rt = ReadThread("ReadThread", s, sendQueue, screenQueue)
rt.start()

wt = WriteThread("WriteThread", s, sendQueue)
wt.start()

app.run()

rt.join()
wt.join()
s.close()
