#!/usr/bin/env python3
""" blackjack.py

    Usage:

        ./blackjack.py

    Play blackjack to get some practice.
"""

# Notes on internal data representation.
#
# * Each card c is an integer 0-51.
# * Break this down as (suite, num) = (c // 13, c % 13 + 1).
# * The suites are in this order: clubs, diamonds, hearts, spades.
# * The numbers are A, 2-10, J, Q, K.
# 


# ______________________________________________________________________
# Imports

import curses
import inspect
import json
import random
import sys
import termios


# ______________________________________________________________________
# Globals

wallet = 1000

# The practice history file.
history_f = None


# ______________________________________________________________________
# Terminal-Escape Printing

def term_print(strs, *args, flush=True):
    ''' This expects `strs` to be a list of strings and tuples. Each
        string is printed, while each tuple is interpreted as a tput command
        with any needed parameters supplied. For example, the tuple ('smul',)
        turns on underlined printing. The command ('setaf', 15) changes the font
        color to color 15 (which is typically white).
    '''

    if args:
        strs = [strs] + list(args)

    # As an edge case, we may receive just a single tuple.
    if type(strs) is tuple:
        strs = [strs]

    for s in strs:
        if type(s) is str:
            s = s.encode()
        elif type(s) is list:
            term_print(s)
            s = b''
        else:
            assert type(s) is tuple
            if len(s) == 1:
                s = curses.tigetstr(s[0])
            else:
                s = curses.tparm(curses.tigetstr(s[0]), *s[1:])
        sys.stdout.buffer.write(s)
    sys.stdout.buffer.flush()


# ______________________________________________________________________
# Utility Functions

def getch():
    old_settings = termios.tcgetattr(0)
    new_settings = old_settings[:]
    new_settings[3] &= ~termios.ICANON & ~termios.ECHO
    try:
        termios.tcsetattr(0, termios.TCSANOW, new_settings)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(0, termios.TCSANOW, old_settings)
    return ch

def wait_for_user_choice(choices):
    ''' Collect one keypress, and return the keypress if
        it is in the string `choices`, ignoring case. Otherwise keep
        collecting keypresses until the user acquiesces. 
    '''
    choice = '_'
    while choice not in choices:
        choice = getch().lower()
    return choice

def be_done():
    print()
    print('Have a great rest of your day!! :)')
    sys.exit(0)

clean = inspect.cleandoc
    
def format_print(s):

    parts = []
    mode = 0
    mode_starts = [('rmul',), ('smul',)]
    for i, substr in enumerate(s.split('_')):
        if i > 0:
            mode = 1 - mode
            parts.append(mode_starts[mode])
        parts.append(substr)

    term_print(parts)


# ______________________________________________________________________
# Blackjack Functions

def shuffle_decks(num_decks):

    one_deck  = list(range(52))
    full_deck = one_deck * num_decks
    random.shuffle(full_deck)

    return full_deck

def get_card_strs(card):
    ''' Return name, suite, where `name` is one of these strings:
        2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A;
        and suite is one (non-ASCII) character.
    '''

    suite = card // 13
    num   = card % 13 + 1

    suites = ['♣', '♦', '♥', '♠']
    names = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}

    name = names.get(num, str(num))

    return name, suites[suite]

def get_card_str(card):
    name, suite = get_card_strs(card)
    return name + suite

def show_cards(name, cards, end='\n'):

    print()
    print(name, end=': ')

    for i, card in enumerate(cards):
        if i: print(', ', end='')
        print(get_card_str(card), end='')
    print(end=end)

## Functions to play

def get_total(hand):
    total = 0
    num_aces = 0
    is_soft = False
    for card in hand:
        num = min(card % 13 + 1, 10)
        if num == 1: num_aces += 1
        total += num
    if total <= 11 and num_aces > 0:
        total += 10
        is_soft = True
    return total, is_soft

def did_bust(hand):
    return get_total(hand)[0] > 21

def resolve_game(player_hand, dealer_hand, deck):

    global wallet, bet

    if did_bust(player_hand):
        print('Gosh golly, you done busted')
        wallet -= bet
        return
    
    show_cards('Dealer', dealer_hand, end='')
    while get_total(dealer_hand)[0] < 17:
        print(' ..hit.. ', end='')
        dealer_hand.append(deck.pop())
        print(get_card_str(dealer_hand[-1]), end='')
    print()

    if did_bust(dealer_hand):
        print('Well lookee, the dealer did a bust')
        print('You win!')
        wallet += bet
        return

    # If we get here, neither the player nor the dealer has busted.
    pl = get_total(player_hand)[0]
    de = get_total(dealer_hand)[0]
    if pl == de:
        print('push')
    elif pl > de:
        print('player wins!')
        wallet += bet
    else:
        print('dealer wins')
        wallet -= bet

def play():

    global bet

    num_decks = 6

    while True:

        print('\n' + '_' * 70)
        print(f'You have ${wallet}.\n')
        try:
            bet = int(input('Bet: '))
        except EOFError:
            be_done()

        # TODO Don't shuffle every time.
        deck = shuffle_decks(num_decks)

        dealer_hand = [deck.pop(), deck.pop()]
        player_hand = [deck.pop(), deck.pop()]

        show_cards('Dealer', dealer_hand[:1])
        show_cards('You', player_hand)

        # TODO Handle a natural blackjack.

        is_done = False

        while not is_done:

            # TODO Add more choices.
            print('[H]it, [S]tand, [Q]uit')
            choice = wait_for_user_choice('hsq')

            if choice == 'q':
                be_done()
            if choice == 'h':
                player_hand.append(deck.pop())
                show_cards('You', player_hand)
                is_done = did_bust(player_hand)
            if choice == 's':
                is_done = True

        # TODO Include the bet and bet outcome here.
        resolve_game(player_hand, dealer_hand, deck)

## Functions to practice

def get_right_action(dealer, player):
    ''' This returns a letter from the string 'hsdopir' indicating
        the right course of action given the dealer hand (with
        dealer[0] visible) and the player hand.
        The actions match those in the prompt within practice().
    '''

    total, is_soft = get_total(player)
    dealer = min(dealer[0] % 13 + 1, 10)
    if dealer == 1: dealer = 11

    # Check for splits.
    c1 = min(player[0] % 13 + 1, 10)
    c2 = min(player[1] % 13 + 1, 10)
    if c1 == c2:
        if c1 == 1 or c1 == 8: return 'p'
        if c1 == 9 and dealer not in [7, 10, 11]: return 'p'
        if c1 == 4 and dealer in [5, 6]: return 'i'
        if c1 in [2, 3, 6, 7] and dealer <= 7 and not (c1 == 6 and dealer == 7):
            if (c1 == 6 and dealer == 2) or (c1 <= 3 and dealer <= 3):
                return 'i'
            return 'p'

    # Check for surrenders.
    if not is_soft:
        if (
                (total == 16 and dealer in [9, 10, 11]) or
                (total == 15 and dealer == 10)
           ):
            return 'r'

    if not is_soft:

        if total >= 17: return 's'
        if total <= 8 : return 'h'
        if 12 <= total <= 16 and dealer <= 6:
            return 'h' if (total == 12 and dealer <= 3) else 's'
        if total == 11: return 'd'
        if total == 10: return 'h' if dealer >= 10 else 'd'
        if total == 9: return 'd' if 3 <= dealer <= 6 else 'h'
        return 'h'

    else:  # The player has a soft total.

        if total >= 20: return 's'
        if total == 19: return 'o' if dealer == 6 else 's'
        if total == 18:
            if dealer <= 6: return 'o'
            return 's' if 7 <= dealer <= 8 else 'h'
        lower = 11.5 - total / 2
        return 'd' if lower <= dealer <= 6 else 'h'

def render_hand(name, hand, do_draw_top=False):
    ''' This renders cards in a 7x3 (7-wide, 3-tall) "card" in color
        in the terminal. The card background is white, with most cards
        using the central 3 character spaces for the card character (eg 2, 6, K)
        on the left and the suite character on the right. The 10 card renders
        with the '1' extending out an extra character to the left.

        There's also room for the `name` string, which is expected to be at most
        6 characters long.
    '''

    _normal    = ('sgr0',)
    _green_bg  = ('setab', 28)
    _subtle_fg = ('setaf', 34)
    _white_bg  = ('setab', 15)
    _red_fg    = ('setaf', 196)
    _black_fg  = ('setaf', 232)

    n = len(hand)

    # Top line.
    if do_draw_top:
        term_print(_green_bg, ' ' * (9 + 8 * 2))
    # Go to normal mode at the end of lines to avoid bg-color overrun, which
    # happens when we print a new line at the bottom of the terminal.
    term_print(_normal)
    print()

    # Top of cards.
    text_free_card_line = []
    text_free_card_line += [_green_bg, ' ' * 9]
    for i in range(2):
        bg = _white_bg if i < n else _green_bg
        text_free_card_line += [bg, ' ' * 7, _green_bg, ' ']
    term_print(text_free_card_line, _normal)
    print()

    # Main line.
    term_print(_green_bg, _subtle_fg, f' {name:6s}  ')
    for i in range(2):
        if i < n:
            card = hand[i]
            name, suite = get_card_strs(card)
            fg = _red_fg if suite in ['♦', '♥'] else _black_fg
            term_print(_white_bg, fg, f' {name:>2s} {suite}  ', _green_bg, ' ')
        else:
            term_print(_green_bg, ' ' * 8)
    term_print(_normal)
    print()

    # Bottom of cards.
    term_print(text_free_card_line, _normal)
    print()

    # Bottom line.
    term_print(_green_bg, ' ' * (9 + 8 * 2))
    term_print(_normal)

def get_choice_str(choice):
    choices = {
            'h': 'hit',
            's': 'stand',
            'd': 'double/hit',
            'o': 'double/stand',
            'p': 'split',
            'i': 'split-if-DAS',
            'r': 'surrender'
    }
    return choices[choice]

def record_practice(dealer, player, choice, right_action):

    global history_f

    if history_f is None:
        history_f = open('practice_history.jsonl', 'w')

    obj = {
            'dealer': get_card_str(dealer[0]),
            'player': ' '.join(get_card_str(c) for c in player),
            'player choice': get_choice_str(choice),
            'right action' : get_choice_str(right_action)
    }

    history_f.write(json.dumps(obj, ensure_ascii=False) + '\n')

def practice():

    num_decks = 6

    while True:

        print('\n' + '_' * 70)

        deck = shuffle_decks(num_decks)

        dealer_hand = [deck.pop(), deck.pop()]
        player_hand = [deck.pop(), deck.pop()]

        render_hand('Dealer', dealer_hand[:1], do_draw_top=True)
        render_hand('You', player_hand)

        msg = clean('''
            Action: _H_it _S_tand _D_ouble/hit D_o_uble/stand
                    S_p_lit Split-_i_f-DAS Su_r_render/hit _Q_uit
        ''')

        format_print('\n\n' + msg + '\n')
        choice = wait_for_user_choice('hsdopirq')

        if choice == 'q':
            be_done()

        print('You chose to', get_choice_str(choice))

        right_action = get_right_action(dealer_hand, player_hand)
        if choice == right_action:
            print('nice')
        else:
            print(f'No, sorry, the right action is {right_action}')

        record_practice(dealer_hand, player_hand, choice, right_action)


# ______________________________________________________________________
# Main

if __name__ == '__main__':

    curses.setupterm()

    # Ask the user to choose a mode.
    print('Choose a mode please:')
    print('[1] Play [2] Practice perfect strategy')
    choice = wait_for_user_choice('12')

    if choice == '1':
        play()
    elif choice == '2':
        # TODO Print out a perfect strategy chart, or otherwise
        #      make that available to the user.
        practice()
