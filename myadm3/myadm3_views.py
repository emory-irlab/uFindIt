from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.contrib.auth.decorators import login_required
import urllib2, urllib
import re
from django.http import HttpResponse
from django.db import connection as conn
from django.template import Context, loader
import StringIO
import xml.sax.saxutils

@login_required()
def players_summary(request):
    prefix = request.GET.get('prefix', "")
    if not prefix: prefix = request.COOKIES.get('prefix', "")

    sql = """SELECT game, player_key,
                   count(*) AS question_get,
                   sum((case when answer is not null and answer<>'' and answer<>'no answer' then 1 else 0 end)) AS answers_sent,
                   sum(cast(is_answer_correct as int)) AS answers_correct,
                   sum((case when is_answer_correct is null then 0 else 1 end)) AS answers_ased,
                   sum(sec_duration) AS game_duration,
                   sum(cnt_queries) AS cnt_queries,
                   sum(cnt_browse_200) AS cnt_browse_200,
                   sum((case when cnt_queries>0 then 1 else 0 end)) AS questions_with_queries,
                   sum((case when cnt_browse_200>0 then 1 else 0 end)) AS questions_with_browse_200,
                   sum(cast(is_answer_url_in_history as int)) AS answer_urls_in_history,
                   to_char(sum(cast(is_answer_url_in_history as int))/(1E-12+sum((case when answer is not null and answer<>'' and answer<>'no answer' then 1 else 0 end))), '0.0') AS hist_of_sent,
                   max(cast(is_mturk_task_finished as int)) AS is_mturk_task_finished,
                   (select pg.mturk_assignment_id
                      from qac3_playergame pg
                           join qac3_player p on p.id=pg.player_id
                      where pg.game_id=q.game
                        and p.mturk_worker_id=q.player_key) AS mturk_assignment_id,
                   (select pg.feedback_comments
                      from qac3_playergame pg
                           join qac3_player p on p.id=pg.player_id
                      where pg.game_id=q.game
                        and p.mturk_worker_id=q.player_key) AS feedback_comments
              FROM """ + prefix + """_questions q
              GROUP BY game, player_key
              ORDER BY game, is_mturk_task_finished desc, answers_sent desc, player_key"""

    def render_hl_1(v):
        if str(v) == '1':
            return '<div style="width:100%; background-color:lightgray; font-weight:bold">' + str(v) + '</div>'
        else:
            return v
    def cell_wide_overflow(v):
        return u'<div style="width:200px; max-height: 26px; overflow-x:hidden; overflow-y: scroll;">' + unicode(v) + u'</div>'
    def hist_of_sent_cell(v):
        if v and float(v)<=0.6:
            return u'<font color="red">' + v + "</font>"
        else:
            return v

    html = render_sql_as_html_table(sql, None, {
        'player_key': lambda v, row: '<a href="player_game?player_key=%s&game=%d">%s</a>' % (v, row['game'], v),
        'is_mturk_task_finished': render_hl_1,
        'feedback_comments': cell_wide_overflow,
        'hist_of_sent': hist_of_sent_cell,
    })

    response = render_to_response("myadm3/html_wrap.html", dict(
        html=html,
        title="Summary of players in log " + prefix + "_queries",
        prefix=prefix
    ))
    response.set_cookie("prefix", prefix)
    return response

def player_game_table(player_key, game, prefix, question_num=None):
    sql = """SELECT *
              FROM """ + prefix + """_questions q
              WHERE game=%s
                AND player_key=%s
          """
    if question_num:
        sql += "        AND question_num=" + str(question_num) + "\n"
    sql += "      ORDER BY question_num"

    def cell_wide(v):
        return u'<div style="width:300px">' + unicode(v) + u'</div>'
    def cell_to_log(v, row):
        return u'<a href="player_question_log?player_key=%s&game=%s&question_num=%d">%s</a>' % (player_key, game, row["question_num"], unicode(v))

    def cell_is_answer_correct(v, row):
        h = """<select name="field_qn_%d_answer" onchange="document.getElementById('id_fields_changed_set').value += ',' + this.name;">""" % row["question_num"]
        h += ' <option'
        if v is None: h += " selected"
        h += '>?</option> <option'
        if v == True: h += " selected"
        h += '>+</option> <option'
        if v == False: h += " selected"
        h += '>-</option>'
        h += '</select>'
        return h

    def cell_is_answer_correct_comment(v, row):
        if v: vv = v
        else: vv = ""
        return """<input type="text" width="20" name="field_qn_%d_answer_com" value="%s" onchange="document.getElementById('id_fields_changed_set').value += ',' + this.name;">""" % (row["question_num"], vv)

    def is_answer_url_in_history(v):
        if v:
            return '<div style="width:100%; background-color:lightgray; font-weight:bold">' + str(v) + '</div>'
        else:
            return v

    html = render_sql_as_html_table(sql, (game, player_key), {
        'question': cell_wide,
        'answer': cell_wide,
        'answer_url': lambda v: '<a href="%s" target="_blank">%s</a>' % (v, re.sub(r'^http://ir-ub.mathcs.emory.edu.*?/http', 'ir-ub/http', unicode(v))),
        'is_answer_correct': cell_is_answer_correct,
        'is_answer_correct_comment': cell_is_answer_correct_comment,
        'last_query': cell_wide,
        'sec_duration': cell_to_log,
        'cnt_queries': cell_to_log,
        'cnt_browse_200': cell_to_log,
        'cnt_browse': cell_to_log,
        'last_browse_url': lambda v: '<a href="http://ir-ub.mathcs.emory.edu:8100%s" target="_blank">%s</a>' % (v, v),
        'is_answer_url_in_history': is_answer_url_in_history
    })

    html += """
        <input type="hidden" name="player_key" value="%s">
        <input type="hidden" name="game" value="%s">
        <input type="hidden" name="fields_changed_set" value="" id="id_fields_changed_set">
        """ % (player_key, game)

    return html

def update_questions_table(request):
    id_fields_changed_set = request.GET.get("fields_changed_set")
    if not id_fields_changed_set: return

    prefix = request.GET.get('prefix')
    if not prefix: prefix = request.COOKIES.get('prefix', "")
    game = request.GET['game']
    player_key = request.GET['player_key']

    cur = conn.cursor()
    fields = set(id_fields_changed_set.strip(",").split(","))
    for field_name in fields:
        m = re.match(r'^field_qn_(\d+)_(answer.*)$', field_name)
        if not m: continue
        question_num, field_tail = m.group(1), m.group(2)
        if field_tail == "answer":
            value = request.GET.get(field_name, 'nokey')
            if value=='nokey': continue
            
            if value == "?":
                cur.execute("""UPDATE """ + prefix + """_questions
                                 SET is_answer_correct=NULL
                                 WHERE player_key=%s
                                   AND game=%s
                                   AND question_num=%s""",
                            (player_key, game, question_num))
            else:
                cur.execute("""UPDATE """ + prefix + """_questions
                                 SET is_answer_correct=%s
                                 WHERE player_key=%s
                                   AND game=%s
                                   AND question_num=%s""",
                            (value=="+", player_key, game, question_num))
        elif field_tail == "answer_com":
            value = request.GET.get(field_name, 'nokey#@#')
            if value=='nokey#@#': continue
            
            cur.execute("""UPDATE """ + prefix + """_questions
                             SET is_answer_correct_comment=%s
                             WHERE player_key=%s
                               AND game=%s
                               AND question_num=%s""",
                        (value, player_key, game, question_num))
        else:
            continue

    cur.close()
    conn.connection.commit()

@login_required()
def player_game(request):
    prefix = request.GET.get('prefix')
    if not prefix: prefix = request.COOKIES.get('prefix', "")
    game = request.GET['game']
    player_key = request.GET['player_key']

    update_questions_table(request)

    html = player_game_table(player_key, game, prefix)

    response = render_to_response("myadm3/html_wrap.html", dict(
        html=html,
        title="Questions for player='%s', game=%s" % (player_key, game),
        prefix=prefix
    ))
    response.set_cookie("prefix", prefix)
    return response

@login_required()
def player_question_log(request):
    prefix = request.GET.get('prefix')
    if not prefix: prefix = request.COOKIES.get('prefix', "")
    game = request.GET['game']
    player_key = request.GET['player_key']
    question_num = request.GET['question_num']

    update_questions_table(request)

    cur = conn.cursor()
    cur.execute("""SELECT ts_game_start, sec_start_question, sec_duration
                     FROM """ + prefix + """_questions
                     WHERE player_key=%s
                       AND game=%s
                       AND question_num=%s
                """, (player_key, game, question_num))
    ts_game_start, sec_start_question, sec_duration = cur.fetchone()
    cur.close()
    if not sec_start_question: sec_start_question = 0

    html = "<h2>query</h2>"
    html += player_game_table(player_key, game, prefix, question_num)
    html += "\n\n<p></p>\n<p></p>\n\n"
    html += "<h2>log</h2>"

    sql = """SELECT ts, "action", param1, param2, game, method, uri, response_code, bytes_sent, time_taken_mks, referer, agent
               FROM """ + prefix + """_log
               WHERE player_key=%s
                 AND ts BETWEEN %s + interval %s AND %s + interval %s"""

    def cell_wide(v):
        return u'<div style="width:300px">' + unicode(v) + u'</div>'
    def cell_wide_overflow(v):
        return u'<div style="width:200px; max-height: 26px; overflow-x:hidden; overflow-y: scroll;">' + unicode(v) + u'</div>'

    html += render_sql_as_html_table(sql, (player_key, ts_game_start, str(sec_start_question) + ' second', ts_game_start, str(sec_start_question + sec_duration) + ' second'), {
        'param1': cell_wide,
        'uri': lambda v: '<div style="width:300px; max-height: 26px; overflow-x:hidden; overflow-y:scroll;"><a href="http://ir-ub.mathcs.emory.edu:8100%s" target="_blank">%s</a></div>' % (v, v),
        'referer': cell_wide_overflow,
        'agent': cell_wide_overflow,
    })

    response = render_to_response("myadm3/html_wrap.html", dict(
        html=html,
        title="Log for player='%s', game=%s, question=%s" % (player_key, game, question_num),
        prefix=prefix,
        form_action="player_game"
    ))
    response.set_cookie("prefix", prefix)
    return response

def render_sql_as_html_table(sql, sql_params, render_cell_map={}):
    try:
        cur = conn.cursor()
        #sql_mogrify = cur.mogrify(sql, sql_params)
        sql_mogrify = sql + "\n" + str(sql_params)
        cur.execute(sql, sql_params)
    except Exception, e:
        error_message = "Exception:" + str(e)
        error_message += "\n\n--- SQL\n"
        error_message += sql
        return '<p style="color:#C00000"><pre>' + error_message + '</pre></p>'

    column_num_to_render_func = {}
    column_names_list = []
    ncol = 0
    for name, type_code, display_size, internal_size, precision, scale, null_ok in cur.description:
        ncol += 1
        column_names_list.append(name)
        render_func = render_cell_map.get(name)
        argnum = 0
        if render_func:
            argnum = render_func.func_code.co_argcount
        column_num_to_render_func[ncol] = (render_func, argnum, name, type_code)

    html = StringIO.StringIO()
    html.write('<table border="1" cellpadding="0" cellspacing="0" class="sqltable">\n')
    html.write('<thead>\n')
    html.write('\t<td class="td_rownum">#</td>\n')
    for name, type_code, display_size, internal_size, precision, scale, null_ok in cur.description:
        html.write("\t<td>" + name.replace('_', ' ') + "</td>\n")
    html.write("</thead>\n")
    html.write("<tbody>\n")
    nrow = 0
    for row in cur:
        nrow += 1
        html.write("\t<tr>\n")
        html.write('\t\t<td class="td_rownum td_mod_' + str(nrow % 3) + '">' + str(nrow) + '</td>\n')
        ncell = 0
        for cell in row:
            ncell += 1
            render_func, argnum, name, type_code = column_num_to_render_func[ncell]
            if render_func:
                if argnum == 1: cell_content = apply(render_func, (cell, ))
                else:
                    rowdict = dict(zip(column_names_list, row))
                    cell_content = apply(render_func, (cell, rowdict))
            else:
                cell_content = cell
            html.write('\t\t<td class="td_mod_' + str(nrow % 3) + '">')
            html.write(cell_content)
            html.write('</td>\n')
        html.write("\t</tr>\n")
    html.write("</tbody>\n")
    html.write("</table>\n")

    html.write("""<p><p><a href="#" onclick="document.getElementById('div_sql_text').style.display='block';" style="font:xx-small Arial">show sql</a>\n""")
    html.write('<div id="div_sql_text" style="border:1px solid black; margin:30px; display:none"><pre>' + xml.sax.saxutils.escape(sql_mogrify) + "</pre></div>\n")

    cur.close()
    return html.getvalue()
