#!/usr/bin/python
# -*- coding:Utf-8 -*-

import urwid
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
        #self.init_signals()

    #def init_signals(self):
        #signal.

    def update_main_view(self, position):
        self.content = self.fill_main_view()
        self.listbox = urwid.ListBox(self.content)
        self.frame.set_body(self.listbox)
        # will fail with divider
        self.content.set_focus(position)

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
        position = self.content.get_focus()[1]
        if self.frame.focus_part == "footer":
            # TODO refatorer ça
            if input == "enter" and self.state == "add todo":
                self.frame.set_focus('body')
                self.show_key.set_text("Todo description: " + self.footer.get_focus().edit_text)
                todo_description = self.footer.get_focus().edit_text
                context = self.content.get_focus()[0].original_widget.get_context()
                if todo_description.strip():
                    tdd.TodoDB().add_todo(todo_description, context=context)
                self.footer.get_focus().edit_text = ""
                self.footer.get_focus().set_caption("")
                self.update_main_view(position)
                self.state = "main"

            elif input == "enter" and self.state == "command":
                self.frame.set_focus('body')
                self.show_key.set_text("User input: " + self.footer.get_focus().edit_text[1:])
                self.footer.get_focus().edit_text = ""
                self.state = "main"

        else:
            if input == 'k' and position > 1:
                self.go_up(position)

            elif input == 'j':
                self.go_down(position)

            elif input == 'q':
                raise urwid.ExitMainLoop()

            elif input == ':':
                self.command_line()

            elif input == "+":
                self.tickle_one_day(position)

            elif input == "a":
                self.at_todo_to_current_context()

            elif input == "é":
                self.frame.set_body(self.listbox)

            elif input == "&":
                self.frame.set_body(urwid.ListBox(urwid.SimpleListWalker([urwid.Text("wééé, change ton body")])))

            elif input == "R":
                self.toggle_n_recreate(position)

            elif input == " ":
                self.toggle_todo(position)

            elif input == "t":
                self.due_today(position)

            elif input == "T":
                self.due_today(position, 4)

            elif input == "w":
                self.due_today(position, 8)

            else:
                self.show_key.set_text(input)

    def due_today(self, position, days=1):
        if isinstance(self.content.get_focus()[0].original_widget, TodoWidget):
            self.content.get_focus()[0].original_widget.due_today(days)
        self.update_main_view(position)

    def tickle_one_day(self, position):
        if isinstance(self.content.get_focus()[0].original_widget, TodoWidget):
            self.content.get_focus()[0].original_widget.item.tickle(datetime.now() + timedelta(days=1))
        self.update_main_view(position)

    def toggle_todo(self, position):
        self.content.get_focus()[0].original_widget.activate()
        self.update_main_view(position)

    def toggle_n_recreate(self, position):
        todo = self.content.get_focus()[0].original_widget
        todo.activate()
        tdd.TodoDB().add_todo(todo.item.description, context=todo.get_context())
        self.update_main_view(position)

    def at_todo_to_current_context(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Todo description: ")
        self.state = "add todo"

    def command_line(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().insert_text(":")
        self.state = "command"

    def go_down(self, position):
        self.content.set_focus(position + 1)
        self.show_key.set_text("Current: %s" % self.content.get_focus()[0].original_widget)
        if isinstance(self.content.get_focus()[0].original_widget, urwid.Divider):
            self.content.set_focus(position + 3)
            self.show_key.set_text("Gotcha !")

    def go_up(self, position):
        self.content.set_focus(position - 1)
        self.show_key.set_text("Current: %s" % self.content.get_focus()[0].original_widget)
        if isinstance(self.content.get_focus()[0].original_widget, ContextWidget):
            self.content.set_focus(position - 3)
            self.show_key.set_text("Gotcha !")

if __name__ == "__main__":
    Window().run()
