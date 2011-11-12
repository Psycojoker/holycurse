import holygrail
import urwid

from datetime import date, datetime

class MyListBox(urwid.ListBox):
    def keypress(self, size, key):
        return key

class MissionWidget(urwid.Text):
    def __init__(self, mission):
        if not isinstance(mission, holygrail._Mission):
            raise ValueError("Mission widget need a holygrail._Mission object")
        self.mission = mission
        urwid.Text.__init__(self, self.display(), wrap="clip")

    def update(self):
        self.set_text(self.display())

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
        if self.mission.active:
            old = date.today() - self.mission.created_at
            if (old.days - 1)/7 > 0:
                display.append(("old", "|"*((old.days - 1)/7)))
                display.append(" ")
            display.append("%s" % self.mission.description)
        else:
            display.append(("unactive", "%s" % self.mission.description))
        if self.mission.quest:
            display.append(" ")
            display.append(("quest", "[%s]" % self.mission.quest.description))
        if self.mission.due:
            display.append(" - ")
            if self.mission.due > datetime.now():
                color = "date left"
                display.append((color, "%s" % format_timedelta(datetime.now() - self.mission.due)))
            else:
                color = "date late"
                display.append((color, "%s" % format_timedelta(self.mission.due - datetime.now() )))

        return display

    def get_realm(self):
        return self.mission.realm

    def get_quest(self):
        return self.mission.quest

class SeparationWidget(urwid.Text):
    def __init__(self, text):
        urwid.Text.__init__(self, ('realm', text.upper()), wrap="clip")

class RealmWidget(SeparationWidget):
    def __init__(self, realm, detailled=False):
        if not isinstance(realm, holygrail._Realm):
            raise ValueError("Realm widget need a holygrail._Realm object")
        self.realm = realm
        self.detailled = detailled
        urwid.Text.__init__(self, self.display(), wrap="clip")

    def display(self):
        text = [('realm', self.realm.description.upper())]
        if self.detailled:
            if self.realm.default_realm:
                text.append(("quest", " [default]"))
            text.append(" (%i)" % len(list(self.realm.get_missions())))
        if self.realm.hide:
            text.append(" - ")
            text.append(("date left", "HIDE"))
        return text

    def update(self):
        self.set_text(self.display())
