#!/usr/bin/env python3


import cmd
import curses
import logging
import npyscreen
import time


class FormedActionController(npyscreen.ActionControllerSimple):
	def create(self):
		self.add_action("quit", self.do_quit, live=False)
		self.add_action(".*", self.do_command, live=False)

	def do_quit(self, command_line, widget_proxy, live):
		raise KeyboardInterrupt

	def do_command(self, command_line, widget_proxy, live):
		# here might be some handling of ui.Formed command vs mastershell commands routing
		self.parent.parentApp.command_handler(command_line)



class FormedForm(npyscreen.fmForm.FormBaseNew):
	BLANK_LINES_BASE = 0

	NETSTAT_WIDGET_CLASS = npyscreen.Pager
	NETSTAT_WIDGET_HEIGHT = 5

	MAIN_WIDGET_CLASS = npyscreen.BufferPager
	MAIN_WIDGET_CLASS_START_LINE = NETSTAT_WIDGET_HEIGHT+1

	STATUS_WIDGET_CLASS = npyscreen.wgtextbox.Textfield
	STATUS_WIDGET_X_OFFSET = 5

	ACTION_CONTROLLER = FormedActionController
	COMMAND_WIDGET_CLASS = npyscreen.fmFormMuttActive.TextCommandBox


	def __init__(self, cycle_widgets=True, *args, **kwargs):

		self.action_controller = self.ACTION_CONTROLLER(parent=self)
		super(FormedForm, self).__init__(cycle_widgets=cycle_widgets, *args, **kwargs)


	def draw_form(self):
		MAXY, MAXX = self.lines, self.columns
		self.curses_pad.hline(self.NETSTAT_WIDGET_HEIGHT, 0, curses.ACS_HLINE, MAXX-1)
		self.curses_pad.hline(MAXY-2-self.BLANK_LINES_BASE, 0, curses.ACS_HLINE, MAXX-1)


	def create(self):
		MAXY, MAXX = self.lines, self.columns

		self.wNetstat = self.add(self.NETSTAT_WIDGET_CLASS, rely=0, relx=0, height=self.NETSTAT_WIDGET_HEIGHT, editable=False)

		self.wStatus1 = self.add(self.STATUS_WIDGET_CLASS, rely=self.NETSTAT_WIDGET_HEIGHT, relx=self.STATUS_WIDGET_X_OFFSET, editable=False)
		self.wStatus1.value = "status 1"
		self.wStatus1.important = True

		self.wMain = self.add(self.MAIN_WIDGET_CLASS, rely=self.MAIN_WIDGET_CLASS_START_LINE, relx=0, max_height=-2)

		self.wStatus2 = self.add(self.STATUS_WIDGET_CLASS, rely=MAXY-2-self.BLANK_LINES_BASE, relx=self.STATUS_WIDGET_X_OFFSET, editable=False)
		self.wStatus2.value = "status 2"
		self.wStatus2.important = True

		self.wCommand = self.add(self.COMMAND_WIDGET_CLASS, rely=MAXY-1-self.BLANK_LINES_BASE, relx=0, history=True)

		self.nextrely = 2


	def h_display(self, input):
		super(FormedForm, self).h_display(input)
		if hasattr(self, 'wMain'):
			if not self.wMain.hidden:
				self.wMain.display()


	def resize(self):
		super(FormedForm, self).resize()
		MAXY, MAXX = self.lines, self.columns
		self.wStatus1.rely = self.NETSTAT_WIDGET_HEIGHT
		self.wStatus2.rely = MAXY-2-self.BLANK_LINES_BASE
		self.wCommand.rely = MAXY-1-self.BLANK_LINES_BASE



class Formed(npyscreen.NPSAppManaged):
	def __init__(self, command_handler, *args, **kwargs):
		super(Formed, self).__init__(*args, **kwargs)

		# handler for passing command from ui commandline to mastershell
		self.command_handler = command_handler

		# internal ui data
		self.netstat_data = {}


	def onStart(self):
		#npyscreen.setTheme(npyscreen.Themes.TransparentThemeDarkText)
		self.form = self.addForm('MAIN', FormedForm)
		curses.mousemask(0)


	def wmain_add_line(self, line):
		self.form.wMain.buffer([line], scroll_end=True)
		self.form.wMain.display()


	def wnetstat_update(self, node, data):
		self.netstat_data[node] = data
		self.form.wNetstat.values = sorted(["[%20s] %s" % (node, data) for node, data in self.netstat_data.items()])
		self.form.wNetstat.display()


	## application interface
	def handle_message(self, message):
		if message["Type"] == "netstat":
			self.wnetstat_update(message["Node"], message["Message"])
		else:
			self.wmain_add_line("[%20s] %s" % (message["Node"], message["Message"]))



class Listener(object):
	def __init__(self):
		self.log = logging.getLogger()


	def run(self):
		while True:
			time.sleep(60)


	def handle_message(self, message):
		self.log.info("[%20s] %10s > %s", message["Node"], message["Type"], message["Message"])



class Commander(cmd.Cmd):
	prompt = "(orc) "

	def __init__(self, command_handler, *args, **kwargs):
		super(Commander, self).__init__(*args, **kwargs)
		self.command_handler = command_handler
		self.log = logging.getLogger()
	
	def default(self, arg):
		return self.command_handler(arg)

	def do_quit(self, arg):
		return True

	def do_EOF(self, arg):
		return True


	def run(self):
		self.cmdloop()

	def handle_message(self, message):
		pass
