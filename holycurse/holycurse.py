import urwid
import louie

from controler import State
from models import MainViewList, RealmList, HelpList, ChooseRealmList

class HolyCurse(object):

    def __init__(self):
        self.state = State(set(("main", "command", "realm", "user_input",
                                "chose_realm", "user_input_main",
                                "user_input_realm", "help")), "main")

        self.frame = urwid.Frame(urwid.Text(""))

        self.main_view = MainViewList(self.frame)
        self.main_view.get_main_view()
        self.realm_view = RealmList(self.frame)
        self.choose_realm = ChooseRealmList(self.frame, self.main_view)
        self.help = HelpList(self.frame, self.state)

        self.header = urwid.Text("HolyGrail 0.1", wrap='clip')
        self.footer = urwid.Pile([urwid.AttrMap(urwid.Text(('header', 'To see help press "?"')), "header"), urwid.Edit("", "")])
        self.frame.set_header(urwid.AttrMap(self.header, 'header'))
        self.frame.set_footer(self.footer)

        palette = [('header', 'white', 'dark red'),
                   ('reveal focus', 'white', 'dark red', 'standout'),
                   ('realm', 'dark red', '', 'bold'),
                   ('quest', 'light green', '', 'bold'),
                   ('old', 'yellow', '', 'bold'),
                   ('date left', 'black', 'light cyan'),
                   ('date late', 'yellow', 'dark magenta'),
                   ('unactive', 'light blue', ''),
                   ('mission', 'light gray', '')]

        self.loop = urwid.MainLoop(self.frame, palette,
                                   input_filter=self.show_all_input,
                                   unhandled_input=self.manage_input)
        self.init_signals()

    def get_state(self):
        return louie.send("get state")[0][1]

    def exit(self):
        raise urwid.ExitMainLoop()

    def run(self):
        self.loop.run()

    def init_signals(self):
        self.main_view.init_signals()
        self.realm_view.init_signals()
        self.choose_realm.init_signals()
        self.help.init_signals()

        louie.connect(self.get_command,                    "enter_command")

        louie.connect(self.get_user_input,                 "enter_user_input")

    def show_all_input(self, input, raw):
        return input

    def manage_input(self, input):
        if self.get_state() == "main":
            self.main_view.position = self.frame.get_body().get_focus()[1]
        louie.send("%s_%s" % (input, self.get_state()))

    def get_command(self):
        self.frame.set_focus('body')
        self.footer.get_focus().edit_text = ""
        louie.send("set state", None, "main")

    def get_user_input(self):
        self.frame.set_focus('body')
        # debug
        self.user_input = self.footer.get_focus().edit_text
        self.footer.get_focus().edit_text = ""
        self.footer.get_focus().set_caption("")
        louie.send("set state", None, "main")
        louie.send("user_input_done")
