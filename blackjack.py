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

import random
import sys
import termios


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

    suites = ['clubs', 'diamonds', 'hearts', 'spades']
    names = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}

    name = names.get(num, str(num))
    print(name + ' of ' + suites[suite], end='')

def show_cards(name, cards):

    print()
    print(name, end=': ')
    for i, card in enumerate(cards):
        if i: print(', ', end='')
        show_card(card)
    print()

def play():

    num_decks = 6

    while True:

        try:
            bet = input('Bet: ')
        except EOFError:
            print()
            print('Have a great rest of your day!! :)')
            sys.exit(0)

        deck = shuffle_decks(num_decks)

        dealer_hand = [deck.pop(), deck.pop()]
        player_hand = [deck.pop(), deck.pop()]

        show_cards('Dealer', dealer_hand[:1])
        show_cards('You', player_hand)



# ______________________________________________________________________
# Main

if __name__ == '__main__':

    play()
