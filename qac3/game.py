from models import *
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpRequest, HttpResponse
import time, smtplib, math, urllib2, random, datetime
from django.template import Context, loader
import urllib

def game_view(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    assert isinstance(game, Game)
    assert isinstance(request, HttpRequest)

    assert game.allow_subscribe # check whether this game is allowed to subscribe

    player = get_player_from_request(request)
    if not player:
        pmessage = "Sorry, we can't recognize you"
        return render_to_response('subscribe.html', {'game': game, 'pmessage': pmessage})

    qtask = None
    state = None
    current_time = time.time()
    game_start_time = time.mktime(game.start_time.timetuple())
    time_to_start = game_start_time - current_time
    lastqto = int(request.GET.get("lastqto", 0))
    game_query_tasks_count = game.query_tasks.count()
    question_order = None

    if current_time < game_start_time:
        state = 'game not started'
    elif game.finish_time and current_time >= time.mktime(game.finish_time.timetuple()):
        state = 'game finished'
    elif game.is_simultaneous_game:
        #####################################################################################
        assert not game.is_randomized

        question_order = (current_time - game_start_time) / game.query_time_limit
        question_order = int(math.floor(question_order) + 1)
        if question_order > game_query_tasks_count:
            if game.do_loop_questions:
                question_order = question_order % game_query_tasks_count
                if question_order == 0: question_order = game_query_tasks_count
            else:
                state = 'game finished'

        if lastqto <= question_order:
            state = "wait next query"

        if not state:
            state = 'playing'
            qtask = GameQueryTask.objects.get(game__id=game.id, order=question_order)

        if state == "wait next query" or state == 'playing':
            loop_count = math.floor( (current_time - game_start_time) / (game.query_time_limit * game_query_tasks_count) )
            loop_start_time = game_start_time + loop_count * game_query_tasks_count * game.query_time_limit
            next_query_time = loop_start_time + game.query_time_limit * question_order
            time_to_start = next_query_time - current_time
    else:  # not simultaneous game
        #####################################################################################
        try:
            player_game = PlayerGame.objects.get(player=player, game=game)
            state = 'playing'
        except PlayerGame.DoesNotExist:
            if request.GET.get('start_new_game'):
                player_game = PlayerGame.objects.create(player=player, game=game)
                player_game.save()
                state = 'playing'
            else:
                state = 'ask_to_start_game'

        if state == 'playing' and player.mturk_worker_id and not player_game.is_captcha_passed:
            state = 'ask_to_start_game'

        if state == 'playing':
            question_order = player_game.last_query_order_answered + 1
            if game.query_time_limit > 0:
                if player_game.date_last_answer:
                    time_from_last_answer = current_time - time.mktime(player_game.date_last_answer.timetuple())
                else:
                    time_from_last_answer = current_time - time.mktime(player_game.date_game_start.timetuple())

                if time_from_last_answer >= game.query_time_limit:
                    loop_count = math.floor(time_from_last_answer / float(game.query_time_limit))
                    question_order += loop_count
                    time_from_last_answer -= loop_count * game.query_time_limit

                time_to_start = game.query_time_limit - time_from_last_answer
                
            elif game.game_time_limit > 0:
                time_to_game_end = time.mktime(player_game.date_game_start.timetuple()) + game.game_time_limit - current_time
                if time_to_game_end <= 0:
                    state = 'game finished'
                else:
                    # to set up timer
                    time_to_start = time_to_game_end

        if state == 'playing':
            if question_order > game_query_tasks_count:
                state = 'game finished'
            else:
                if game.is_randomized:
                    pgrt = PlayerGameRandomizedTasks.objects.get(player_game=player_game, order_show=question_order)
                    qtask = pgrt.game_query_task
                else:
                    qtask = GameQueryTask.objects.get(game__id=game.id, order=question_order)

    search_engine = request.COOKIES.get('search_engine', 'google')
    if question_order is not None: question_order = int(question_order)

    response = render_to_response('game.html', dict(
        game=game,
        state=state,
        current_time=time.ctime(current_time),
        time_to_start=time_to_start,
        qtask=qtask,
        question_order=question_order,
        player=player,
        search_engine=search_engine,
        captcha_error='&error=' + str(request.GET.get('captcha_error'))
        ))
    set_player_cookie(player, response)
    return response

def get_player_from_request(request):
    assert isinstance(request, HttpRequest)
    player_idkey = request.GET.get('p', None)
    if not player_idkey and request.method == 'POST':
        player_idkey = request.POST.get('p', None)
    if not player_idkey:
        player_idkey = request.COOKIES.get('p', None)

    if not player_idkey:
        return None
#        pmessage = "This game does not allow anonymous access"
#        return render_to_response('subscribe.html', {'game': game, 'pmessage': pmessage})

    try:
        player = Player.objects.get(idkey=player_idkey)
    except Player.DoesNotExist:
        return None
#        pmessage = "Sorry, we can't recognize you"
#        return render_to_response('subscribe.html', {'game': game, 'pmessage': pmessage})

    return player

def set_player_cookie(player, response):
    response.set_cookie("p", player.idkey, max_age=3600*24*30)

def subscribe_view(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    assert isinstance(game, Game)
    assert isinstance(request, HttpRequest)

    assert game.allow_subscribe # check whether this game is allowed to subscribe

    if not request.POST.has_key("_submit"):
        return render_to_response('subscribe.html', {'game': game })

    email = request.POST["email"]
    try:
        player = Player.objects.get(email=email)
    except Player.DoesNotExist:
        #import hashlib
        #idkey = hashlib.new('ripemd160', email + "some hash salt some hash salt").hexdigest()
        import sha
        idkey = sha.new(email + "some hash salt some hash salt").hexdigest()
        player = Player.objects.create(email=email, name=request.POST["name"], idkey=idkey)
    player.save()

    # send an email to subscriber
    #try:
    #from email.mime.text import MIMEText
    from email.MIMEText import MIMEText
    mailtext = loader.get_template('subscribe_email.txt').render(Context({ 'player': player, 'game': game, 'host': request.get_host() }))
    msg = MIMEText(mailtext)

    msg['Subject'] = 'subscription to Query Answering Game'
    msg['From'] = 'Query Answering Game <qag.mathcs@gmail.com>'
    msg['To'] = player.email

    # Send the message via our own SMTP server, but don't include the envelope header.
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    #s.set_debuglevel(1)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login('qag.mathcs', 'tech1tech2')
    s.sendmail(msg['From'], player.email, msg.as_string())
    s.quit()
    #except:

    return render_to_response('subscribe_ok.html', { 'game': game })

def subscribe_g_view(request):
    assert isinstance(request, HttpRequest)

    if not request.POST.has_key("_submit"):
        return render_to_response('subscribe_g.html')

    email = request.POST["email"]
    name = request.POST["name"]

    import sha
    idkey = sha.new(name + "some hash salt some hash salt").hexdigest()

    try:
        player = Player.objects.get(idkey=idkey)
    except Player.DoesNotExist:
        player = Player.objects.create(email=email, name=name, idkey=idkey)

    if not player.g_game_id:
        player.g_game_id = random.sample((6,7,8,9), 1)[0]

    player.save()

    game = Game.objects.get(id=player.g_game_id)

    try:
        player_game = PlayerGame.objects.get(player=player, game=game)
    except PlayerGame.DoesNotExist:
        player_game = PlayerGame.objects.create(player=player, game=game)
    player_game.save()

    response = redirect("/game/%d/?p=%s" % (game.id, player.idkey))
    set_player_cookie(player, response)
    return response

def query_view(request, game_id):
    assert isinstance(request, HttpRequest)

    query = request.GET['query']
    search_engine = request.GET.get('search_engine', 'google')
    if search_engine == 'yahoo':
        request_prefix = 'search.yahoo.com/search?p='
    elif search_engine == 'bing':
        request_prefix = 'www.bing.com/search?q='
    else:
        search_engine = 'google'
        request_prefix = 'www.google.com/search?q='

    #return redirect("http://search.yahoo.com/search?p=" + urllib.quote(query))
    response = redirect("http://ir-ub.mathcs.emory.edu:8100/http/" + request_prefix + urllib.quote(query))
    response.set_cookie('search_engine', search_engine)
    return response

def answer_view(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    assert isinstance(game, Game)
    assert isinstance(request, HttpRequest)

    player = get_player_from_request(request)
    if not player:
        pmessage = "Sorry, we can't recognize you"
        return render_to_response('subscribe.html', {'game': game, 'pmessage': pmessage})

    params = request.POST
    qtask_order = params['qto']
    question_order = params['question_order']
    answer = params['answer']
    answer_url = params['answer_url']

    game_query_task = GameQueryTask.objects.get(game__id=game.id, order=qtask_order)
    game_unit = GameUnit.objects.create(
        player=player,
        game_query_task=game_query_task,
        ip_addr=request.META['REMOTE_ADDR'],
        answer=answer,
        answer_url=answer_url,
    )
    game_unit.save()

    if not game.is_simultaneous_game:
        player_game = PlayerGame.objects.get(player=player, game=game)
        player_game.last_query_order_answered = question_order
        player_game.date_last_answer = datetime.datetime.now()
        player_game.save()

    return redirect("/game/%d/?p=%s&lastqto=%s&rand=%d" % (game.id, player.idkey, question_order, int(random.random() * 10000)))

def test_cookie_view(request):
    c = request.COOKIES.get('p')
    if c:
        return HttpResponse("True")
    else:
        return HttpResponse("False")