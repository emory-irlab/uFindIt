from models import *
from django.contrib import admin
from django.shortcuts import get_object_or_404, render_to_response
from models import *
from django.http import HttpResponseRedirect

class GameQueryTask_Inline(admin.TabularInline):
    model = GameQueryTask
    extra = 1

class QueryTaskAnswer_Inline(admin.TabularInline):
    model = QueryTaskAnswer
    extra = 1

class GameUnit_Inline(admin.StackedInline):
    model = GameUnit
    extra = 0

class PlayerGame_Inline(admin.StackedInline):
    model = PlayerGame
    extra = 0

class QueryTaskAdmin(admin.ModelAdmin):
    model = QueryTask
    inlines = (GameQueryTask_Inline, QueryTaskAnswer_Inline, )

class PlayerAdmin(admin.ModelAdmin):
    model = Player
    inlines = (PlayerGame_Inline, GameUnit_Inline, )
    list_display = ('email', 'name', 'idkey', 'mturk_worker_id', 'g_game_id')

class GameAdmin(admin.ModelAdmin):
    model = Game
    inlines = (GameQueryTask_Inline, )

admin.site.register(QueryTask, QueryTaskAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Player, PlayerAdmin)

#class GameUnit(models.Model):
#    player = models.ForeignKey(Player)
#    game_query_task = models.ForeignKey(GameQueryTask)
#
#    date_start = models.DateTimeField(auto_now_add=True)
#    date_answer = models.DateTimeField(blank=True)
#    answer = models.CharField(max_length=2000)
#    answer_url = models.CharField(max_length=2000)
#
#    is_checked = models.BooleanField(default=False)
#    is_correct = models.BooleanField(default=False)

#class TransBounce_Cols_Inline(admin.TabularInline):
#    model = TransBounce_Cols
#    extra = 0
#    can_delete = False
#    fields = ('name', 'datatype', 'description', 'do_use', 'do_show',)
#    readonly_fields = ('name', 'datatype', 'description', )

