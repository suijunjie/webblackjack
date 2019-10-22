# Create your views here.
from django.shortcuts import render
from django.template.context_processors import csrf
from django.http import HttpResponse
import random
import BJGame.redis_helper as r
import BJGame.blackjack as bj

def conv_image_path(list):
    return [ str(i[1]) + '_' + str(i[0]).zfill(2) + '.png' for i in list]
    
def game(request):
    if request.method == 'GET':
        token = str(random.random())
        request.session['token'] = token
        
        r.set_redis(token, 'game_now', False)
        
        deck = bj.make_deck()
        r.set_redis(token, 'deck', deck)
        r.set_redis(token, 'money', 100)
        r.set_redis(token, 'bet', 0)
        r.set_redis(token, 'player_hands', [])
        r.set_redis(token, 'dealer_hands', [])
        dictionary = {
                'msg': 'ベットしてください。',
                'dealer_cards': [],
                'dealer_point': 0,
                'player_cards': [],
                'player_point': 0,
                'able_bet': True,
                'money': 100,
                }
        dictionary.update(csrf(request))
        
        return render(request, 'bjgame2.html', dictionary)
    elif request.method == 'POST':
        token = request.session['token']
        deck = r.get_redis(token, 'deck')
        money = r.get_redis(token, 'money')
        
        player_hands = r.get_redis(token, 'player_hands')
        dealer_hands = r.get_redis(token, 'dealer_hands')
        
        if r.get_redis(token, 'game_now') == False:
            try:
                if money < int(request.POST['bet']):
                    raise ValueError('too large bet')
            except ValueError:
                dictionary = {
                    'msg': '正しくベットしてください。',
                    'dealer_cards': [],
                    'dealer_point': 0,
                    'player_cards': [],
                    'player_point': 0,
                    'able_bet': True,
                    'money': money,
                    }
                dictionary.update(csrf(request))
                return render(request, 'bjgame2.html', dictionary)

            r.set_redis(token, 'game_now', True)
            money -= int(request.POST['bet'])
            r.set_redis(token, 'money', money)
            r.set_redis(token, 'bet', int(request.POST['bet']))
            dealer_hands = []
            dealer_hands.append(deck.pop())
            player_hands = []
            player_hands.append(deck.pop())
            player_hands.append(deck.pop())
            
            r.set_redis(token, 'dealer_hands', dealer_hands)
            r.set_redis(token, 'player_hands', player_hands)
            
            dealer_point = bj.get_point(dealer_hands)
            player_point = bj.get_point(player_hands)
            
            r.set_redis(token, 'deck', deck)
            dictionary = {
                    'msg': '選択してください。',
                    'dealer_cards': conv_image_path(dealer_hands),
                    'dealer_point': dealer_point,
                    'player_cards': conv_image_path(player_hands),
                    'player_point': player_point,
                    'able_bet': False,
                    'able_double': False,
                    'money': 100,
                    'bet': int(request.POST['bet']),
                    }
            dictionary.update(csrf(request))
            return render(request, 'bjgame2.html', dictionary)
        else:
            op = request.POST['operation']
            bet = r.get_redis(token, 'bet')
            doubled, ending = bj.player_op(deck, player_hands, op)
            r.set_redis(token, 'player_hands', player_hands)
            r.set_redis(token, 'deck', deck)
            player_point = bj.get_point(player_hands)
            print(player_hands)
            
            if doubled:
                bet = r.get_redis(token, 'bet')
                money -= bet
                bet *= 2
                r.set_redis(token, 'bet')
                r.set_redis(token, 'money', money)
            if ending:
                dealer_hands.append(deck.pop())
                bj.dealer_op(deck, player_hands, dealer_hands)
                r.set_redis(token, 'dealer_hands', dealer_hands)
                
                dealer_point = bj.get_point(dealer_hands)
                player_point = bj.get_point(player_hands)
                msg, money = bj.win_lose(dealer_hands, player_hands, bet, money)
                if money <= 0:
                    #return HttpResponse('GameOver')
                    return render(request, 'gameover.html')
                r.set_redis(token, 'money', money)
                msg += 'ベットしてください。'
                
                dictionary = {
                'msg': msg,
                'dealer_cards': conv_image_path(dealer_hands),
                'dealer_point': bj.get_point(dealer_hands),
                'player_cards': conv_image_path(player_hands),
                'player_point': bj.get_point(player_hands),
                'able_bet': True,
                'money': money,
                }
                dictionary.update(csrf(request))
                deck = bj.make_deck()
                r.set_redis(token, 'deck', deck)
                r.set_redis(token, 'game_now', False)
                return render(request, 'bjgame2.html', dictionary)
            else:
                r.set_redis(token, 'deck', deck)
                dictionary = {
                'dealer_cards': conv_image_path(dealer_hands),
                'dealer_point': bj.get_point(dealer_hands),
                'player_cards': conv_image_path(player_hands),
                'player_point': player_point,
                'able_bet': False,
                'money': money,
                'bet': bet,
                }
                dictionary.update(csrf(request))
                return render(request, 'bjgame2.html', dictionary)
            
            
def howto(request):
    return render(request, 'howto.html')