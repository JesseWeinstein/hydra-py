#!/usr/bin/env python2

import sys
import curses
import hydra.tpf
from rdflib import *

g=Graph('TPFStore')

class Entry:
    def __init__(self, code, parent=None):
        self.code = code
        self.parent = parent
        self.wd = WD[self.code]
        self._generator = g.subjects(WDT.P279, self.wd)
        self.children = []
        self.idx = -1
        self.all_loaded = False
        self.window = None
        maybe_label = g.preferredLabel(self.wd, 'en', labelProperties=(RDFS.label,))
        self.label = maybe_label[0][1].encode('utf-8') if maybe_label else self.code

    def load(self, y, x):
        self.y = y
        self.x = x
        self.is_active = True
        if not self.window:
            self.window = curses.newwin(3, 2, self.y, self.x)
            self.adjust_current(+1)
        else:
            self.window.mvwin(self.y, self.x)
            self.redisplay()
        return self

    
    def open_current(self):
        new = self.children[self.idx].load(
            self.y + self.idx+1,
            self.x + self.window.getmaxyx()[1])
        if not new.children:
            return self
        else:
            self.is_active = False
            self.redisplay()
            return new

    def move_to_parent(self):
        self.is_active = False
        self.redisplay()
        if self.parent:
            self.parent.is_active = True
            self.parent.redisplay()
            return self.parent
        return self
    
    def adjust_current(self, direction):
        self.idx += direction
        if self.idx < 0:
            self.idx = 0
        if self.idx >= len(self.children):
            if self.all_loaded:
                self.idx = len(self.children)-1
            else:
                start_loading()
                try:
                    self.children.append(Entry(self._generator.next().split('/')[-1], self))
                except StopIteration:
                    self.all_loaded = True
                    self.idx = len(self.children)-1
                done_loading()
        self.redisplay()
    def redisplay(self):
        if not self.children:
            self.window.resize(1,2)
            self.window.clear()
            self.window.addstr(0,0,'*')
        else:
            ci = str(self.idx)
            self.window.resize(len(self.children) + 2, max(
                len(ci) + 3,
                (len(self.children[-1].label) + 2) if len(self.children) else 0,
                self.window.getmaxyx()[1]))
            self.window.clear()
            if self.is_active:
                self.window.border(0,0,0,0,'+','+','+','+')
            else:
                self.window.border()
            self.window.addstr(0,0, ci, curses.A_BOLD if self.all_loaded else curses.A_NORMAL)
            update_url_window(self.children[self.idx].wd if self.idx > -1 else '***')
            for idx, e in enumerate(self.children):
                self.window.addstr(idx+1, 1, e.label, curses.A_BOLD if idx == self.idx else curses.A_NORMAL)
        self.window.refresh()

def start_loading():
    stdscr.addstr(0, stdscr.getmaxyx()[1]-1, '*')
    stdscr.refresh()

def done_loading():
    stdscr.addch(0, stdscr.getmaxyx()[1]-1, curses.ACS_URCORNER)
    stdscr.refresh()

def update_url_window(thing):
    url_window.clear()
    url_window.resize(1, len(thing) + 1)
    url_window.addstr(0,0, thing)
    url_window.refresh()

def main(s):
    global WD, WDT, stdscr, url_window
    stdscr = s
    try:
        s.leaveok(0)
        curses.curs_set(0)
    except curses.error:
        pass
    s.clear()
    s.border()
    s.addstr("Wikidata Subclasses", curses.A_BOLD)
    url_window = curses.newwin(1,2,s.getmaxyx()[0]-1,2)
    s.refresh()
    start_loading()
    g.open('https://query.wikidata.org/bigdata/ldf')
    WD=Namespace(g.store.namespace('wd'))
    WDT=Namespace(g.store.namespace('wdt'))

    active = Entry(sys.argv[1] if len(sys.argv)>1 else 'Q35120')
    active.load(1,1)
    done_loading()
    while 1:
        s.move(0,0)
        c = s.getch()
        if c == curses.KEY_UP:
            active.adjust_current(-1)
        elif c == curses.KEY_DOWN:
            active.adjust_current(+1)
        elif c == curses.KEY_RIGHT:
            active = active.open_current()
        elif c == curses.KEY_LEFT:
            active = active.move_to_parent()
        elif c == ord('q'):
            break

if __name__ == '__main__':
    curses.wrapper(main)

"""
Desired UI:

Curses file manager-like
Up/down arrow selects current entry; if down pressed at end, more loaded.
Right arrow loads subclasses of current entry, inserted, indented, after current entry
Left arrow jumps to parent of current entry (only if loaded)
"""


