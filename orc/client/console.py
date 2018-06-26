#!/usr/bin/env python3
"""orc console"""

# inspired by:
## https://gist.github.com/interstar/3005137
## https://github.com/ruicovelo/async-console/

import cmd
import curses
import curses.textpad
import logging


class Console():

	def __init__(self):
		self.screen = None
		self.output_window = None
		self.prompt_window = None

		self.backlog = []
		self.backlog_offset = 0

		self.initialize()


	def initialize(self):
		self.screen = curses.initscr()
		curses.noecho()
		curses.cbreak()

		(max_y, max_x) = self.screen.getmaxyx()

		# coordinates -- nlines, ncols, y, x
		self.output_window = self.screen.subwin(max_y-2, max_x, 0, 0)
		self.output_window.scrollok(True)

		self.screen.hline(max_y-2, 0, "-", max_x)

		self.prompt_window = self.screen.subwin(1, max_x, max_y-1, 0)
		#self.prompt_window.scrollok(True) #FIX: not working with textpad.Textbox

		self.prompt_textpad = curses.textpad.Textbox(self.prompt_window, insert_mode=True)

		self.screen.refresh()


	def prompt_input(self):
		self.prompt_window.keypad(True)
		tmp = self.prompt_textpad.edit(self.prompt_keystroke)
		self.prompt_window.clear()
		self.prompt_window.refresh()
		return tmp


	def prompt_keystroke(self, key):
		if key == curses.KEY_PPAGE:
			(lines, cols) = self.output_window.getmaxyx()			
			if self.backlog_offset <= len(self.backlog) - lines:
				self.backlog_offset += 1
			self.output_refresh()

		if key == curses.KEY_NPAGE:
			if self.backlog_offset > 0:
				self.backlog_offset -= 1
			self.output_refresh()

		return key


	def add_line(self, line):
	        #TODO: make this thread safe?

		self.backlog.append("%s\n" % line)
		self.output_refresh()


	def output_refresh(self):
		# save cursor
		(cy, cx) = self.prompt_window.getyx()

		self.output_window.erase()
		(output_window_lines, output_window_cols) = self.output_window.getmaxyx()
		tail = max(0, len(self.backlog) - self.backlog_offset)
		head = max(0, tail - output_window_lines)
		for i in range(head, tail):
			self.output_window.addstr(self.backlog[i])
		self.output_window.refresh()

		# restore cursor
		self.prompt_window.move(cy, cx)

	def teardown(self):
		curses.nocbreak()
		curses.echo()
		curses.endwin()


if __name__ == "__main__":
	console = Console()

	for i in range(0,100):
		console.add_line("a"*i+str(i))

	try:
		shutdown = False
		while not shutdown:
			prompt_input = console.prompt_input()
			console.add_line(prompt_input)
	except KeyboardInterrupt:
		pass
	except Exception as e:
		logging.error(e)

	console.teardown()
