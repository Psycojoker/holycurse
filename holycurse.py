#!/usr/bin/python
# -*- coding:Utf-8 -*-

import urwid
import louie
import holygrail

from datetime import datetime, timedelta, date

class MissionWidget(urwid.Text):
    def __init__(self, item):
        if not isinstance(item, holygrail._Mission):
            raise ValueError("Mission widget need a holygrail._Mission object")
        self.item = item
        urwid.Text.__init__(self, self.display(), wrap="clip")

    def display(self):
        def format_timedelta(td):
            if -td.days > 1:
                return "%s days" % ((-td.days) - 1)
            else:
                minutes = td.seconds / 60
                if minutes > 60:
                    return "%s hours" % (minutes  / (60))
                else:
                    return "%s minutes" % (minutes)

        display = ["   "]
        old = date.today() - self.item.created_at
        if (old.days - 1)/7 > 0:
            display.append("."*((old.days - 1)/7))
            display.append(" ")
        display.append("%s" % self.item.description)
        if self.item.quest:
            display.append(" ")
            display.append(("quest", "[%s]" % self.item.quest.description))
        if self.item.due:
            display.append(" - ")
            color = "date left" if self.item.due > datetime.now() else "date late"
            display.append((color, "%s" % format_timedelta(datetime.now() - self.item.due)))

        return display

    def activate(self):
        self.item.toggle()

    def due_today(self, days):
        if days == 1:
            self.item.due_for(datetime.today())
        else:
            self.item.due_for(datetime.today() + timedelta(days))

    def get_realm(self):
        return self.item.realm

class SeparationWidget(urwid.Text):
    def __init__(self, text):
        urwid.Text.__init__(self, ('realm', text.upper()), wrap="clip")

    def activate(self):
        pass

class RealmWidget(SeparationWidget):
    def __init__(self, realm, detailled=False):
        if not isinstance(realm, holygrail._Realm):
            raise ValueError("Realm widget need a holygrail._Realm object")
        text = [('realm', realm.description.upper())]
        if detailled:
            text.append(" (%i)" % len(realm.get_missions()))
        if realm.hide:
            text.append(" - ")
            text.append(("date left", "HIDE"))
        urwid.Text.__init__(self, text, wrap="clip")
        self.realm = realm

    def activate(self):
        self.realm.toggle_hide()

class Window(object):
    def __init__(self):
        self.content = self.fill_main_view()
        self.listbox = urwid.ListBox(self.content)
        self.show_key = urwid.Text("HolyGrail 0.1", wrap='clip')
        self.top = urwid.AttrMap(self.show_key, 'header')
        self.footer = urwid.Pile([urwid.AttrMap(urwid.Text(('header', "I am before command line")), "header"), urwid.Edit("", "")])
        self.frame = urwid.Frame(self.listbox, self.top, self.footer)

        palette = [('header', 'white', 'dark red'),
                   ('reveal focus', 'white', 'dark red', 'standout'),
                   ('realm', 'dark red', '', 'bold'),
                   ('quest', 'light green', '', 'bold'),
                   ('date left', 'black', 'light cyan'),
                   ('date late', 'yellow', 'dark magenta'),
                   ('mission', 'light gray', '')]

        self.loop = urwid.MainLoop(self.frame, palette, input_filter=self.show_all_input, unhandled_input=self.manage_input)
        self.state = "main"
        self.init_signals()
        self.position_chose_realm = 0

    def exit(self):
        raise urwid.ExitMainLoop()

    def run(self):
        self.loop.run()

    def init_signals(self):
        louie.connect(self.update_main_view,               "update_main")
        louie.connect(self.update_realm_view,              "update_realm")

        louie.connect(self.get_command,                    "enter_command")

        louie.connect(self.go_up,                          "k_main")
        louie.connect(self.go_down,                        "j_main")
        louie.connect(self.exit,                           "q_main")
        louie.connect(self.command_line,                   ":_main")
        louie.connect(self.tickle_one_day,                 "+_main")
        louie.connect(self.tickle_3_hours,                 "=_main")
        louie.connect(self.add_mission_to_current_realm,   "a_main")
        louie.connect(self.add_mission_to_default_realm,   "n_main")
        louie.connect(self.add_completed_mission,          "c_main")
        louie.connect(self.toggle_n_recreate,              "R_main")
        louie.connect(self.toggle_mission,                 " _main")
        louie.connect(self.remove_mission,                 "d_main")
        louie.connect(self.due_today,                      "t_main")
        louie.connect(self.due_in_3_days,                  "T_main")
        louie.connect(self.due_this_week,                  "w_main")
        louie.connect(self.no_due,                         "W_main")
        louie.connect(self.add_quest_to_current_mission,   "p_main")
        louie.connect(self.swap_mission_to_quest,          "s_main")
        louie.connect(self.update_realm_view,              "2_main")

        louie.connect(self.update_main_view,               "1_realm")
        louie.connect(self.move_up_realm,                  "K_realm")
        louie.connect(self.move_down_realm,                "J_realm")
        louie.connect(self.go_up_chose_realm,              "k_realm")
        louie.connect(self.go_down_chose_realm,            "j_realm")
        louie.connect(self.toggle_realm_hide,              " _realm")
        louie.connect(self.exit,                           "q_realm")

        louie.connect(self.get_user_input,                 "enter_user_input")

        louie.connect(self.chose_realm,                    "C_main")
        louie.connect(self.go_up_chose_realm,              "k_chose_realm")
        louie.connect(self.go_down_chose_realm,            "j_chose_realm")
        louie.connect(self.return_to_main_view,            "q_chose_realm")
        louie.connect(self.select_realm,                   "enter_chose_realm")

    def select_realm(self):
        if isinstance(self.listbox.get_focus()[0].original_widget, MissionWidget):
            self.listbox.get_focus()[0].original_widget.item.change_realm(self.frame.get_body().get_focus()[0].original_widget.realm.id)
        louie.send("update_main")

    def chose_realm(self):
        realm_list = [RealmWidget(c) for c in holygrail.Grail().list_realms(all_realms=True)]
        realm_list = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in realm_list])
        listbox = urwid.ListBox(realm_list)
        listbox.set_focus(self.position_chose_realm)
        self.frame.set_body(listbox)
        self.state = "chose_realm"

    def return_to_main_view(self):
        self.frame.set_body(self.listbox)
        self.state = "main"

    def update_realm_view(self):
        self.content = self.fill_realm_view()
        self.listbox = urwid.ListBox(self.content)
        self.frame.set_body(self.listbox)
        self.content.set_focus(self.position_chose_realm)
        self.state = "realm"

    def fill_realm_view(self):
        context_view = [RealmWidget(i, detailled=True) for i in holygrail.Grail().list_realms(all_realms=True)]
        return urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in context_view])

    def update_main_view(self):
        self.content = self.fill_main_view()
        self.listbox = urwid.ListBox(self.content)
        self.frame.set_body(self.listbox)
        self.content.set_focus(self.position)
        self.state = "main"

    def fill_main_view(self):
        main_view = []
        for i in holygrail.Grail().super_main_view():
            try:
                main_view.append(RealmWidget(i[0]))
            except:
                main_view.append(SeparationWidget(i[0]))
            for j in i[1]:
                main_view.append(MissionWidget(j))

            main_view.append(urwid.Divider(" "))

        a = 0
        main_view.append(SeparationWidget("LAST COMPLETED MISSIONS"))
        for i in holygrail.Grail().last_completed_missions():
            if a > 5:
                break
            a += 1
            main_view.append(MissionWidget(i))

        to_return = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in main_view[:-1]])
        to_return.set_focus(1)
        return to_return

    def show_all_input(self, input, raw):
        return input

    def manage_input(self, input):
        if self.state == "main":
            self.position = self.frame.get_body().get_focus()[1]
        if not louie.send("%s_%s" % (input, self.state)):
            self.show_key.set_text(input if not isinstance(input, tuple) else "%s, %s, %s, %s" % input)

    def get_command(self):
        self.frame.set_focus('body')
        self.show_key.set_text("User input: " + self.footer.get_focus().edit_text[1:])
        self.footer.get_focus().edit_text = ""
        self.state = "main"

    def due_today(self, days=1):
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, MissionWidget):
            self.frame.get_body().get_focus()[0].original_widget.due_today(days)
        louie.send("update_main")

    def due_in_3_days(self):
        self.due_today(4)

    def due_this_week(self):
        self.due_today(8)

    def tickle_3_hours(self):
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, MissionWidget):
            self.frame.get_body().get_focus()[0].original_widget.item.tickle(datetime.now() + timedelta(hours=3))
        louie.send("update_main")

    def tickle_one_day(self):
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, MissionWidget):
            self.frame.get_body().get_focus()[0].original_widget.item.tickle(datetime.now() + timedelta(days=1))
        louie.send("update_main")

    def no_due(self):
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, MissionWidget):
            self.frame.get_body().get_focus()[0].original_widget.item.due_for(None)
        louie.send("update_main")

    def toggle_realm_hide(self):
        self.frame.get_body().get_focus()[0].original_widget.activate()
        louie.send("update_realm")

    def remove_mission(self):
        self.frame.get_body().get_focus()[0].original_widget.item.remove()
        self.frame.get_body().set_focus(self.position - 1)
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, SeparationWidget):
            self.frame.get_body().set_focus(self.position)
        else:
            self.position -= 1
        louie.send("update_main")

    def toggle_mission(self):
        self.frame.get_body().get_focus()[0].original_widget.activate()
        self.frame.get_body().set_focus(self.position - 1)
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, SeparationWidget):
            self.frame.get_body().set_focus(self.position)
        else:
            self.position -= 1
        louie.send("update_main")

    def toggle_n_recreate(self):
        mission = self.frame.get_body().get_focus()[0].original_widget
        mission.activate()
        holygrail.Grail().add_mission(mission.item.description, realm=mission.get_realm())
        louie.send("update_main")

    def get_user_input(self):
        self.frame.set_focus('body')
        # debug
        self.show_key.set_text("Mission description: " + self.footer.get_focus().edit_text)
        self.user_input = self.footer.get_focus().edit_text
        self.footer.get_focus().edit_text = ""
        self.footer.get_focus().set_caption("")
        self.state = "main"
        louie.send("user_input_done")

    def swap_mission_to_quest(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Mission description: ")
        self.state = "user_input"
        louie.connect(self.get_swap_mission_to_quest, "user_input_done")

    def get_swap_mission_to_quest(self):
        # I got what I want, disconnect
        louie.disconnect(self.get_swap_mission_to_quest, "user_input_done")
        if self.user_input.strip():
            old_mission = self.frame.get_body().get_focus()[0].original_widget.item
            is_quest = holygrail.Grail().get_quest_by_desc(old_mission.description)
            if not is_quest:
                new_quest = holygrail.Grail().add_quest(old_mission.description)
                old_mission.change_quest(new_quest.id)
            else:
                old_mission.change_quest(is_quest[0].id)
            old_mission.rename(self.user_input)
            louie.send("update_main")

    def add_mission_to_current_realm(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Mission description: ")
        self.state = "user_input"
        louie.connect(self.get_current_realm_mission, "user_input_done")

    def add_quest_to_current_mission(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Quest description: ")
        self.state = "user_input"
        louie.connect(self.get_quest_to_current_mission, "user_input_done")

    def get_quest_to_current_mission(self):
        # I got what I want, disconnect
        louie.disconnect(self.get_quest_to_current_mission, "user_input_done")
        if self.user_input.strip():
            is_quest = holygrail.Grail().get_quest_by_desc(self.user_input.strip())
            if not is_quest:
                new_quest = holygrail.Grail().add_quest(self.user_input)
                self.frame.get_body().get_focus()[0].original_widget.item.change_quest(new_quest.id)
            else:
                self.frame.get_body().get_focus()[0].original_widget.item.change_quest(is_quest[0].id)
            louie.send("update_main")

    def add_mission_to_default_realm(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Mission description: ")
        self.state = "user_input"
        louie.connect(self.get_default_realm_mission, "user_input_done")

    def add_completed_mission(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption("Mission description: ")
        self.state = "user_input"
        # this is the receiver
        louie.connect(self.get_completed_mission, "user_input_done")

    def get_completed_mission(self):
        # I got what I want, disconnect
        louie.disconnect(self.get_completed_mission, "user_input_done")
        if self.user_input.strip():
            new_mission = holygrail.Grail().add_mission(self.user_input)
            new_mission.toggle()

    def get_default_realm_mission(self):
        louie.disconnect(self.get_current_realm_mission, "user_input_done")
        if self.user_input.strip():
            self.position += 1
            holygrail.Grail().add_mission(self.user_input)
            louie.send("update_main")

    def get_current_realm_mission(self):
        louie.disconnect(self.get_current_realm_mission, "user_input_done")
        if self.user_input.strip():
            self.position += 1
            new_mission_realm = self.frame.get_body().get_focus()[0].original_widget.get_realm()
            holygrail.Grail().add_mission(self.user_input, realm=new_mission_realm)
            louie.send("update_main")

    def command_line(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().insert_text(":")
        self.state = "command"

    def move_down_realm(self):
        if self.position_chose_realm < len(holygrail.Grail().list_realms(all_realms=True)):
            realm = self.frame.get_body().get_focus()[0].original_widget.realm
            a = realm.position
            realm.change_position(realm.position + 1)
            self.position_chose_realm += 1
            louie.send("update_realm")

    def move_up_realm(self):
        if self.position_chose_realm > 0:
            realm = self.frame.get_body().get_focus()[0].original_widget.realm
            realm.change_position(realm.position - 1)
            self.position_chose_realm -= 1
            louie.send("update_realm")

    def go_down_chose_realm(self):
        # really unoptimised if
        if self.position_chose_realm < len(holygrail.Grail().list_realms(all_realms=True)):
            self.frame.get_body().set_focus(self.position_chose_realm + 1)
            self.position_chose_realm += 1
            self.show_key.set_text("Current: %s" % self.frame.get_body().get_focus()[0].original_widget)

    def go_up_chose_realm(self):
        if self.position_chose_realm > 0:
            self.frame.get_body().set_focus(self.position_chose_realm - 1)
            self.position_chose_realm -= 1
            self.show_key.set_text("Current: %s" % self.frame.get_body().get_focus()[0].original_widget)

    def go_down(self):
        self.frame.get_body().set_focus(self.position + 1)
        self.show_key.set_text("Current: %s" % self.frame.get_body().get_focus()[0].original_widget)
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, urwid.Divider):
            self.frame.get_body().set_focus(self.position + 3)
            self.show_key.set_text("Gotcha !")

    def go_up(self):
        if self.position > 1:
            self.frame.get_body().set_focus(self.position - 1)
            self.show_key.set_text("Current: %s" % self.frame.get_body().get_focus()[0].original_widget)
            if isinstance(self.frame.get_body().get_focus()[0].original_widget, SeparationWidget):
                self.frame.get_body().set_focus(self.position - 3)
                self.show_key.set_text("Gotcha !")

if __name__ == "__main__":
    Window().run()
