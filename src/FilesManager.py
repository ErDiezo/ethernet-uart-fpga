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
from curses.textpad import rectangle

import os
from datetime import datetime
from typing import List



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
logsFiles = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
# logsFiles = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

# Defining the colors used by the environment. Each color is matched to an integer, and has its proper object
# (see the funciont _initializeColors in the FilesManager class)
COLORS = {
	# The indexes of each color, used to create the objects
	"index" : {
		"text" : 0,
		"file" : 0,
		"dir" : 1,
		"path" : 3, # Same as alert
		"alert" : 3
	},
	# The objects used to display some text. Defined here for more clarity
	"curses" : {
		"text" : None,
		"file" : None,
		"dir" : None,
		"path" : None,
		"alert" : None
	}
}



# ===========================================================================================
# ****************************************** CLASS ******************************************
# ===========================================================================================
# Variable declaration/definition

class FilesManager(threading.Thread):
	"""
    Represents a files manager. Allows to navigate through the tree, and select a file.
	"""
	def __init__(self,
				threadGroup=None,
				threadTarget=None,
				threadName=None,
				threadArgs=list(),
				threadKwargs=dict(),
				threadDaemon=None,
				logger=None):
		
		# Initialization of the thread
		super().__init__(group=threadGroup, target=threadTarget, name=threadName, daemon=threadDaemon)
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
		self._files = sorted(os.listdir(self._currentDir))
		self._selectedIndex = 0
		self._offset = 0
		self._availableLines = 0
		self._height, self._width = 0, 0
		self._chosenFile = None


	def run(self) -> str:
		"""
		This function is almost a copy/paste of the curses.wrapper function (see https://github.com/python/cpython/blob/3.12/Lib/curses/__init__.py).
		Doing this allows the curses environment to be used inside of a threaded class.
		It only initializes the curses envrionment. The main function is _mainLoop.
		However, it returns the path to the selected file.
		"""

		self._logger.info("Starting files manager")

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
		
		self._logger.info("Files manager started. Start of the main loop")

		try:
			return self._mainLoop()
		except curses.error as e:
			filesManagerLogger.error("The terminal might be too small. Try to make it bigger (Error : %s)", e)


	def _mainLoop(self) -> str:
		"""
		The mainloop of the curses envrionment.
		It returns the path to the selected file.
		"""
		
		# Hide the cursor
		curses.curs_set(0)

		# Display before starting the loop
		self._display()

		while True:
			# Get the key pressed
			key = self._stdscr.getch()

			# Actions depending on the key pressed
			if key == ord('q'): # Quit the program
				break
			elif key == ord('a'): # Test
				self._alert("test")
			elif key == curses.KEY_UP and self._selectedIndex > 0: # Navigate threw the tree
				self._selectedIndex -= 1
				if (self._selectedIndex < self._offset):
					self._offset -= 1
			elif key == curses.KEY_DOWN and self._selectedIndex < len(self._files) - 1: # Navigate threw the tree
				self._selectedIndex += 1
				if (self._selectedIndex > self._availableLines - 1 + self._offset):
					self._offset += 1
			elif key == curses.KEY_LEFT:
				self._changeDir(os.path.dirname(self._currentDir))
			elif key == curses.KEY_RIGHT:
				self._onKeyRight()
			elif key == curses.KEY_ENTER or key == 10 or key == 13: # ENTER or \n or \r
				if self._onEnterPress():
					break
			# TODO : one key to press to enter the full path with the keyboard

			self._display()

		# End of the file manager
		self._logger.info("Ending files manager")
		# Set everything back to normal
		self._stdscr.keypad(0)
		curses.echo()
		curses.nocbreak()
		curses.endwin()

		if self._chosenFile:
			self._logger.info("File chosen : %s", self._chosenFile)
		return self._chosenFile
	

	def _initializeColors(self) -> None:
		"""
		Initializes the colors used in the terminal.
		The values used are defined upstream, in the "COLORS" dictionnary (check the VARIABLES section).
		"""

		# ********** Basic colors ********** 
		# Creates pairs linked to an integer
		# They represent the foreground color, then the background color
		curses.init_pair(COLORS["index"]["dir"], curses.COLOR_CYAN, curses.COLOR_BLACK) # Directory
		curses.init_pair(COLORS["index"]["alert"], curses.COLOR_RED, curses.COLOR_BLACK) # Alert

		# Match the color object on the color pair
		# These are the objects used when displaying some text
		COLORS["curses"]["text"] = curses.color_pair(COLORS["index"]["text"])
		COLORS["curses"]["file"] = curses.color_pair(COLORS["index"]["file"])
		COLORS["curses"]["dir"] = curses.color_pair(COLORS["index"]["dir"])
		COLORS["curses"]["path"] = curses.color_pair(COLORS["index"]["path"])
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
		self._stdscr.addstr(0, 0, "path :", COLORS["curses"]["text"])
		# If too large for the screen (size of "path : ..." + 1), shortens the path
		if (len(self._currentDir)) < width-11:
			self._stdscr.addstr(0, 7, self._currentDir, COLORS["curses"]["path"])
		else:
			self._stdscr.addstr(0, 7, "...{}".format(self._currentDir[len(self._currentDir)-width+11:]), COLORS["curses"]["path"])
		self._drawHorizontalLine(1)

		# ---------- Footer ----------
		footerLines = 2
		self._drawHorizontalLine(height-2)
		footer = "[q] Quit    [<] Go out    [>] Go in    [ENTER] Send file"
		if width > 56: # len(footer) 
			self._stdscr.addstr(height-1, 0, "[q] Quit    [<] Go out    [>] Go in    [ENTER] Send file", COLORS["curses"]["text"])
		else:
			self._stdscr.addstr(height-1, 0, "[q]    [<]    [>]    [ENTER]", COLORS["curses"]["text"])

		# ---------- Main ----------
		self._availableLines = height - headerLines - footerLines
		# The offset allows to scrool the list if it is too long to be shown in the entire screen
		offset = max(0, self._selectedIndex - self._availableLines + 1)
		for i in range(min(len(self._files), self._availableLines)):
			currentFile = os.path.join(self._currentDir, self._files[i + self._offset])
			if os.path.isdir(currentFile):
				self._stdscr.addstr(i + headerLines, 0, self._files[i + self._offset], COLORS["curses"]["dir"] | curses.A_BOLD | curses.A_REVERSE*((i + self._offset)==self._selectedIndex))
			else:
				self._stdscr.addstr(i + headerLines, 0, self._files[i + self._offset], COLORS["curses"]["file"] | curses.A_REVERSE*((i + self._offset)==self._selectedIndex))

		self._stdscr.refresh()
	

	def _alert(self,
			subText1 = "Do you really want to send this file?",
			subText1Replacement = "Send this file?",
			subText2 = ""
			) -> bool:
		"""
		This function is used to display an alert in the center of the screen
		"""

		response = False

		oldHeight, oldWidth = self._stdscr.getmaxyx()
		nLines = 7 # 5 lines + 2 for borders
		nCols = min(oldWidth, max(len(subText1) + 4, len(subText1) + 2, len(subText2))) # + 2 for borders + 2 for padding

		xMin = (oldWidth - nCols) // 2
		yMin = (oldHeight - nLines) // 2

		alertWin = curses.newwin(nLines, nCols, yMin, xMin)
		
		while True:

			alertWin.clear()

			# All the lines to show
			alertWin.addstr(1, (nCols - 5) // 2, "ALERT", curses.A_BOLD | COLORS["curses"]["alert"])
			if nCols >= len(subText1) + 2:
				alertWin.addstr(2, (nCols - len(subText1)) // 2, subText1)
			else:
				alertWin.addstr(2, (nCols - len(subText1Replacement)) // 2, subText1Replacement)
			alertWin.addstr(3, (nCols - len(subText2)) // 2, subText2, curses.A_ITALIC)
			# Empty line
			alertWin.addstr(5, (nCols - 2) // 3, "No", curses.A_REVERSE*(not response))
			alertWin.addstr(5, (nCols - 3) // 3 * 2, "Yes", curses.A_REVERSE*response)

			alertWin.border() # Border included in the window size.

			alertWin.refresh()

			key = self._stdscr.getch()

			if key == ord('q'):
				response = False
				break
			elif key == ord('n'):
				response = False
				break
			elif key == ord('y'):
				response = True
				break
			elif key == curses.KEY_RIGHT:
				response = True
			elif key == curses.KEY_LEFT:
				response = False
			elif key == curses.KEY_ENTER or key == 10 or key == 13: # ENTER or \n or \r
				break
		
		return response

	
	def _onKeyRight(self) -> None:
		"""
		Defines what happens when the user press the right key.
		"""

		currentFile = os.path.join(self._currentDir, self._files[self._selectedIndex])
		if os.path.isdir(currentFile):
			self._changeDir(currentFile)


	def _onEnterPress(self) -> bool:
		"""
		Defines what happens when the user press the ENTER key.
		Returns the path to the file if a file is selected.
		"""

		currentFile = os.path.join(self._currentDir, self._files[self._selectedIndex])
		if os.path.isdir(currentFile):
			self._changeDir(currentFile)
		elif self._alert(subText2 = self._files[self._selectedIndex]):
			self._chosenFile = currentFile
			return True

		return False


	def _changeDir(self, dirPath: str) -> None:
		"""
		Changes the working directory.
		"""
		self._currentDir = dirPath
		self._selectedIndex = 0
		self._offset = 0
		self._files = sorted(os.listdir(self._currentDir))
		self._logger.debug("Current directory changed : %s", self._currentDir)
		




if __name__ == "__main__":
	# logFile = os.path.join("logs", "FilesManager_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logFile = os.path.join("logs", "FilesManager_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

	handler = logging.FileHandler(logFile)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	
	filesManagerLogger = logging.Logger("FilesManager")
	filesManagerLogger.setLevel(logging.DEBUG)
	filesManagerLogger.addHandler(handler)

	filesManager = FilesManager(logger=filesManagerLogger)
	
	filesManager.start()
	filesManager.join()