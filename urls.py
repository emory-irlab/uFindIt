from django.conf.urls.defaults import *
#from django.views.generic import DetailView, ListView
from qac3.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #(r'^http/(?P<url>)/$', 'qac3.http_url_proxy.httpreq'),
    (r'^game/(?P<game_id>[0-9]+)/$', 'qac3.game.game_view'),
    (r'^game/(?P<game_id>[0-9]+)/query$', 'qac3.game.query_view'),
    (r'^game/(?P<game_id>[0-9]+)/answer$', 'qac3.game.answer_view'),

    (r'^$', 'django.views.generic.list_detail.object_list', dict(
           template_name="index.html",
           queryset=Game.objects.all(),
           ) ),
    (r'^aa/$', 'django.views.generic.list_detail.object_list', dict(
           template_name="index.html",
           queryset=Game.objects.all(),
           ) ),
    (r'^game/(?P<game_id>[0-9]+)/subscribe$', 'qac3.game.subscribe_view'),

    (r'^start_playing_now$', 'qac3.game.subscribe_g_view'),

    (r'^test_cookie$', 'qac3.game.test_cookie_view'),

    # (r'^qac/', include('qac.foo.urls')),
    # (r'^$', ListView.as_view(model=Game, context_object_name='games', template_name='index.html')),

    #(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/misha/qac/site_media'}),

    (r'^mturk$', 'django.views.generic.simple.redirect_to', {'url': 'mturk/'}),
    (r'^mturk/$', 'django.views.generic.simple.direct_to_template', {'template': 'mturk_index.html'}),
    (r'^mturk/subscribe$', 'qac3.mturk.mturk_subscribe_view'),
    (r'^mturk/mturk_captcha$', 'qac3.mturk.mturk_captcha_view'),
    (r'^mturk/task_finished$', 'qac3.mturk.mturk_task_finished_view'),
    (r'^mturk/mturk_task_finished_ok$', 'django.views.generic.simple.direct_to_template', {'template': 'mturk_task_finished_ok.html'}),

    (r'^rules.html$',  'django.views.generic.simple.direct_to_template', {'template': 'rules.html'}),

    (r'^myadm3/$', 'myadm3.myadm3_views.players_summary'),
    (r'^myadm3/player_game$', 'myadm3.myadm3_views.player_game'),
    (r'^myadm3/player_question_log$', 'myadm3.myadm3_views.player_question_log'),
    (r'^accounts/login/$', 'django.views.generic.simple.redirect_to', {'url': '/myadm2/'}),

    # Uncomment the next line to enable the admin:
    (r'^myadm2/', include(admin.site.urls)),
)
