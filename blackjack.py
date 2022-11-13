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
import random
import sys
import termios


# ______________________________________________________________________
# Globals

wallet = 1000

# Terminal-related globals.
smul, rmul = None, None


# ______________________________________________________________________
# Terminal-Escape Printing

def term_print(strs, flush=True):
    ''' This expects `strs` to be a list of strings and tuples. Each
        string is printed, while each tuple is interpreted as a tput command
        with any needed parameters supplied. For example, the tuple ('smul',)
        turns on underlined printing. The command ('setaf', 15) changes the font
        color to color 15 (which is typically white).
    '''
    for s in strs:
        if type(s) is str:
            s = s.encode()
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

def show_card(card):

    suite = card // 13
    num   = card % 13 + 1

    suites = ['♣', '♦', '♥', '♠']
    names = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}

    name = names.get(num, str(num))
    print(name + suites[suite], end='')

def show_cards(name, cards, end='\n'):

    print()
    print(name, end=': ')

    for i, card in enumerate(cards):
        if i: print(', ', end='')
        show_card(card)
    print(end=end)

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
        show_card(dealer_hand[-1])
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

def get_right_action(dealer, player):
    ''' This returns a letter from the string 'hsdopir' indicating
        the right course of action given the dealer hand (with
        dealer[0] visible) and the player hand.
        The actions match those in the prompt within practice().
    '''

    total, is_soft = get_total(player)
    dealer = min(dealer[0] % 13 + 1, 10)

    # Check for surrenders first.
    if (total == 16 and dealer in [1, 9, 10]) or (total == 15 and dealer == 10):
        return 'r'

    # Check for splits.
    c1 = min(player[0] % 13 + 1, 10)
    c2 = min(player[1] % 13 + 1, 10)
    if c1 == c2:
        if c1 == 1 or c1 == 8: return 'p'
        if c1 == 9 and dealer not in [1, 7, 10]: return 'p'
        if c1 == 4 and dealer in [5, 6]: return 'i'
        if c1 in [2, 3, 6, 7] and dealer <= 7 and not (c1 == 6 and dealer == 7):
            if (c1 == 6 and dealer == 2) or (c1 <= 3 and dealer <= 3):
                return 'i'
            return 'p'

    if not is_soft:

        if total >= 17: return 's'
        if total <= 8 : return 'h'
        if 12 <= total <= 16 and dealer <= 6:
            return 'h' if dealer in [2, 3] else 's'
        if total == 11: return 'd'
        if total == 10: return 'h' if dealer in [1, 10] else 'd'
        if total == 9: return 'd' if 3 <= dealer <= 6 else 'h'
        return 'h'

    else:  # The player has a soft total.

        if total >= 20: return 's'
        if total == 19: return 'o' if dealer == 6 else 's'
        if total == 18:
            if dealer <= 6: return 'o'
            return 's' if dealer <= 8 else 'h'
        lower = 11.5 - total / 2
        return 'd' if lower <= dealer <= 6 else 'h'

def practice():

    num_decks = 6

    while True:

        print('\n' + '_' * 70)

        deck = shuffle_decks(num_decks)

        dealer_hand = [deck.pop(), deck.pop()]
        player_hand = [deck.pop(), deck.pop()]

        show_cards('Dealer', dealer_hand[:1])
        show_cards('You', player_hand)

        msg = clean('''
            Action: _H_it _S_tand _D_ouble/hit D_o_uble/stand
                    S_p_lit Split-_i_f-DAS Su_r_render/hit _Q_uit
        ''')

        format_print('\n' + msg + '\n')
        choice = wait_for_user_choice('hsdopirq')

        if choice == 'q':
            be_done()

        right_action = get_right_action(dealer_hand, player_hand)
        if choice == right_action:
            print('nice')
        else:
            print(f'No, sorry, the right action is {right_action}')


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
