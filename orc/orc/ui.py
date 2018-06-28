"""orc ui module"""


import cmd
import curses
import logging
import npyscreen
import time


class FormedActionController(npyscreen.ActionControllerSimple):
	"""action controller, used to pass commands from main form commandline/textcommandbox"""

	def create(self):
		self.add_action("quit", self.do_quit, live=False)
		self.add_action(".*", self.do_command, live=False)

	def do_quit(self, command_line, widget_proxy, live): # pylint: disable=unused-argument,no-self-use
		"""emit shutdown"""

		raise KeyboardInterrupt

	def do_command(self, command_line, widget_proxy, live): # pylint: disable=unused-argument
		"""process entered command"""

		# here might be some handling of ui.Formed command vs mastershell commands routing
		self.parent.parentApp.command_handler(command_line)



class FormedForm(npyscreen.fmForm.FormBaseNew): # pylint: disable=too-many-ancestors
	"""main app form"""

	BLANK_LINES_BASE = 0

	NETSTAT_WIDGET_CLASS = npyscreen.Pager
	NETSTAT_WIDGET_HEIGHT = 5

	MAIN_WIDGET_CLASS = npyscreen.BufferPager
	MAIN_WIDGET_CLASS_START_LINE = NETSTAT_WIDGET_HEIGHT+1

	STATUS_WIDGET_CLASS = npyscreen.wgtextbox.Textfield
	STATUS_WIDGET_X_OFFSET = 5

	ACTION_CONTROLLER = FormedActionController
	COMMAND_WIDGET_CLASS = npyscreen.fmFormMuttActive.TextCommandBox


	def __init__(self, *args, **kwargs):
		self.action_controller = self.ACTION_CONTROLLER(parent=self)
		super(FormedForm, self).__init__(*args, **kwargs)


	def draw_form(self):
		maxy, maxx = self.lines, self.columns
		self.curses_pad.hline(self.NETSTAT_WIDGET_HEIGHT, 0, curses.ACS_HLINE, maxx-1)
		self.curses_pad.hline(maxy-2-self.BLANK_LINES_BASE, 0, curses.ACS_HLINE, maxx-1)


	def create(self):
		maxy = self.lines

		self.w_netstat = self.add(self.NETSTAT_WIDGET_CLASS, rely=0, relx=0, height=self.NETSTAT_WIDGET_HEIGHT, editable=False)

		self.w_status1 = self.add(self.STATUS_WIDGET_CLASS, rely=self.NETSTAT_WIDGET_HEIGHT, relx=self.STATUS_WIDGET_X_OFFSET, editable=False)
		self.w_status1.value = "status 1"
		self.w_status1.important = True

		self.w_main = self.add(self.MAIN_WIDGET_CLASS, rely=self.MAIN_WIDGET_CLASS_START_LINE, relx=0, max_height=-2)

		self.w_status2 = self.add(self.STATUS_WIDGET_CLASS, rely=maxy-2-self.BLANK_LINES_BASE, relx=self.STATUS_WIDGET_X_OFFSET, editable=False)
		self.w_status2.value = "status 2"
		self.w_status2.important = True

		self.w_command = self.add(self.COMMAND_WIDGET_CLASS, rely=maxy-1-self.BLANK_LINES_BASE, relx=0, history=True)

		self.nextrely = 2


	def h_display(self, inputx): # pylint: disable=arguments-differ
		super(FormedForm, self).h_display(inputx)
		if hasattr(self, "w_main"):
			if not self.w_main.hidden:
				self.w_main.display()


	def resize(self):
		super(FormedForm, self).resize()
		maxy = self.lines
		self.w_status1.rely = self.NETSTAT_WIDGET_HEIGHT
		self.w_status2.rely = maxy-2-self.BLANK_LINES_BASE
		self.w_command.rely = maxy-1-self.BLANK_LINES_BASE



class Formed(npyscreen.NPSAppManaged):
	"""main formed application"""

	def __init__(self, command_handler, *args, **kwargs):
		super(Formed, self).__init__(*args, **kwargs)
		self.command_handler = command_handler
		self.form = None
		self.netstat_data = {}


	def onStart(self):
		#npyscreen.setTheme(npyscreen.Themes.TransparentThemeDarkText)
		self.form = self.addForm('MAIN', FormedForm)
		curses.mousemask(0)


	def wmain_add_line(self, line):
		"""add output line to main console widget"""

		self.form.w_main.buffer([line], scroll_end=True)
		self.form.w_main.display()


	def wnetstat_update(self, node, data):
		"""update netstat data"""

		self.netstat_data[node] = data
		self.form.w_netstat.values = sorted(["[%20s] %s" % (node, data) for node, data in self.netstat_data.items()])
		self.form.w_netstat.display()


	## application interface
	def handle_message(self, message):
		"""handle message, called from outr app"""

		if message["Type"] == "netstat":
			self.wnetstat_update(message["Node"], message["Message"])
		else:
			self.wmain_add_line("[%20s] %s" % (message["Node"], message["Message"]))



class Listener(object):
	"""listener ui class"""

	def __init__(self):
		self.log = logging.getLogger()


	## application interface
	def run(self): # pylint: disable=no-self-use
		"""class main"""

		while True:
			time.sleep(60)


	def handle_message(self, message):
		"""handle message, called from outer app"""

		self.log.info("[%20s] %10s > %s", message["Node"], message["Type"], message["Message"])



class Commander(cmd.Cmd):
	"""commander ui class"""

	prompt = "(orc) "

	def __init__(self, command_handler, *args, **kwargs):
		super(Commander, self).__init__(*args, **kwargs)
		self.command_handler = command_handler
		self.log = logging.getLogger()

	def default(self, line):
		return self.command_handler(line)

	def do_quit(self, arg): # pylint: disable=unused-argument,no-self-use
		"""quit"""

		return True

	def do_EOF(self, arg): # pylint: disable=unused-argument,no-self-use,invalid-name
		"""quit"""

		return True


	## application interface
	def run(self):
		"""class main"""

		self.cmdloop()


	def handle_message(self, message): # pylint: disable=unused-argument,no-self-use
		"""handle message, called from outer app"""

		pass
