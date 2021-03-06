from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, JsonResponse
from . import credentials as cred 
from .models import Card, Deck2, Distribution
from . import kf_data_v2 as kf2
from django.db.models import Sum, Q

import json
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.datastructures import MultiValueDictKeyError


def index(request):
    return render(request, 'kf_main/index.html', {'message': '', 'search': '#'})


def search(request):
    data = json.loads(request.body)
    search_str = data['search']
    print(search_str)
    deck_list = Deck2.objects.filter(name__icontains=search_str).order_by('name')

    deck_dict={}
    for i, deck in enumerate(deck_list):
        deck_dict[i] = model_to_dict(deck)

    page = data['page']
    paginator = Paginator(deck_list, 25)

    try:
        decks = paginator.page(page)
    except PageNotAnInteger:
        decks = paginator.page(1)
    except EmptyPage:
        decks = paginator.page(paginator.num_pages)

    index = decks.number - 1 
    max_index = len(paginator.page_range)
    start_index = index - 3 if index >= 3 else 0
    end_index = index + 3 if index <= max_index - 3 else max_index
    page_range = list(paginator.page_range)[start_index:end_index]

    deck_dict2={}
    for i, deck in enumerate(decks):
        deck_dict2[i] = model_to_dict(deck)

    house_lists = [] 
    for deck in decks:
        house_lists.append(deck.house_list)

    context = {
        'house_lists': house_lists,
        'search_str': search_str,
        'page_range': page_range,
        'deck_dict': deck_dict,
        'deck_dict2': deck_dict2
    }

    return JsonResponse(context)


def deck_search(request):
    search = request.POST['search_string']
    if search:
        deck_list = Deck2.objects.filter(name__icontains=search)
    else: 
        deck_list = []

    if not deck_list:
        return render(request, 'kf_main/index.html', {'message': 'No decks found', 'search': '#'})
    elif len(deck_list) == 1:
        return HttpResponseRedirect(reverse('kf_main:deck_detail', args=(deck_list[0].id,)))
    else:
        return render(request, 'kf_main/index.html', {'message': '', 'search': search})


def get_tooltip(request):
    data = json.loads(request.body)
    deck = Deck2.objects.get(id=data['deck_id'])
    deck_dict = model_to_dict(deck)
    return JsonResponse(deck_dict)


def deck_detail(request, deck_id):
    deck = Deck2.objects.get(id=deck_id)        
    global_dist = model_to_dict(Distribution.objects.get(id=1))
    top_dist = model_to_dict(Distribution.objects.get(id=2))
    g_action, g_artifact, g_creature, g_upgrade, g_amber = global_dist['action'], global_dist['artifact'], global_dist['creature'], global_dist['upgrade'], global_dist['amber']
    top_action, top_artifact, top_creature, top_upgrade, top_amber = top_dist['action'], top_dist['artifact'], top_dist['creature'], top_dist['upgrade'], top_dist['amber']

    type_nums = []
    type_nums.append({'type': 'action', 'amount': deck.num_action})
    type_nums.append({'type': 'artifact', 'amount': deck.num_artifact})
    type_nums.append({'type': 'creature', 'amount': deck.num_creature})
    type_nums.append({'type': 'upgrade', 'amount': deck.num_upgrade})

    card_objects = [] 
    for card_id in deck.card_list:
        card_objects.append(Card.objects.get(id=card_id))
        
    context = {
        'deck': deck,
        'house1': deck.house_list[0],
        'house2': deck.house_list[1],
        'house3': deck.house_list[2],
        'deck_card_list': card_objects,
        'power_list': deck.creature_pwr,
        'deck_amber': deck.bonus_amber,
        'type_nums': type_nums,
        'g_action': g_action,
        'g_artifact': g_artifact,
        'g_creature': g_creature,
        'g_upgrade': g_upgrade,
        'g_amber': g_amber,
        'top_action': top_action,
        'top_artifact': top_artifact,
        'top_creature': top_creature,
        'top_upgrade': top_upgrade,
        'top_amber': top_amber,
    }

    return render(request, 'kf_main/deck_detail.html', context)


def get_stats(deck_cards):      # list of card ids
    power_list = {} 
    deck_amber = 0
    type_nums = {
        'action': 0,
        'artifact': 0,
        'creature': 0,
        'upgrade': 0
    }
    
    for card in deck_cards:     
        card_details = Card.objects.get(id=card)        
        type_nums[card_details.card_type.lower()] += 1       
        deck_amber += card_details.amber

        if card_details.power == 0:
            continue
        elif card_details.power in power_list:
            power_list[card_details.power] += 1
        else:
            power_list[card_details.power] = 1
        
    type_list = []
    for card_type in type_nums:
        type_list.append({'type': card_type, 'amount': type_nums[card_type]})

    return (power_list, type_list, deck_amber)


def get_global_dist():
    deck_list = Deck2.objects.all()
    return (get_dist(deck_list))
            
            
def get_top_dist():
    deck_list = Deck2.objects.filter(power_level__gt=1)
    top_decks = []

    for deck in deck_list:
        if deck.losses != 0 and deck.power_level == 2:
            if deck.wins / deck.losses >= 3:
                top_decks.append(deck) 
        else:
            top_decks.append(deck)

    return(get_dist(top_decks))


def get_dist(deck_list):
    action_dist, artifact_dist, creature_dist, upgrade_dist, amber_dist = {}, {}, {}, {}, {} 
    for deck in deck_list:
        if deck.num_action in action_dist:
            action_dist[deck.num_action] += 1
        else:
            action_dist[deck.num_action] = 1
        if deck.num_artifact in artifact_dist:
            artifact_dist[deck.num_artifact] += 1
        else:
            artifact_dist[deck.num_artifact] = 1
        if deck.num_creature in creature_dist:
            creature_dist[deck.num_creature] += 1
        else:
            creature_dist[deck.num_creature] = 1
        if deck.num_upgrade in upgrade_dist:
            upgrade_dist[deck.num_upgrade] += 1
        else:
            upgrade_dist[deck.num_upgrade] = 1
        if deck.bonus_amber in amber_dist:
            amber_dist[deck.bonus_amber] += 1
        else:
            amber_dist[deck.bonus_amber] = 1


    return (action_dist, artifact_dist, creature_dist, upgrade_dist, amber_dist)



# Average chains for decks with registered games   
def get_chains():
    total_chains = Deck2.objects.aggregate(Sum('chains'))
    deck_count = Deck2.objects.filter(Q(wins__gt=0) | Q(losses__gt=0)).count()

    return total_chains['chains__sum'] / deck_count


# Average win/loss ratio for decks with registered games 
def get_win_loss():
    deck_list = Deck2.objects.filter(Q(wins__gt=0) | Q(losses__gt=0))
    win_loss_total = 0

    for deck in deck_list:
        if deck.losses != 0:
            win_loss_total += deck.wins / deck.losses
        else:
            win_loss_total += deck.wins

    return win_loss_total / len(deck_list)


# Average OP games for decks with registered games
def get_avg_games():
    deck_list = Deck2.objects.filter(Q(wins__gt=0) | Q(losses__gt=0))
    total_games = 0

    for deck in deck_list:
        total_games += deck.wins + deck.losses

    return total_games / len(deck_list)



def get_nodes(request):
    data = json.loads(request.body)
    deck_id = data['deck_id']
    user_deck = Deck2.objects.get(id=deck_id)
    houses = user_deck.house_list
    decks = Deck2.objects.all()
    house_match_list = []

    for deck in decks:
        if houses[0] not in deck.house_list or houses[1] not in deck.house_list or houses[2] not in deck.house_list:
            continue
        else:
            house_match_list.append(deck)

    percent_match = []
    
    for deck in house_match_list:
        card_count = 0
        for card in user_deck.card_list:
            if card in deck.card_list:
                card_count+=1
        
        percent_match.append([int(card_count / 36 * 100), deck.id, deck.wins, deck.losses])

    percent_match.sort(key=lambda x: x[0], reverse=True)
    percent_match = {'percent_match': percent_match[:26]}

    return JsonResponse(percent_match)


def update_dist():
    g_action, g_artifact, g_creature, g_upgrade, g_amber = get_global_dist()
    top_action, top_artifact, top_creature, top_upgrade, top_amber = get_top_dist()

    if Distribution.objects.filter(id=1).exists():
        Distribution.objects.filter(id=1).update(action=g_action)
        Distribution.objects.filter(id=1).update(artifact=g_artifact)
        Distribution.objects.filter(id=1).update(creature=g_creature)
        Distribution.objects.filter(id=1).update(upgrade=g_upgrade)
        Distribution.objects.filter(id=1).update(amber=g_amber)
    else:
        dist = Distribution.objects.create(action=g_action, artifact=g_artifact, creature=g_creature, upgrade=g_upgrade, amber=g_amber, id=1)
        dist.save()

    if Distribution.objects.filter(id=2).exists():
        Distribution.objects.filter(id=2).update(action=top_action)
        Distribution.objects.filter(id=2).update(artifact=top_artifact)
        Distribution.objects.filter(id=2).update(creature=top_creature)
        Distribution.objects.filter(id=2).update(upgrade=top_upgrade)
        Distribution.objects.filter(id=2).update(amber=top_amber)
    else:
        dist = Distribution.objects.create(action=top_action, artifact=top_artifact, creature=top_creature, upgrade=top_upgrade, amber=top_amber, id=2)
        dist.save()


def get_top100(request):
    top100 = []
    pwr_dict ={}

    for i in range(2,11):
        pwr_list = Deck2.objects.filter(power_level=i)
        pwr_dict[i] = pwr_list

    for power in pwr_dict:
        ordered_list = []
        for deck in pwr_dict[power]:
            if not ordered_list:
                ordered_list.append(deck)
            else:
                for i, top_deck in enumerate(ordered_list):
                    if deck.chains > top_deck.chains:
                        ordered_list.insert(i, deck)
                        break
                    elif deck.chains == top_deck.chains:
                        if deck.wins / (deck.wins + deck.losses) > top_deck.wins / (top_deck.wins+top_deck.losses):
                            ordered_list.insert(i, deck)
                            break
                        elif deck.wins / (deck.wins + deck.losses) == top_deck.wins / (top_deck.wins+top_deck.losses):
                            if deck.wins > top_deck.wins:
                                ordered_list.insert(i, deck)
                                break
            if deck not in ordered_list:
                ordered_list.append(deck)

        top100 = ordered_list + top100

    house_lists = [] 
    for deck in top100[:100]:
        house_lists.append(deck.house_list)

    top_dict={}
    for i, deck in enumerate(top100[:100]):
        top_dict[i] = model_to_dict(deck)

    context = {
        'top_dict': top_dict,
        'house_lists': house_lists
    }
        
    return JsonResponse(context)
                
                
def get_card_freq(request):
    import requests
    decks = json.loads(get_top100(None).content.decode("utf-8"))['top_dict']

    houses = {
        'Brobnar':{},
        'Dis':{},
        'Logos':{},
        'Mars':{},
        'Sanctum':{},
        'Shadows':{},
        'Untamed':{},
    }
    
    for i in decks:
        for card_id in decks[i]['card_list']:
            card = Card.objects.get(id=card_id)

            if card.card_title in houses[card.house]:
                houses[card.house][card.card_title] += 1
            else:
                houses[card.house][card.card_title] = 1
    
    sorted_houses = {}
    for house in houses:
        sorted_house = sorted(houses[house].items(), key=lambda kv: kv[1], reverse=True)
        sorted_houses[house] = [list(tup) for tup in sorted_house]

    return JsonResponse(sorted_houses)
            


# get_top100("w")
# get_card_freq("k")
# update_dist()
# kf2.set_main_data(kf2.page, kf2.site)
# get_nodes('eb5d4c4a-5957-4276-ab9a-0d1b19f42e81')
# get_top_dist()
# dp.set_deck_attrib()
# deck_card_list = Card.objects.filter(deck_card__deck_id=deck)