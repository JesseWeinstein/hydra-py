#!/usr/bin/env python

import curses
import hydra.tpf
from rdflib import *

g=Graph('TPFStore')

class Entry:
    def __init__(self, code, parent=None):
        self.code = code
        self.parent = parent
        self.wd = WD[self.code]
        self._subclasses = g.subjects(WDT.P279, self.wd)
        self.loaded_subclasses = []
        self.current_idx = -1
        self.all_loaded = False

    def make_window(self, y, x):
        self.y = y
        self.x = x
        self.window = curses.newwin(3, 2, self.y, self.x)
        self.adjust_current(+1)
        return self

    @property    
    def label(self):
        maybe_label = g.preferredLabel(self.wd, 'en', labelProperties=(RDFS.label,))
        self.label = str(maybe_label[0][1]) if maybe_label else self.code
        return self.label
    
    def open_current(self):
        return self.loaded_subclasses[self.current_idx].make_window(
            self.y + self.current_idx,
            self.x + self.window.getmaxyx()[1] + 2)

    def adjust_current(self, direction):
        self.current_idx += direction
        if self.current_idx < 0:
            self.current_idx = 0
        if self.current_idx >= len(self.loaded_subclasses):
            if self.all_loaded:
                self.current_idx = len(self.loaded_subclasses)-1
            else:
                try:
                    self.loaded_subclasses.append(Entry(self._subclasses.next().split('/')[-1], self))
                except StopIteration:
                    self.all_loaded = True
                    self.current_idx = len(self.loaded_subclasses)-1
        self.redisplay()

    def redisplay(self):
        if len(self.loaded_subclasses):
            self.window.resize(len(self.loaded_subclasses) + 2, max(
                len(self.loaded_subclasses[-1].label)+2,
                self.window.getmaxyx()[1]))
        self.window.clear()
        self.window.border()
        self.window.addstr(0,0,str(self.current_idx), curses.A_BOLD if self.all_loaded else curses.A_NORMAL)
        for idx, e in enumerate(self.loaded_subclasses):
            self.window.addstr(idx+1, 1, e.label, curses.A_BOLD if idx == self.current_idx else curses.A_NORMAL)
        self.window.refresh()

def main(s):
    global WD, WDT
    curses.curs_set(0)
    s.clear()
    s.border()
    s.addstr("Wikidata Subclasses", curses.A_BOLD)
    s.refresh()

    g.open('https://query.wikidata.org/bigdata/ldf')
    WD=Namespace(g.store.namespace('wd'))
    WDT=Namespace(g.store.namespace('wdt'))

    active = Entry('Q35120')
    active.make_window(1,1)
    while 1:
        c = s.getch()
        if c == curses.KEY_UP:
            active.adjust_current(-1)
        elif c == curses.KEY_DOWN:
            active.adjust_current(+1)
        elif c == curses.KEY_RIGHT:
            active = active.open_current()
        elif c == curses.KEY_LEFT and active.parent:
            active = active.parent 
        elif c == ord('q'):
            break

def main2(s):
    s.clear()
    s.border()
    s.addstr("what")
    s.refresh()

    s2=curses.newwin(3, 30, 1,1)
    s2.clear()
    while 1:
        s2.border()
        s2.addstr(1,1, "***")
        s2.refresh()
        c = s.getch()
        if c == ord('q'):
            break
        elif c == curses.KEY_DOWN:
            y, x = s2.getmaxyx()
            s2.resize(y + 1, x)
            s2.clear()

if __name__ == '__main__':
    curses.wrapper(main)

"""
Desired UI:

Curses file manager-like
Up/down arrow selects current entry; if down pressed at end, more loaded.
Right arrow loads subclasses of current entry, inserted, indented, after current entry
Left arrow jumps to parent of current entry (only if loaded)
"""


