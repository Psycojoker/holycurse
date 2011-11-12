#!/usr/bin/python
# -*- coding:Utf-8 -*-

import urwid
import louie
import holygrail

from datetime import datetime, timedelta

from controler import commands, command, State
from widgets import MissionWidget, SeparationWidget, RealmWidget, MyListBox
from shortcuts import cant_be_call_on_empty_mainview, disconnect, update_main, toggle_current_mission, have_input, update_current_item, update_realm

def get_documentations():
    for i in commands.keys():
        yield urwid.AttrMap(urwid.Text(('header', "  %s" % i)), "header")
        for a, b in commands[i]:
            yield urwid.Text("%s : %s" % (a, b))
        yield urwid.Divider(" ")
    yield urwid.Text("For more informations/repport bugs go to http://blog.worlddomination.be/holycurse")
    yield urwid.Text("Thanks for using this software !")

class HelpList(object):
    def __init__(self, frame, state):
        self.frame = frame
        self.state = state
        self.position = 0
        self.init_signals()
        self.previous_state = None

    def init_signals(self):
        command(self.exit,                  "q", "help", "return to previous view")
        command(self.go_down,               "j" ,"help", "move the cursor down")
        command(self.go_up,                 "k", "help", "move the cursor up")
        command(self.go_down,               "down" ,"help", "move the cursor down")
        command(self.go_up,                 "up", "help", "move the cursor up")
        command(self.go_down,               "down" ,"help", "move the cursor down")
        command(self.go_up,                 "up", "help", "move the cursor up")

        louie.connect(self.fill_list, "help")

    def exit(self):
        louie.send("update_%s" % self.previous_state)

    def fill_list(self):
        self.content = [i for i in get_documentations()]
        self.content = urwid.SimpleListWalker([urwid.AttrMap(i, None, 'reveal focus') for i in self.content])
        self.frame.set_body(MyListBox(self.content))
        if self.state.get() != "help":
            self.previous_state = self.state.get()
        self.state.set_state("help")

    def go_down(self):
        if self.position < (len(self.content) - 1):
            self.position += 1
            self.frame.get_body().set_focus(self.position)

    def go_up(self):
        if self.position > 0:
            self.position -= 1
            self.frame.get_body().set_focus(self.position)

class MainViewList(object):
    def __init__(self, frame):
        self.position = 0
        self.frame = frame
        self.unactive = True
        self.grail = holygrail.Grail()

    def init_signals(self):
        louie.connect(self.update_main_view,                          "update_main")

        command(self.go_up,                                     "k", "main", "go up in the main view")
        command(self.go_down,                                   "j", "main", "go down in the main view")
        command(self.go_up,                                     "up", "main", "go up in the main view")
        command(self.go_down,                                   "down", "main", "go down in the main view")
        command(self.exit,                                      "q", "main", "quit holycurse")
        command(self.command_line,                              ":", "main", "enter command line mode, useless right now")
        command(self.tickle_one_day,                            "+", "main", "tickle the current mission for one")
        command(self.tickle_3_hours,                            "=", "main", "tickle the current mission for 3 hours")
        command(self.due_today,                                 "t", "main", "set the due date for this todo to today")
        command(self.due_in_3_days,                             "T", "main", "set the due date for this todo to in 3 days")
        command(self.due_this_week,                             "w", "main", "set the due date for this todo to this week")
        command(self.no_due,                                    "W", "main", "remove the due date of the current mission")
        command(self.toggle_n_recreate,                         "R", "main", "set has completed the current mission and recreate a misison in the same realm with the same description and same quest")
        command(self.toggle_mission,                            " ", "main", "toggle the completion state of the current mission")
        command(self.remove_mission,                            "d", "main", "")
        self.update_realm_view = lambda : louie.send("update_realm")
        command(self.update_realm_view,                         "2", "main", "go to realm view")
        command(self.add_mission_to_current_realm,              "a", "main", "add a new mission in the current realm")
        command(self.add_mission_to_current_realm_with_quest,   "A", "main", "add a new mission in the current realm with the same quest has the current mission")
        command(self.add_mission_to_default_realm,              "n", "main", "add a new mission to the default realm")
        command(self.add_completed_mission,                     "c", "main", "add a new completed mission")
        command(self.add_quest_to_current_mission,              "p", "main", "add a quest to the current mission")
        command(self.swap_mission_to_quest,                     "s", "main", "swap the current mission to a quest and add a new mission to this quest")
        command(self.rename_mission,                            "r", "main", "rename the current mission")
        command(self.update_main_view,                          "U", "main", "update the main view")
        command(self.toggle_active_mission,                     "u", "main", "toggle the active state of the current mission")
        command(self.toggle_showing_unactive_missions,          "z", "main", "toggle the display of unactive missions")
        self.get_help = lambda : louie.send("help")
        command(self.get_help,                                  "?", "main", "show help")

        louie.connect(self.get_user_input_main_view,                  "enter_user_input_main")

    def update_main_view(self):
        self.content = self.fill_main_view()
        self.listbox = MyListBox(self.content)
        self.frame.set_body(self.listbox)
        self.content.set_focus(self.position)
        if isinstance(self.frame.get_body().get_focus()[0], urwid.Text):
            pass
        elif isinstance(self.frame.get_body().get_focus()[0].original_widget, urwid.Divider):
            self.position -= 1
        elif isinstance(self.frame.get_body().get_focus()[0].original_widget, SeparationWidget):
            self.position += 1
        self.content.set_focus(self.position)
        louie.send("set state", None, "main")

    def fill_main_view(self):
        def D(string): open("DEBUG", "a").write("%s\n" % string)
        #from time import time
        #init = time()
        #som = init
        super_main_view = self.grail.super_main_view(unactive=self.unactive)
        #now = time()
        #D(" ")
        #D("get main view: %s" %  str(int(100 * (now - som))))
        #som = now
        last_completed_missions = self.grail.last_completed_missions()
        #now = time()
        #D("get last completed: %s" % str(int(100 * (  now - som))))
        #som = now
        if not super_main_view and not last_completed_missions:
        #if not super_main_view:
            return urwid.SimpleListWalker([urwid.Text("You don't have any mission, press 'n' to create a new one")])
        main_view = []
        for i in super_main_view:
            if type(i[0]) is str:
                main_view.append(SeparationWidget(i[0]))
            else:
                main_view.append(RealmWidget(i[0]))
            for j in i[1]:
                main_view.append(MissionWidget(j))

            main_view.append(urwid.Divider(" "))
        #now = time()
        #D("draw main view %s" %str(int(100 * (  now - som))))
        #som = now

        if last_completed_missions:
            main_view.append(SeparationWidget("LAST COMPLETED MISSIONS"))
            for i in last_completed_missions:
                main_view.append(MissionWidget(i))
        else:
            main_view.pop()
        #now = time()
        #D("draw last completed %s" %str(int(100 * (  now - som))))
        #som = now

        to_return = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in main_view])
        #now = time()
        #D("create the simplelistwalker %s" %str(int(100 * (  now - som))))
        #som = now

        to_return.set_focus(1)
        #D("total: %s" %str(int(100 * (  time() - init))))
        return to_return

    def refill_last_completed_missions(self):
        last_completed_missions = self.grail.last_completed_missions()
        if last_completed_missions:
            # if already have completed missions remove everything
            # yes, badly optimised
            saved_position = self.position
            if self.content[-1].original_widget.mission.completed:
                completed_missions, it = 0, len(self.content) -1
                while not isinstance(self.content[it].original_widget, SeparationWidget):
                    it -= 1
                    completed_missions += 1

                for i in xrange(completed_missions + 1):
                    self.content.pop()

            a = 0
            self.content.append(urwid.AttrMap(SeparationWidget("LAST COMPLETED MISSIONS"), None, 'reveal focus'))
            for i in self.grail.last_completed_missions():
                if a > 4:
                    break
                a += 1
                self.content.append(urwid.AttrMap(MissionWidget(i), None, 'reveal focus'))

            self.position = saved_position if saved_position < len(self.content) else len(self.content) - 1
            self.frame.get_body().set_focus(self.position)

    def get_main_view(self):
        self.update_main_view()
        return self.content

    @cant_be_call_on_empty_mainview
    def go_down(self):
        self.frame.get_body().set_focus(self.position + 1)
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, urwid.Divider):
            self.frame.get_body().set_focus(self.position + 3)

    @cant_be_call_on_empty_mainview
    def go_up(self):
        if self.position > 1:
            self.frame.get_body().set_focus(self.position - 1)
            if isinstance(self.frame.get_body().get_focus()[0].original_widget, SeparationWidget):
                self.frame.get_body().set_focus(self.position - 3)

    def command_line(self):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().insert_text(":")
        louie.send("set state", None, "command")

    @cant_be_call_on_empty_mainview
    @update_main
    def tickle_one_day(self):
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, MissionWidget):
            self._get_current_mission().tickle(datetime.now() + timedelta(days=1))

    @cant_be_call_on_empty_mainview
    @update_main
    def tickle_3_hours(self):
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, MissionWidget):
            self._get_current_mission().tickle(datetime.now() + timedelta(hours=3))

    @cant_be_call_on_empty_mainview
    def due_today(self, days=1):
        mission = self._get_current_mission()
        mission.due_for(datetime.today() + timedelta(days))
        if mission.completed:
            self._due_mission_completed(mission)
        else:
            self._due_mission(mission)

    @update_main
    def _due_mission(self, mission):
        return mission

    def _due_mission_completed(self, mission):
        self._get_current_widget().update()

    def due_in_3_days(self):
        self.due_today(4)

    def due_this_week(self):
        self.due_today(8)

    @cant_be_call_on_empty_mainview
    @update_main
    def no_due(self):
        self._get_current_mission().due_for(None)

    @cant_be_call_on_empty_mainview
    @update_main
    def toggle_n_recreate(self):
        mission = self._get_current_mission()
        self._toggle_mission(mission)
        return self.grail.add_mission(mission.description, quest=mission.quest, realm=mission.realm)

    @cant_be_call_on_empty_mainview
    @update_main
    def remove_mission(self):
        self._get_current_mission().remove()

    @update_main
    def toggle_active_mission(self):
        self._get_current_mission().toggle_active()

    @update_main
    def toggle_showing_unactive_missions(self):
        self.unactive = not self.unactive

    @cant_be_call_on_empty_mainview
    def toggle_mission(self):
        mission = self._get_current_mission()

        if not mission.completed:
            if mission.quest:
                self.add_new_mission_to_quest()
            else:
                self._toggle_mission(mission)
        else:
            mission.toggle()
            louie.send("update_main")

    #@remove_current_item
    #@add_to_completed_task
    @update_main
    def _toggle_mission(self, mission=None):
        if not mission:
            mission = self._get_current_mission()
        mission.toggle()
        return mission

    def add_new_mission_to_quest(self):
        self._wait_for_input("Next mission description (enter nothing to end quest): ", self.get_next_mission_to_quest)

    @disconnect
    @toggle_current_mission
    @have_input
    @update_main
    def get_next_mission_to_quest(self):
        old_mission = self._get_current_mission()
        return self.grail.add_mission(self.user_input, realm=old_mission.realm.id, quest=old_mission.quest.id, due=old_mission.due)

    @cant_be_call_on_empty_mainview
    def add_mission_to_current_realm(self):
        self._wait_for_input("Mission description: ", self.get_current_realm_mission)

    @disconnect
    @have_input
    #@append_mission_to_current_group
    @update_main
    def get_current_realm_mission(self):
        new_mission_realm = self._get_current_mission().realm

        current_todo_due_date = self._get_current_mission().due
        due_date = None
        if current_todo_due_date:
            for i in (1, 4, 8):
                if current_todo_due_date < datetime.now() + timedelta(i):
                    due_date = datetime.now() + timedelta(i)
                    new_mission_realm = None
                    break

        return self.grail.add_mission(self.user_input, realm=new_mission_realm, due=due_date)

    @cant_be_call_on_empty_mainview
    def add_mission_to_current_realm_with_quest(self):
        self._wait_for_input("Mission description: ", self.get_current_realm_mission_with_quest)

    @disconnect
    @have_input
    @update_main
    def get_current_realm_mission_with_quest(self):
        new_mission_realm = self._get_current_mission().realm
        new_mission_quest = self._get_current_mission().quest.id

        current_todo_due_date = self._get_current_mission().due
        due_date = None
        if current_todo_due_date:
            for i in (1, 4, 8):
                if current_todo_due_date < datetime.now() + timedelta(i):
                    due_date = datetime.now() + timedelta(i)
                    new_mission_realm = None
                    break

        return holygrail.Grail().add_mission(self.user_input, realm=new_mission_realm, due=due_date, quest=new_mission_quest)

    def get_user_input_main_view(self):
        self.frame.set_focus('body')
        # debug
        self.user_input = self.frame.footer.get_focus().edit_text
        self.frame.footer.get_focus().edit_text = ""
        self.frame.footer.get_focus().set_caption("")
        louie.send("set state", None, "main")
        louie.send("user_input_done")

    def add_mission_to_default_realm(self):
        self._wait_for_input("Mission description: ", self.get_default_realm_mission)

    @disconnect
    @have_input
    #@place_mission
    @update_main
    def get_default_realm_mission(self):
        self.grail.add_mission(self.user_input)

    def add_completed_mission(self):
        self._wait_for_input("Mission description: ", self.get_completed_mission)

    @disconnect
    @have_input
    @update_main
    def get_completed_mission(self):
        new_mission = self.grail.add_mission(self.user_input)
        new_mission.toggle()
        return new_mission

    @cant_be_call_on_empty_mainview
    def add_quest_to_current_mission(self):
        self._wait_for_input("Quest description: ", self.get_quest_to_current_mission)

    @disconnect
    @have_input
    @update_current_item
    def get_quest_to_current_mission(self):
        is_quest = self.grail.get_quest_by_desc(self.user_input.strip())
        if not is_quest:
            new_quest = self.grail.add_quest(self.user_input)
            self._get_current_mission().change_quest(new_quest.id)
        else:
            self._get_current_mission().change_quest(is_quest[0].id)

    @cant_be_call_on_empty_mainview
    def swap_mission_to_quest(self):
        self._wait_for_input("Mission description: ", self.get_swap_mission_to_quest)

    @disconnect
    @have_input
    @update_current_item
    def get_swap_mission_to_quest(self):
        old_mission = self._get_current_mission()
        is_quest = self.grail.get_quest_by_desc(old_mission.description)
        if not is_quest:
            new_quest = self.grail.add_quest(old_mission.description)
            old_mission.change_quest(new_quest.id)
        else:
            old_mission.change_quest(is_quest[0].id)
        old_mission.rename(self.user_input)

    @cant_be_call_on_empty_mainview
    def rename_mission(self):
        self._wait_for_input("New mission description: ", self.get_rename_mission)

    @disconnect
    @have_input
    @update_current_item
    def get_rename_mission(self):
        self._get_current_mission().rename(self.user_input.strip())

    def _wait_for_input(self, text, callback):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption(text)
        louie.send("set state", None, "user_input_main")
        louie.connect(callback, "user_input_done")

    def _get_current_widget(self):
        return self.frame.get_body().get_focus()[0].original_widget

    def _get_current_mission(self):
        return self._get_current_widget().mission

    def exit(self):
        raise urwid.ExitMainLoop()

class ChooseRealmList(object):
    def __init__(self, frame, main_view):
        self.position = 0
        self.frame = frame
        self.user_input = ""
        self.main_view = main_view
        self.grail = holygrail.Grail()

    def init_signals(self):
        command(self.go_up,                          "k",     "chose_realm", "move down in the realm list")
        command(self.go_down,                        "j",     "chose_realm", "move up in the realm list")
        command(self.go_up,                          "up",    "chose_realm", "move down in the realm list")
        command(self.go_down,                        "down",  "chose_realm", "move up in the realm list")
        command(self.return_to_main_view,            "q",     "chose_realm", "return to the main view")
        command(self.select_realm,                   "enter", "chose_realm", "chose the current realm")
        command(self.chose_realm,                    "C",     "main", "enter chose mode to select a new realm for the current mission")

    def chose_realm(self):
        realm_list = [RealmWidget(c) for c in self.grail.list_realms(all_realms=True)]
        self.content = realm_list
        realm_list = urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in realm_list])
        listbox = MyListBox(realm_list)
        listbox.set_focus(self.position)
        self.frame.set_body(listbox)
        louie.send("set state", None, "chose_realm")

    def return_to_main_view(self):
        louie.send("update_main")

    def go_down(self):
        # really unoptimised if
        if self.position < (len(self.content) - 1):
            self.frame.get_body().set_focus(self.position + 1)
            self.position += 1

    def go_up(self):
        if self.position > 0:
            self.frame.get_body().set_focus(self.position - 1)
            self.position -= 1

    @update_main
    def select_realm(self):
        if isinstance(self.main_view.listbox.get_focus()[0].original_widget, MissionWidget):
            self.main_view.listbox.get_focus()[0].original_widget.mission.change_realm(self.frame.get_body().get_focus()[0].original_widget.realm.id)

class RealmList(object):
    def __init__(self, frame):
        self.position = 0
        self.frame = frame
        self.user_input = ""
        self.grail = holygrail.Grail()

    def init_signals(self):
        louie.connect(self.update_realm_view,              "update_realm")

        self.update_main_view = lambda : louie.send("update_main")
        command(self.update_main_view,                          "1", "realm", "go to the main view")
        command(self.go_up,                                     "k", "realm", "go up in the realm list")
        command(self.go_down,                                   "j", "realm", "go down in the realm list")
        command(self.go_up,                                     "up", "realm", "go up in the realm list")
        command(self.go_down,                                   "down", "realm", "go down in the realm list")
        command(self.move_up_realm,                             "K", "realm", "move up the current realm")
        command(self.move_down_realm,                           "J", "realm", "move down the current realm")
        command(self.toggle_realm_hide,                         " ", "realm", "toggle the hidden state of the current realm")
        command(self.exit,                                      "q", "realm", "quit holycurse")
        command(self.rename_realm,                              "r", "realm", "rename the current realm")
        command(self.add_new_realm,                             "a", "realm", "add a new realm")
        command(self.add_new_realm,                             "n", "realm", "add a new realm")
        command(self.remove_realm,                              "d", "realm", "delete the current realm")
        command(self.update_realm_view,                         "U", "realm", "update the realm view")
        self.get_help = lambda : louie.send("help")
        command(self.get_help,                                  "?", "realm", "show help")

        louie.connect(self.get_user_input_realm,           "enter_user_input_realm")

    def update_realm_view(self):
        self.content = self.fill_realm_view()
        self.listbox = MyListBox(self.content)
        self.frame.set_body(self.listbox)
        self.content.set_focus(self.position)
        louie.send("set state", None, "realm")

    def fill_realm_view(self):
        context_view = [RealmWidget(i, detailled=True) for i in self.grail.list_realms(all_realms=True)]
        if context_view:
            return urwid.SimpleListWalker([urwid.AttrMap(w, None, 'reveal focus') for w in context_view])
        else:
            return urwid.SimpleListWalker([urwid.Text("Error, you don't have any realm, something really wrong has happended")])

    def go_down(self):
        # really unoptimised if
        if self.position < (len(self.content) - 1):
            self.position += 1
            self.frame.get_body().set_focus(self.position)

    def go_up(self):
        if self.position > 0:
            self.position -= 1
            self.frame.get_body().set_focus(self.position)

    @update_realm
    def move_down_realm(self):
        if self.position < (len(self.content) - 1):
            realm = self.frame.get_body().get_focus()[0].original_widget.realm
            realm.change_position(realm.position + 1)
            self.position += 1

    @update_realm
    def move_up_realm(self):
        if self.position > 0:
            realm = self.frame.get_body().get_focus()[0].original_widget.realm
            realm.change_position(realm.position - 1)
            self.position -= 1

    @update_current_item
    def toggle_realm_hide(self):
        self.frame.get_body().get_focus()[0].original_widget.realm.toggle_hide()

    def exit(self):
        raise urwid.ExitMainLoop()

    def rename_realm(self):
        self._wait_for_input("New realm description: ", self.get_rename_realm)

    @disconnect
    @have_input
    @update_current_item
    def get_rename_realm(self):
        self.frame.get_body().get_focus()[0].original_widget.realm.rename(self.user_input.strip())

    def get_user_input_realm(self):
        self.frame.set_focus('body')
        # debug
        self.user_input = self.frame.get_footer().get_focus().edit_text
        self.frame.get_footer().get_focus().edit_text = ""
        self.frame.get_footer().get_focus().set_caption("")
        louie.send("set state", None, "realm")
        louie.send("user_input_done")

    def add_new_realm(self):
        self._wait_for_input("Realm description: ", self.get_new_realm)

    @disconnect
    @have_input
    @update_realm
    def get_new_realm(self):
        self.position += 1
        self.grail.add_realm(self.user_input)

    @update_realm
    def remove_realm(self):
        realm = self.frame.get_body().get_focus()[0].original_widget.realm
        if realm.default_realm:
            # TODO display error
            return
        all_missions = realm.get_missions(all_missions=True)

        # I can't delete a realm with mission, so move all the missions to the default realm
        if all_missions:
            for i in all_missions:
                i.change_realm(self.grail.get_default_realm().id)
        realm.remove()

        self.frame.get_body().set_focus(self.position - 1)
        if isinstance(self.frame.get_body().get_focus()[0].original_widget, SeparationWidget):
            self.frame.get_body().set_focus(self.position)
        else:
            self.position -= 1

    def _wait_for_input(self, text, callback):
        self.frame.set_focus('footer')
        self.frame.get_footer().get_focus().set_caption(text)
        louie.send("set state", None, "user_input_realm")
        louie.connect(callback, "user_input_done")

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
