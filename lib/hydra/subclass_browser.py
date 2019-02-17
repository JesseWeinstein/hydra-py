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
            self.window = pad.subwin(3, 2, self.y, self.x)
            self.adjust_current(+1)
        else:
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
        if self.parent:
            self.is_active = False
            self.redisplay()
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
            # for n in range(1, 10):
            #     try:
            #         self.window.addstr(n,0,str(n))
            #     except curses.error:
            #         pass

            self.window.addstr(0,0, ci, curses.A_BOLD if self.all_loaded else curses.A_NORMAL)
            update_url_window(self.children[self.idx].wd if self.idx > -1 else '***')
            for idx, e in enumerate(self.children):
                self.window.addstr(idx+1, 1, e.label, curses.A_BOLD if idx == self.idx else curses.A_NORMAL)

def start_loading():
    update_url_window('Loading...')

def update_url_window(thing):
    url_window.clear()
    try:
        url_window.addstr(0,1, thing)
    except curses.error:
        pass # may fail if the window is too small
    url_window.refresh()

def setup():
    my, mx=stdscr.getmaxyx()
    stdscr.clear()
    stdscr.border()
    stdscr.addstr(0,0, "Wikidata Subclasses", curses.A_BOLD)
    # for n in range(1, 10):
    #     stdscr.addstr(n,0,str(n))

    stdscr.refresh()
    url_window.resize(1, mx-4)
    url_window.mvwin(my-1, 2)
    url_window.refresh()
    stdscr.move(0,0)

def main(s):
    global WD, WDT, stdscr, url_window, pad
    stdscr = s
    try:
        stdscr.leaveok(0)
        curses.curs_set(0)
    except curses.error:
        pass
    url_window = curses.newwin(1, 1, 1, 2)

    mpady, mpadx = (500,500)
    y, x = (0, 0)
    pad = curses.newpad(mpady, mpadx)

    setup()

    start_loading()
    g.open('https://query.wikidata.org/bigdata/ldf')

    WD=Namespace(g.store.namespace('wd'))
    WDT=Namespace(g.store.namespace('wdt'))

    active = Entry(sys.argv[1] if len(sys.argv)>1 else 'Q35120')
    active.load(0,1)
    while 1:
        setup()
        my, mx=stdscr.getmaxyx()
        # stdscr.addstr(0, 20, str((y,x)))
        # stdscr.addstr(0, 30, str(y-active.y - active.idx + my))

        pad.refresh(y, x, 1, 1, my-2, mx-2)    
        c = stdscr.getch()
        if c == curses.KEY_UP:
            active.adjust_current(-1)
        elif c == curses.KEY_DOWN:
            active.adjust_current(+1)
        elif c == curses.KEY_LEFT:
            active = active.move_to_parent()
        elif c == curses.KEY_RIGHT:
            active = active.open_current()

        qy = y - active.y - active.idx # distance from active to top
        qmy = qy + my - 2 # distance from active to bottom
        if c == ord('e') or (c == curses.KEY_UP and (qy == 1 or qy == 2)) and y > 0: # up
            y += -1
        elif c == ord('d') or (c == curses.KEY_DOWN and (qmy == 1 or qmy == 2)) and y < mpady: # down
            y += 1
        elif c == ord('s') and x > 0: # <-
            x += -1
        elif c == ord('f') and x < mpadx: # ->
            x += 1
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
