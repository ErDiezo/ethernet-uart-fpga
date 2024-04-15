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
		"alert" : 3
	},
	# The objects used to display some text. Defined here for more clarity
	"curses" : {
		"text" : None,
		"alert" : None
	}
}



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
			self._logger = logging.Logger("default")

		# Initialization of the values used for the curses environment
		self._stdscr = None
		self._currentDir = os.getcwd()
		self._offset = 0

		self._connectedClient = "" # The id to the client, shown in the header

		self._running = False
		self._input = "" # A string containing the user input
		self._cursorXPos = 0 # The horizontal position of the cursor, relatively to the beginning of the self._input string

		self._history = [] 	# A list that contains tuples of the command and the associated data:
							# Example : [(command1, data1), (command2, data2)]

		self.commands = [] # A list of all commands that have to be sent


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
			self._stdscr.move(curses.LINES - 1, 3 + self._cursorXPos)

			# Refresh to allow the user to see the cursor
			self._stdscr.refresh()
			
			# Get the key pressed
			key = self._stdscr.getch()

			if key != curses.ERR:
				if key == curses.KEY_BACKSPACE:
					if self._input:
						self._input = self._input[:-1]
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
						# Prevent to enter something larger than the sceen size
						if self._cursorXPos < curses.COLS - 4:
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
		curses.init_pair(COLORS["index"]["alert"], curses.COLOR_RED, curses.COLOR_BLACK) # Alert

		# Match the color object on the color pair
		# These are the objects used when displaying some text
		COLORS["curses"]["text"] = curses.color_pair(COLORS["index"]["text"])
		COLORS["curses"]["alert"] = curses.color_pair(COLORS["index"]["alert"])

		# ********** Alert colors **********
		

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
		if self._connectedClient:
			if len(text) < width-11:
				self._stdscr.addstr(0, (width - len(text)) // 2, text, COLORS["curses"]["text"] | curses.A_BOLD)
			elif len(self._connectedClient) < width-11:
				# If too large for the screen display only the id
				self._stdscr.addstr(0, (width - len(self._connectedClient)) // 2, self._connectedClient, COLORS["curses"]["text"] | curses.A_BOLD)
			else:
				self._stdscr.addstr(0, (width - 9) // 2, "Connected", COLORS["curses"]["text"] | curses.A_BOLD)
		else:
			self._stdscr.addstr(0, (width - 13) // 2, "Not connected", COLORS["curses"]["text"] | curses.A_BOLD)

		self._drawHorizontalLine(1)

		# ---------- Footer ----------
		footerLines = 2
		self._drawHorizontalLine(height - 2)
		self._stdscr.addstr(height-1, 0, ">> " + self._input, COLORS["curses"]["text"])
		
		# ---------- Main ----------
		availableLines = height - headerLines - footerLines
		# Define the maximum width available for text (considering indentation)
		maxWidth = width - 5

		linesCount = 0
		textToDisplay = []

		for command, text in reversed(self._history):
			if text:
				# Split text into lines if it exceeds the maximum width
				lines = reversed([text[i:i+maxWidth] for i in range(0, len(text), maxWidth)])

				for line in lines:
					textToDisplay.append(line)
					linesCount += 1
					if linesCount >= availableLines:
						break
			
			if linesCount >= availableLines:
				break
			textToDisplay.append("*BOLD*" + command + ":")
			linesCount += 1
			if linesCount >= availableLines:
				break
		
		textToDisplay.reverse()
		self._stdscr.move(headerLines, 0)
		for idx, line in enumerate(textToDisplay):
			if line[:6] == "*BOLD*":
				self._stdscr.attron(curses.A_BOLD)
				self._stdscr.addstr(line[6:] + '\n')
				self._stdscr.attroff(curses.A_BOLD)
			else:
				self._stdscr.addstr("    " + line)
				if idx < len(textToDisplay) - 1:
					self._stdscr.addch('\n')


		self._stdscr.refresh()


	def _onEnterPress(self) -> None:
		"""
		Executed when the user presses ENTER
		"""
		if self._input == "exit":
			self.stop()
			return

		# Process the command
		inputList = self._input.split(' ')
		self._history.append((inputList[0], ' '.join(inputList[1:]) if len(inputList) > 1 else None))
		self._input = ""
		self._cursorXPos = 0


	def stop(self) -> None:
		"""
		Stops the files manager.
		"""
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

	terminal._history = [
        ("KEYWORD1", "some text corresponding to keyword 1 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD2", "some text corresponding to keyword 2 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD3", "some text corresponding to keyword 3 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD4", "some text corresponding to keyword 4 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD5", "some text corresponding to keyword 5 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD6", "some text corresponding to keyword 6 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD7", "some text corresponding to keyword 7 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD8", "some text corresponding to keyword 8 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD9", "some text corresponding to keyword 9 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD10", "some text corresponding to keyword 10 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD11", "some text corresponding to keyword 11 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD12", "some text corresponding to keyword 12 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD13", "some text corresponding to keyword 13 that can be longer than the width of the screen so it has to be split in lines"),
        ("KEYWORD14", "some text corresponding to keyword 14 that can be longer than the width of the screen so it has to be split in lines"),
        # Add more data as needed
    ]
	
	terminal.start()
	terminal.join()

	with open(logsFile, "+a") as f:
		f.write("\n")