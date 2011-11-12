import louie
import urwid

commands = {}

def command(func, key, mode, doc):
    louie.connect(func, "%s_%s" % (key, mode))
    if doc:
        if commands.has_key(mode):
            commands[mode].append((key, doc))
        else:
            commands[mode] = [(key, doc)]

class State(object):
    def __init__(self, states_set, state):
        self.avalaible_states = states_set
        self.state = None
        self.set_state(state)
        louie.connect(self.set_state, "set state")
        louie.connect(self.get,       "get state")

    def set_state(self, state):
        if state not in self.avalaible_states:
            raise ValueError("Unknow state: %s, should be one of those %s" % (state, self.avalaible_states))
        self.state = state

    def get(self):
        return self.state

def get_documentations():
    for i in commands.keys():
        yield urwid.AttrMap(urwid.Text(('header', "  %s" % i)), "header")
        for a, b in commands[i]:
            yield urwid.Text("%s : %s" % (a, b))
        yield urwid.Divider(" ")
    yield urwid.Text("For more informations/repport bugs go to http://blog.worlddomination.be/holycurse")
    yield urwid.Text("Thanks for using this software !")
