# ===========================================================================================
# ***************************************** LICENSE *****************************************
# ===========================================================================================
# Copyright (c) 2024, CATIE
# SPDX-License-Identifier: Apache-2.0

# ===========================================================================================
# *************************************** DESCRIPTION ***************************************
# ===========================================================================================
# This file is used to define the files manager.
# It uses the curses module to develop a terminal integrated files manager.


# ===========================================================================================
# **************************************** LIBRARIES ****************************************
# ===========================================================================================
# Libraries used for this application.
import logging
import threading

import curses

import os
from datetime import datetime



# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

pass

# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition

# Logs
logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
# logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

# Defining the colors used by the environment. Each color is matched to an integer, and has its proper object
# (see the funciont _initializeColors in the Terminal class)
COLORS = {
	# The indexes of each color, used to create the objects
	"index" : {
		"text" : 0,
		"sent" : 1,
		"received" : 0, # Same as text
		"alert" : 3
	},
	# The objects used to display some text. Defined here for more clarity
	"curses" : {
		"text" : None,
		"sent" : None,
		"received" : None,
		"alert" : None
	}
}

# Display flags
BOLD 	= 0b00000001
INDENT 	= 0b00000010
UPPER	= 0b00000100
ALERT 	= 0b00001000
SENT 	= 0b00010000
RECEIVED= 0b00100000



# ===========================================================================================
# ****************************************** CLASS ******************************************
# ===========================================================================================
# Class declaration/definition

class Terminal(threading.Thread):
	"""
    Represents a files manager. Allows to navigate through the tree, and select a file.
	The parameter thread indicates if the class has to be used threaded or not.
	"""
	def __init__(self,
				executeCommandFunction=None,
				threadGroup=None,
				threadTarget=None,
				threadName=None,
				threadArgs=list(),
				threadKwargs=dict(),
				threadDaemon=None,
				threaded=True,
				logger=None):
		
		if threaded:
			# Initialization of the thread
			super().__init__(group=threadGroup, target=threadTarget, name=threadName, daemon=threadDaemon)
		else:
			# Use the class as non threaded
			self.start = self.run

		self._args = threadArgs
		self._kwargs = threadKwargs

		# Initialization of the logger
		if logger:
			self._logger = logger
		else:
			self._logger = logging.Logger("Terminal")

		# Initialization of the values used for the curses environment
		self._stdscr = None
		self._offset = 0

		self.connectedClient = "" # The id to the client, shown in the header

		self._running = False
		self._input = "" # A string containing the user input
		self._cursorXPos = 0 # The horizontal position of the cursor, relatively to the beginning of the self._input string

		self._history = [] 	# A list that contains tuples of the command and the associated data:
							# Example : [(command1, data1), (command2, data2)]

		if (executeCommandFunction):
			self._executeCommandFunction = executeCommandFunction
		else:
			self._executeCommandFunction = lambda cmd, *args : self._logger.info("command %s : %s", cmd, args)


	def run(self):
		"""
		This function is almost a copy/paste of the curses.wrapper function (see https://github.com/python/cpython/blob/3.12/Lib/curses/__init__.py).
		Doing this allows the curses environment to be used inside of a threaded class.
		It only initializes the curses envrionment. The main function is _mainLoop.
		However, it returns the path to the selected file.
		"""

		self._logger.info("Starting terminal")

		# Initialize curses
		self._stdscr = curses.initscr()

		# Turn off echoing of keys, and enter cbreak mode,
		# where no buffering is performed on keyboard input
		curses.noecho()
		curses.cbreak()

		# In keypad mode, escape sequences for special keys
		# (like the cursor keys) will be interpreted and
		# a special value like curses.KEY_LEFT will be returned
		self._stdscr.keypad(1)

		# Start color, too.  Harmless if the terminal doesn't have
		# color; user can test with has_color() later on.  The try/catch
		# works around a minor bit of over-conscientiousness in the curses
		# module -- the error return from C start_color() is ignorable.
		try:
			curses.start_color()
		except:
			self._logger.warning("Could not initialize colors")
		else:
			self._initializeColors()

		# Turn on instant key response
		# self._stdscr.nodelay(1)
		
		self._logger.info("Files manager started. Start of the main loop")

		self._mainLoop()


	def _mainLoop(self):
		"""
		The mainloop of the curses envrionment.
		It returns the path to the selected file.
		"""
		self._running = True
		
		# Hide the cursor
		# curses.curs_set(0)

		# Display before starting the loop
		self._display()

		while self._running:
			# Move the cursor
			self._stdscr.move(curses.LINES - 1, min(curses.COLS - 1, 3 + self._cursorXPos))

			# Refresh to allow the user to see the cursor
			self._stdscr.refresh()
			
			# Get the key pressed
			key = self._stdscr.getch()

			if key != curses.ERR:
				if key == curses.KEY_BACKSPACE:
					if self._input and self._cursorXPos > 0:
						self._input = self._input[:self._cursorXPos-1] + self._input[self._cursorXPos:]
						self._cursorXPos -= 1
				elif key == curses.KEY_DC:
					self._input = self._input[:self._cursorXPos] + self._input[self._cursorXPos+1:]
				elif key == curses.KEY_ENTER or key == 10:  # 10 is the ASCII code for Enter
					self._onEnterPress()
				elif key == curses.KEY_LEFT:
					if self._cursorXPos > 0:
						self._cursorXPos -= 1
				elif key == curses.KEY_RIGHT:
					if self._cursorXPos < len(self._input):
						self._cursorXPos += 1
				elif key == 258 or key == 259: # Scrolling
					pass
				else:
					keyChar = chr(key)
					if keyChar.isprintable():
						if (self._cursorXPos < len(self._input)):
							self._input = self._input[:self._cursorXPos] + str(keyChar) + self._input[self._cursorXPos:]
						else:
							self._input += str(keyChar)
						self._cursorXPos += 1

			# Global display
			self._display()

		# End of the file manager
		self._logger.info("Ending files manager")
		# Set everything back to normal
		self._stdscr.keypad(0)
		curses.curs_set(1)
		curses.echo()
		curses.nocbreak()
		curses.endwin()
	

	def _initializeColors(self) -> None:
		"""
		Initializes the colors used in the terminal.
		The values used are defined upstream, in the "COLORS" dictionnary (check the VARIABLES section).
		"""

		# ********** Basic colors ********** 
		# Creates pairs linked to an integer
		# They represent the foreground color, then the background color
		curses.init_pair(COLORS["index"]["sent"], curses.COLOR_BLUE, curses.COLOR_BLACK) # Alert
		curses.init_pair(COLORS["index"]["alert"], curses.COLOR_RED, curses.COLOR_BLACK) # Alert

		# Match the color object on the color pair
		# These are the objects used when displaying some text
		COLORS["curses"]["text"] = curses.color_pair(COLORS["index"]["text"])
		COLORS["curses"]["sent"] = curses.color_pair(COLORS["index"]["sent"])
		COLORS["curses"]["received"] = curses.color_pair(COLORS["index"]["received"])
		COLORS["curses"]["alert"] = curses.color_pair(COLORS["index"]["alert"])
		

	def _drawHorizontalLine(self, line: int) -> None:
		"""
		Draws an horizontal line at the y line, through the whole screen.
		"""
		_, maxY = self._stdscr.getmaxyx()
		for i in range(maxY):
			self._stdscr.addch(line, i, curses.ACS_HLINE | COLORS["curses"]["text"])


	def _display(self) -> None:
		"""
		Displays the lines on the screen, with few additionnal infos like the keys to navigate through the tree.
		"""

		self._stdscr.clear()
		height, width = self._stdscr.getmaxyx()

		# ---------- Header ----------
		headerLines = 2
		self._stdscr.attron(curses.A_BOLD)

		if self.connectedClient:
			text = "Connected: {}".format(self.connectedClient)
			if len(text) < width-11:
				self._stdscr.addstr(0, (width - len(text)) // 2, text, COLORS["curses"]["text"] | curses.A_BOLD)
			elif len(self.connectedClient) < width-11:
				# If too large for the screen display only the id
				self._stdscr.addstr(0, (width - len(self.connectedClient)) // 2, self.connectedClient, COLORS["curses"]["text"] | curses.A_BOLD)
			else:
				self._stdscr.addstr(0, (width - 9) // 2, "Connected", COLORS["curses"]["text"] | curses.A_BOLD)
		else:
			self._stdscr.addstr(0, (width - 13) // 2, "Not connected", COLORS["curses"]["text"] | curses.A_BOLD)

		self._drawHorizontalLine(1)

		# ---------- Footer ----------
		footerLines = 2
		self._drawHorizontalLine(height - 2)
		if (3 + len(self._input) >= width):
			self._stdscr.addstr(height-1, 0, ">> " + self._input[self._cursorXPos-(width-3-1):self._cursorXPos], COLORS["curses"]["text"])
		else:
			self._stdscr.addstr(height-1, 0, ">> " + self._input, COLORS["curses"]["text"])
			
		
		# ---------- Main ----------
		availableLines = height - headerLines - footerLines
		# Define the maximum width available for text (considering indentation)
		maxWidth = width - 5

		linesCount = 0
		textToDisplay = []

		for command, text, flags in reversed(self._history):
			if text:
				# Split text into lines if it exceeds the maximum width
				lines = reversed([text[i:i+maxWidth] for i in range(0, len(text), maxWidth)])

				for line in lines:
					textToDisplay.append((line, flags | INDENT))
					linesCount += 1
					if linesCount >= availableLines:
						break
			
			if linesCount >= availableLines:
				break
			textToDisplay.append((command + ":", flags | BOLD | UPPER))
			linesCount += 1
			if linesCount >= availableLines:
				break
		
		textToDisplay.reverse()
		self._stdscr.move(headerLines, 0)
		for idx, (text, flags) in enumerate(textToDisplay):
			format = COLORS["curses"]["text"]

			# Configure format depending on the flags
			if flags & SENT:
				format = COLORS["curses"]["sent"]
			if flags & RECEIVED:
				format = COLORS["curses"]["received"]
			if flags & ALERT:
				format = COLORS["curses"]["alert"]
			if flags & BOLD:
				format |= curses.A_BOLD
			if flags & INDENT:
				text = "    " + text
			if flags & UPPER:
				text = text.upper()

			# Display the text
			self._stdscr.addstr(text, format)

			# Adds a line break for all line except the last one
			if idx < len(textToDisplay) - 1:
				self._stdscr.addch('\n')


		self._stdscr.refresh()


	def _onEnterPress(self) -> None:
		"""
		Executed when the user presses ENTER
		"""
		# Process the command
		inputList = self._input.split(' ')

		while inputList[0] == '': # Entry's first element empty
			if len(inputList) <= 1: # Empty entry
					self._input = ""
					self._cursorXPos = 0
					return
			inputList.pop(0)

		if inputList[0] == "exit":
			# End of the program
			self.stop()
			self._executeCommandFunction(inputList[0])
			return

		self._executeCommandFunction(inputList[0], *inputList[1:] if len(inputList) > 1 else ())
		self._input = ""
		self._cursorXPos = 0
	

	def addEntry(self, title: str, text: str, flags = 0) -> None:
		"""
		Add the title and text to the historic. Title is displayed in uppercase.
		Flags can be specified using the constant defined in this module
		"""
		self._history.append((title, text, flags))
		if len(self._history) > 45:
			self._history.pop(0)


	def stop(self) -> None:
		"""
		Stops the files manager.
		"""
		if self._running:
			self._logger.info("Closing terminal...")
			self._running = False
			self._stdscr.clear()




if __name__ == "__main__":
	# logsFile = os.path.join("logs", "Terminal_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logsFile = os.path.join("logs", "Terminal_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

	handler = logging.FileHandler(logsFile)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	handler.setLevel(logging.DEBUG)
	
	terminalLogger = logging.Logger("Terminal")
	terminalLogger.addHandler(handler)

	terminal = Terminal(logger=terminalLogger)

	history = [
        ("KEYWORD1", "some text corresponding to keyword 1 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD2", "some text corresponding to keyword 2 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD3", "some text corresponding to keyword 3 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD4", "some text corresponding to keyword 4 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD5", "some text corresponding to keyword 5 that can be longer than the width of the screen so it has to be split in lines", ALERT),
        ("KEYWORD6", "some text corresponding to keyword 6 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD7", "some text corresponding to keyword 7 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD8", "some text corresponding to keyword 8 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD9", "some text corresponding to keyword 9 that can be longer than the width of the screen so it has to be split in lines", ALERT),
        ("KEYWORD10", "some text corresponding to keyword 10 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD11", "some text corresponding to keyword 11 that can be longer than the width of the screen so it has to be split in lines", 0),
        ("KEYWORD12", "some text corresponding to keyword 12 that can be longer than the width of the screen so it has to be split in lines", SENT),
        ("KEYWORD13", "some text corresponding to keyword 13 that can be longer than the width of the screen so it has to be split in lines", RECEIVED),
        ("KEYWORD14", "some text corresponding to keyword 14 that can be longer than the width of the screen so it has to be split in lines", ALERT),
    ]
	for h in history:
		terminal.addEntry(*h)
	
	terminal.start()
	terminal.join()

	with open(logsFile, "+a") as f:
		f.write("\n")