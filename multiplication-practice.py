#!/usr/bin/python3

from tkinter import Label, Tk, StringVar
from random import randint
from types import MethodType, GetSetDescriptorType
from typing import List, Dict
from textwrap import dedent
import re
import time

class MultiplicationWidgetState:
    def __init__(self, message: str=None, event_routings=None):
        '''
        Used to manage states for the MultiplicationWidget

        @param message: str The message to be displayed when in this state
        @param event_routings: List[Dict] A list of dicts containing event types
                                          and the methods they should bind to.
        
        The messages are formatted in the following way:
        Anything within square brackets is considered to be
        a variable.
        They are first matched against object properties,
        and then against any other variable within function scope.

        The event routings should be of the form
        {'event_name': ['<method_name>', ...], ...}
        '''
        self.message = message if message else ''
        self.event_routings = event_routings if event_routings else []


class MultiplicationWidget(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initialize properties
        self.num_problems: int = 5
        self.seconds_elapsed: float = None
        self.num_solved: int = None
        self._num_displayed: int = None
        self.first_num: int = None
        self.second_num: int = None

        self._start_time: float = None
        self._end_time: float = None

        self._user_input_buffer: str = None
        
        # factor limits 
        self._min_factor: int  = 0
        self._max_factor: int = 10

        # initialize widget state
        self.widget_states = {
            'initial':      MultiplicationWidgetState(
                message='[num_problems] Challenges.\nClick to Start!',
                event_routings={
                    '<Button-1>': ['start_game'],
                    '<Return>': ['start_game']
                    }),
            'problem':      MultiplicationWidgetState(
                message='[first_num] X [second_num]\n[_user_input_buffer]',
                event_routings={
                    '<Key>': ['on_keypress'],
                    '<BackSpace>': ['on_backspace'],
                    '<Return>': ['on_enter'],
                    }),
            'correct':      MultiplicationWidgetState(
                message="That's correct!\nClick to continue.",
                event_routings={
                    '<Button-1>': ['next_problem'],
                    '<Return>': ['next_problem'],
                }
            ),
            'incorrect':      MultiplicationWidgetState(
                message="That's incorrect.\nClick to continue.",
                event_routings={
                    '<Button-1>': ['next_problem'],
                    '<Return>': ['next_problem'],
                }
            ),
            'end':          MultiplicationWidgetState(
                message='You solved [num_solved] out of [num_problems] in [seconds_elapsed] seconds!\n'
                                'Click to play again!',
                event_routings={
                    '<Button-1>': ['start_game'],
                    '<Return>': ['start_game']})
        }

        # initialize widget state
        self.curr_widget_state = 'initial'

        # initialize text variable
        self.text = StringVar()

        # initialize internal label
        self.label = Label(self, textvariable=self.text)
        self.label.pack()

        # set label text
        self.set_widget_state(self.curr_widget_state)

        # configure label
        self.label.config(font=('Arial Black', 40, 'bold'))
        self.label.config(bg='#222', fg='#fff')
        self.config(bg='#222')
    
    def start_game(self, event):
        # starts loop of displaying different math problems
        self._init_vars()
        self._start_time = time.time()
        self._display_problem()
    
    def _gen_factors(self):
        self.first_num = randint(self._min_factor, self._max_factor)
        self.second_num = randint(self._min_factor, self._max_factor)
    
    def _init_vars(self):
        self.num_solved = 0
        self._num_displayed = 0
        self._user_input_buffer = ""
    
    def _get_formatted(self, template: str) -> str:
        '''
        Returns formatted version of template
        '''
        match_str = r'(?<!\\)\[(.+?)(?<!\\)\]'
        # find everything wrapped in square braces
        replacement_candidates = re.findall(match_str, template)

        # initialize dict for end values
        replacements = {}

        # find the values to replace them with
        for candidate in replacement_candidates:
            if candidate in vars(self):
                # class property
                replacements[candidate] = vars(self)[candidate]
            elif candidate in dict(globals(), **locals()):
                # within scope
                replacements[candidate] = dict(globals(), **locals())[candidate]
            else:
                raise RuntimeError('Bad format key: "{}"'.format(candidate))
        
        # replace with correct values
        for candidate in  replacements:
            sub_string = r'(?<!\\)\['+str(candidate)+r'(?<!\\)\]'
            template = re.sub(sub_string, str(replacements[candidate]), template)
        return template
    
    def refresh_text(self, *args):
        '''
        refreshes the self.text property
        '''
        widget_state = self.widget_states[self.curr_widget_state]
        self.text.set(self._get_formatted(widget_state.message))
    
    def set_widget_state(self, state_name: str):
        '''
        Sets widget state to any value from widget_states
        '''
        widget_state = self.widget_states[state_name]
        old_widget_state = self.widget_states[self.curr_widget_state]

        # unbind old events
        for event_name in old_widget_state.event_routings:
            for func_name in old_widget_state.event_routings[event_name]:
                exec('self.unbind(\'{event_name}\')'.format(event_name=event_name))

        # bind new ones
        for event_name in widget_state.event_routings:
            for func_name in widget_state.event_routings[event_name]:
                exec('self.bind(\'{event_name}\', self.{func_name})'.format(event_name=event_name, func_name=func_name))
        
        # set display text
        self.text.set(self._get_formatted(widget_state.message))

        # set state
        self.curr_widget_state = state_name
    
    def on_keypress(self, event):
        if event.char.isnumeric():
            self._user_input_buffer += event.char
            self.refresh_text()
    
    def on_backspace(self, event):
        self._user_input_buffer = self._user_input_buffer[:-1]
        self.refresh_text()
    
    def on_enter(self, event):
        if len(self._user_input_buffer) > 0:
            # check response
            correct_result = self.first_num * self.second_num
            if int(self._user_input_buffer) == correct_result:
                self.num_solved += 1
                self.set_widget_state('correct')
            else:
                self.set_widget_state('incorrect')
    
    def next_problem(self, event):
        self._gen_factors()
        self._user_input_buffer = ""
        self._display_problem()

    def _display_problem(self):
        if self._num_displayed == self.num_problems:
            # challenge set complete
            self._end_time = time.time()
            self.seconds_elapsed = round(self._end_time - self._start_time, 1)
            self.set_widget_state('end')
        else:
            # generate numbers
            self._gen_factors()
            # display next problem
            self.set_widget_state('problem')
            self._num_displayed += 1
    
    
        
            


if __name__ == '__main__':
    mw = MultiplicationWidget()
    mw.mainloop()