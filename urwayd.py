#!/usr/bin/python
# -*- coding:Utf-8 -*-

import urwid
import louie
import tdd

from datetime import datetime, timedelta

class ItemWidget(urwid.Text):
    def __init__(self, item):
        if not isinstance(item, tdd._Item):
            raise ValueError("Item widget need a tdd._Item object")
        urwid.Text.__init__(self, ('item', "    " + item.description), wrap="clip")
        self.item = item

    def activate(self):
        pass

    def get_context(self):
        return self.item.context

class TodoWidget(ItemWidget):
    def __init__(self, item):
        if not isinstance(item, tdd._Todo):
            raise ValueError("Todo widget need a tdd._Item object")
        self.item = item
        urwid.Text.__init__(self, self.display(), wrap="clip")

    def display(self):
        display = "    %s" % self.item.description
        if self.item.due:
            if self.item.due > datetime.now():
                display += " - %s left" % (datetime.now() - self.item.due)
            else:
                display += " - %s late" % (datetime.now() - self.item.due)

        return display

    def activate(self):
        self.item.toggle()

    def due_today(self, days):
        if days == 1:
            self.item.due_for(datetime.today())
        else:
            self.item.due_for(datetime.today() + timedelta(days))

class ContextWidget(urwid.Text):
    def __init__(self, context):
        if not isinstance(context, tdd._Context):
            raise ValueError("Context widget need a tdd._Context object")
        urwid.Text.__init__(self, ('context', context.description.upper()), wrap="clip")
        self.context = context

    def activate(self):
        pass

class Window(object):
    def __init__(self):
        self.content = self.fill_main_view()
        self.listbox = urwid.ListBox(self.content)
        self.show_key = urwid.Text("Toudoudone 0.1", wrap='clip')
        self.top = urwid.AttrMap(self.show_key, 'header')
        self.footer = urwid.Pile([urwid.AttrMap(urwid.Text(('header', "I am before command line")), "header"), urwid.Edit("", "")])
        self.frame = urwid.Frame(self.listbox, self.top, self.footer)

        palette = [('header', 'white', 'dark red'),
                   ('reveal focus', 'white', 'dark red', 'standout'),
                   ('context', 'dark red', '', 'bold'),
                   ('item', 'light cyan', ''),
                   ('todo', 'light gray', '')]

        self.loop = urwid.MainLoop(self.frame, palette, input_filter=self.show_all_input, unhandled_input=self.manage_input)
        self.state = "main"
        self.init_signals()

    def exit(self):
        raise urwid.ExitMainLoop()

    def init_signals(self):
        louie.connect(self.go_up,                       "k_main")
        louie.connect(self.go_down,                     "j_main")
        louie.connect(self.exit,                        "q_main")
        louie.connect(self.command_line,                ":_main")
        louie.connect(self.tickle_one_day,              "+_main")
        louie.connect(self.at_todo_to_current_context,  "a_main")
        louie.connect(self.toggle_n_recreate,           "R_main")
        louie.connect(self.toggle_todo,                 " _main")
        louie.connect(self.due_today,                   "t_main")
        louie.connect(self.due_today,                   "T_main")
        louie.connect(self.due_today,                   "w_main")
        louie.connect(self.update_main_view,            "update_main")
        louie.connect(self.get_add_todo,                "enter_add todo")
        louie.connect(self.get_command,                 "enter_command")

    def update_main_view(self):
        self.content = self.fill_main_view()
        self.listbox = urwid.ListBox(self.content)
        self.frame.set_body(self.listbox)
        # will fail with divider
        self.content.set_focus(self.position)

    def fill_main_view(self):
        main_view = []
        for i in tdd.TodoDB().super_main_view():
            try:
                main_view.append(ContextWidget(i[0]))
            except:
                main_view.append(urwid.Text(('context', i[0].upper()), wrap="clip"))
            for j in i[1]:
                main_view.append(ItemWidget(j))
            for j in i[2]:
                #main_view.append(urwid.Columns([('fixed', 4, urwid.Divider("    ")), TodoWidget(j), urwid.Text("blod")]))
                main_view.append(TodoWidget(j))

            main_view.append(urwid.Divider(" "))

        a = 0
        main_view.append(urwid.Text(('context', "LAST COMPLETED TODOS"), wrap="clip"))
        for i in tdd.TodoDB().last_completed_todos():
            if a > 5:
                break
            a += 1
            main_view.append(TodoWidget(i))

        to_return = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in main_view[:-1]])
        to_return.set_focus(1)
        return to_return

    def run(self):
        self.loop.run()

    def show_all_input(self, input, raw):
        return input

    def manage_input(self, input):
        self.position = self.content.get_focus()[1]
        louie.send("%s_%s" % (input, self.state))
        self.show_key.set_text(input)

    def get_command(self):
        self.frame.set_focus('body')
        self.show_key.set_text("User input: " + self.footer.get_focus().edit_text[1:])
        self.footer.get_focus().edit_text = ""
        self.state = "main"

    def get_add_todo(self):
        self.frame.set_focus('body')
        self.show_key.set_text("Todo description: " + self.footer.get_focus().edit_text)
        todo_description = self.footer.get_focus().edit_text
        context = self.content.get_focus()[0].original_widget.get_context()
        if todo_description.strip():
            tdd.TodoDB().add_todo(todo_description, context=context)
        self.footer.get_focus().edit_text = ""
        self.footer.get_focus().set_caption("")
        louie.send("update_main")
        self.state = "main"

    def due_today(self, days=1):
        if isinstance(self.content.get_focus()[0].original_widget, TodoWidget):
            self.content.get_focus()[0].original_widget.due_today(days)
        louie.send("update_main")

    def tickle_one_day(self):
        if isinstance(self.content.get_focus()[0].original_widget, TodoWidget):
            self.content.get_focus()[0].original_widget.item.tickle(datetime.now() + timedelta(days=1))
        louie.send("update_main")

    def toggle_todo(self):
        self.content.get_focus()[0].original_widget.activate()
        louie.send("update_main")

    def toggle_n_recreate(self):
        todo = self.content.get_focus()[0].original_widget
        todo.activate()
        tdd.TodoDB().add_todo(todo.item.description, context=todo.get_context())
        louie.send("update_main")

    def at_todo_to_current_context(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Todo description: ")
        self.state = "add todo"

    def command_line(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().insert_text(":")
        self.state = "command"

    def go_down(self):
        self.content.set_focus(self.position + 1)
        self.show_key.set_text("Current: %s" % self.content.get_focus()[0].original_widget)
        if isinstance(self.content.get_focus()[0].original_widget, urwid.Divider):
            self.content.set_focus(self.position + 3)
            self.show_key.set_text("Gotcha !")

    def go_up(self):
        if self.position > 1:
            self.content.set_focus(self.position - 1)
            self.show_key.set_text("Current: %s" % self.content.get_focus()[0].original_widget)
            if isinstance(self.content.get_focus()[0].original_widget, ContextWidget):
                self.content.set_focus(self.position - 3)
                self.show_key.set_text("Gotcha !")

if __name__ == "__main__":
    Window().run()
