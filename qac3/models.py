from django.db import models
from django.db.models.signals import post_save

class QueryTask(models.Model):
    query = models.CharField(max_length=2000, unique=True)

    def __unicode__(self):
        return self.query

class Game(models.Model):
    name = models.CharField(max_length=200)
    query_tasks = models.ManyToManyField(QueryTask, through='GameQueryTask')

    allow_subscribe = models.BooleanField(default=True, help_text=u"do allow players to subscribe to this game")

    query_time_limit = models.IntegerField(default=180, help_text=u"query time limit in seconds, 0 means inifinite and is allowed only if is_simultaneous_game=False)")
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField(blank=True, null=True)
    game_time_limit = models.IntegerField(default=1800, help_text=u"0 means inifinite, this field is ignored when is_simultaneous_game or query_time_limit>0") 

    do_loop_questions = models.BooleanField(default=False, help_text=u"do show first question after the game ends")
    allow_subscribe = models.BooleanField(default=True, help_text=u"do allow players to subscribe to this game")
    is_simultaneous_game = models.BooleanField(default=True, help_text=u"if True, then all users can see the only the same questions")
    #allow_anonymous_access = models.BooleanField(default=False, help_text=u"do allow players to play this game (should be False yet)")
    is_randomized = models.BooleanField(default=False, help_text=u"randomize question order for each player, only if not is_simultaneous_game")

    mturk_hit_id = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.name

class GameQueryTask(models.Model):
    game = models.ForeignKey(Game)
    query_task = models.ForeignKey(QueryTask)
    order = models.PositiveIntegerField()

    def __unicode__(self):
        return self.game.name + ": q#" + str(self.order) + " " + self.query_task.query

    class Meta:
        ordering = ('order',)

class Player(models.Model):
    email = models.EmailField(unique=True, blank=True, null=True)
    idkey = models.SlugField(unique=True)
    name = models.CharField(max_length=50)

    games = models.ManyToManyField(Game, through='PlayerGame')
    game_units = models.ManyToManyField(GameQueryTask, through='GameUnit')

    mturk_worker_id = models.CharField(max_length=100, blank=True, null=True)

    g_game_id = models.IntegerField(blank=True, null=True, help_text=u'id of game assigned for this player by randomly selecting in subscribe_g_view')

    def __unicode__(self):
        return self.email

class GameUnit(models.Model):
    player = models.ForeignKey(Player)
    game_query_task = models.ForeignKey(GameQueryTask)

    date_answer = models.DateTimeField(auto_now_add=True)
    ip_addr = models.IPAddressField(default=u"127.0.0.1")

    answer = models.CharField(max_length=2000)
    answer_url = models.CharField(max_length=2000)

    is_checked = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

class PlayerGame(models.Model):
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)

    date_game_start = models.DateTimeField(auto_now_add=True)
    last_query_order_answered = models.IntegerField(default=0, help_text=u'last query answered, identified by order_id')
    date_last_answer = models.DateTimeField(blank=True, null=True)

    is_captcha_passed = models.BooleanField(default=False)
    mturk_assignment_id = models.CharField(max_length=100, blank=True, null=True)
    feedback_comments = models.CharField(max_length=4000, blank=True, null=True)

    def __unicode__(self):
        ret = str(self.id) + ": " + str(self.game)
        pgrt_set = PlayerGameRandomizedTasks.objects.filter(player_game=self).order_by('order_show')
        if pgrt_set.count():
            ret += " randomized" + str([pgrt.order_gqt for pgrt in pgrt_set])
        return ret


def player_game_post_save(sender, instance, created, **kwargs):
    if not created or not instance.game.is_randomized: return

    ## create PlayerGameRandomizedTasks
    questions = GameQueryTask.objects.filter(game=instance.game)
    question_list = [gqt for gqt in questions]

    import random
    random.shuffle(question_list)

    i = 0
    for gqt in question_list:
        i += 1
        pgrt = PlayerGameRandomizedTasks(player_game=instance, order_show=i, order_gqt=gqt.order, game_query_task=gqt)
        pgrt.save()
    
post_save.connect(player_game_post_save, PlayerGame, dispatch_uid="qac3.models")

class PlayerGameRandomizedTasks(models.Model):
    player_game = models.ForeignKey(PlayerGame)
    order_show = models.PositiveIntegerField()
    order_gqt = models.PositiveIntegerField()
    game_query_task = models.ForeignKey(GameQueryTask)

### checking the results
class QueryTaskAnswer(models.Model):
    query_task = models.ForeignKey(QueryTask)

    answer = models.CharField(max_length=2000)
    answer_url = models.CharField(max_length=2000)
    is_correct = models.BooleanField(default=False)
    comment = models.BooleanField(default=False)

