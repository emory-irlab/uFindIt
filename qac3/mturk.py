from models import *
from django.shortcuts import get_object_or_404, render_to_response, redirect
import urllib2, urllib

def mturk_subscribe_view(request):
    assignmentId = request.GET['assignmentId']

    if assignmentId=='ASSIGNMENT_ID_NOT_AVAILABLE':
        return redirect("/mturk/")

    hitId = request.GET['hitId']
    workerId = request.GET['workerId']

    #game = Game.objects.get(mturk_hit_id=hitId)
    game = Game.objects.get(id=6)

    workerId += "@Game" + str(game.id)

    try:
        player = Player.objects.get(mturk_worker_id=workerId)
    except Player.DoesNotExist:
        player = Player.objects.create(email=workerId + ".com", name=workerId, idkey=workerId, mturk_worker_id=workerId)
    player.save()

    try:
        player_game = PlayerGame.objects.get(player=player, game=game)
    except PlayerGame.DoesNotExist:
        player_game = PlayerGame.objects.create(player=player, game=game)
    player_game.mturk_assignment_id = assignmentId
    player_game.save()

    response = redirect("/game/%d/?p=%s" % (game.id, player.idkey))
    import game
    game.set_player_cookie(player, response)
    return response

def mturk_captcha_view(request):
#    onclick="document.location.href='?p={{ player.idkey }}&start_new_game=on'"
    private_key = '6LeQo78SAAAAAHivldRoYO2l5HCYV9H-2aNSbHk-'
    remote_ip = request.META['REMOTE_ADDR']
    challenge_field = request.POST['recaptcha_challenge_field']
    response_field = request.POST['recaptcha_response_field']

    player_idkey = request.POST['p']
    game_id = request.POST['game_id']

    resp = urllib2.urlopen('http://www.google.com/recaptcha/api/verify',
                           data=urllib.urlencode(dict(
                                privatekey=private_key,
                                remoteip=remote_ip,
                                challenge=challenge_field,
                                response=response_field
                           )))
    ret = resp.read()
    ret_split = ret.split("\n")
    is_success = ret_split[0]=='true'
    if is_success:
        player = Player.objects.get(idkey=player_idkey)
        game = Game.objects.get(id=game_id)

        try:
            player_game = PlayerGame.objects.get(player=player, game=game)
        except PlayerGame.DoesNotExist:
            player_game = PlayerGame.objects.create(player=player, game=game)
        player_game.is_captcha_passed = True
        player_game.save()

        response = redirect("/game/%d/?p=%s" % (game.id, player.idkey))
        import game
        game.set_player_cookie(player, response)
        return response
    else:
        error_code = ret_split[1]
        return redirect("/game/%d/?p=%s&captcha_error=%s" % (int(game_id), player_idkey, error_code))

def mturk_task_finished_view(request):
    player_idkey = request.POST['p']
    game_id = request.POST['game_id']
    feedback_comments = request.POST['comment']

    player = Player.objects.get(idkey=player_idkey)
    game = Game.objects.get(id=game_id)
    player_game = PlayerGame.objects.get(player=player, game=game)
    player_game.feedback_comments = feedback_comments
    player_game.save()

    resp = urllib2.urlopen('http://www.mturk.com/mturk/externalSubmit?' +
                           urllib.urlencode(dict(
                                assignmentId=player_game.mturk_assignment_id,
                                sb="submit HIT"
                                )))
    ret = resp.read()
    return render_to_response("mturk_task_finished_ok.html", { 'mturk_response': ret })

