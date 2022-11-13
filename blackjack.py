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

    global smul, rmul

    if smul is None:
        curses.setupterm()
        smul = curses.tigetstr('smul')
        rmul = curses.tigetstr('rmul')

    byte_list = []
    mode = 0
    mode_starts = [rmul, smul]
    for ch in s:
        if ch == '_':
            mode = 1 - mode
            byte_list.append(mode_starts[mode])
        else:
            byte_list.append(ch.encode())
    sys.stdout.buffer.write(b''.join(byte_list))
    sys.stdout.buffer.flush()


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
    for card in hand:
        num = min(card % 13 + 1, 10)
        if num == 1: num_aces += 1
        total += num
    if total <= 11 and num_aces > 0:
        total += 10
    return total

def did_bust(hand):
    return get_total(hand) > 21

def resolve_game(player_hand, dealer_hand, deck):

    global wallet, bet

    if did_bust(player_hand):
        print('Gosh golly, you done busted')
        wallet -= bet
        return
    
    show_cards('Dealer', dealer_hand, end='')
    while get_total(dealer_hand) < 17:
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
    pl = get_total(player_hand)
    de = get_total(dealer_hand)
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
                    S_p_lit Split-_i_f-DAS Su_r_render _Q_uit
        ''')

        format_print('\n' + msg + '\n')
        choice = wait_for_user_choice('hsdopirq')

        if choice == 'q':
            be_done()



# ______________________________________________________________________
# Main

if __name__ == '__main__':

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
