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
		"path" : 2
	},
	# The objects used to display some text. Defined here for more clarity
	"curses" : {
		"text" : None,
		"file" : None,
		"dir" : None,
		"path" : None
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


	def run(self) -> None:
		"""
		This function is almost a copy/paste of the curses.wrapper function (see https://github.com/python/cpython/blob/3.12/Lib/curses/__init__.py).
		Doing this allows the curses environment to be used inside of a threaded class.
		It only initializes the curses envrionment. The main function is _mainLoop.
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

		self._mainLoop()


	def _mainLoop(self) -> None:
		"""
		The mainloop of the curses envrionment.
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
			elif key == curses.KEY_DOWN and self._selectedIndex < len(self._files) - 1: # Navigate threw the tree
				self._selectedIndex += 1
			elif key == curses.KEY_LEFT:
				self._changeDir(os.path.dirname(self._currentDir))
			elif key == curses.KEY_RIGHT:
				self._onEnterPress()
			elif key == curses.KEY_ENTER or key == 10 or key == 13: # ENTER or \n or \r
				self._onEnterPress()
			# TODO : one key to press to enter the full path with the keyboard

			self._display()

		# End of the file manager
		self._logger.info("Ending files manager")
		# Set everything back to normal
		self._stdscr.keypad(0)
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
		curses.init_pair(COLORS["index"]["dir"], curses.COLOR_CYAN, curses.COLOR_BLACK) # Directory
		curses.init_pair(COLORS["index"]["path"], curses.COLOR_RED, curses.COLOR_BLACK) # Path

		# Match the color object on the color pair
		# These are the objects used when displaying some text
		COLORS["curses"]["text"] = curses.color_pair(COLORS["index"]["text"])
		COLORS["curses"]["file"] = curses.color_pair(COLORS["index"]["file"])
		COLORS["curses"]["dir"] = curses.color_pair(COLORS["index"]["dir"])
		COLORS["curses"]["path"] = curses.color_pair(COLORS["index"]["path"])

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

		# Header
		headerLines = 2
		self._stdscr.addstr(0, 0, "path :", COLORS["curses"]["text"])
		# If too large for the screen (size of "path : ..." + 1), shortens the path
		if (len(self._currentDir)) < width-11:
			self._stdscr.addstr(0, 7, self._currentDir, COLORS["curses"]["path"])
		else:
			self._stdscr.addstr(0, 7, "...{}".format(self._currentDir[len(self._currentDir)-width+11:]), COLORS["curses"]["path"])
		self._drawHorizontalLine(1)

		# Footer
		footerLines = 2
		self._drawHorizontalLine(height-2)
		footer = "[q] Quit    [<] Go out    [>] Go in    [ENTER] Send file"
		if width > 56: # len(footer) 
			self._stdscr.addstr(height-1, 0, "[q] Quit    [<] Go out    [>] Go in    [ENTER] Send file", COLORS["curses"]["text"])
		else:
			self._stdscr.addstr(height-1, 0, "[q]    [<]    [>]    [ENTER]", COLORS["curses"]["text"])

		# Main
		# TODO : scroll the list if the cursor is in the bottom of the list
		for idx, file in enumerate(self._files):
			if idx >= height - (headerLines + footerLines):
				continue
			currentFile = os.path.join(self._currentDir, file)
			if os.path.isdir(currentFile):
				self._stdscr.addstr(idx + headerLines, 0, file, COLORS["curses"]["dir"] | curses.A_BOLD | curses.A_REVERSE*(idx==self._selectedIndex))
			else:
				self._stdscr.addstr(idx + headerLines, 0, file, COLORS["curses"]["file"] | curses.A_REVERSE*(idx==self._selectedIndex))

		self._stdscr.refresh()
	

	def _alert(self, text) -> bool:
		"""
		This function is used to display an alert in the center of the screen
		"""

		response = False

		nLines = len(text) + 8 # + 2 (borders) + 2*3 for padding
		nCols = 4
		oldHeight, oldWidth = self._stdscr.getmaxyx()

		xMin = (oldWidth - nCols) // 2
		yMin = (oldHeight - nLines) // 2

		alertWin = curses.newwin(nLines, nCols, yMin, xMin)
		
		while True:

			alertWin.clear()

			for i in range(nLines):
				alertWin.addstr(i, 0, " "*(nCols-1), curses.A_REVERSE)

			alertWin.border() # Border included in the window size. Example for 3x2 : +-+
							  # 													  +-+

			alertWin.refresh()

			key = self._stdscr.getch()

			if key == ord('q'):
				break
		
		return response

		
	def _onEnterPress(self) -> None:
		"""
		Defines what happens when the user press the ENTER key.
		"""
		
		if self._files[self._selectedIndex] == ".":
			self._files = [".", ".."] + sorted(os.listdir(self._currentDir))
		elif self._files[self._selectedIndex] == "..":
			self._changeDir(os.path.dirname(self._currentDir))
		else:
			currentFile = os.path.join(self._currentDir, self._files[self._selectedIndex])
			if os.path.isdir(currentFile):
				self._changeDir(currentFile)


	def _changeDir(self, dirPath: str) -> None:
		"""
		Changes the working directory.
		"""
		self._currentDir = dirPath
		self._selectedIndex = 0
		self._files = sorted(os.listdir(self._currentDir))
		self._logger.debug("Current directory changed : %s", self._currentDir)
		




if __name__ == "__main__":
	# logsFiles = os.path.join("logs", "FilesManager_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logsFiles = os.path.join("logs", "FilesManager_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

	handler = logging.FileHandler(logsFiles)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	
	filesManagerLogger = logging.Logger("FilesManager")
	filesManagerLogger.setLevel(logging.DEBUG)
	filesManagerLogger.addHandler(handler)

	filesManager = FilesManager(logger=filesManagerLogger)
	
	filesManager.start()
	filesManager.join()