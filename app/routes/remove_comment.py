from flask import request, session, redirect, abort
from .. import mysql
from flask import Blueprint
remove_comment_blueprint = Blueprint('remove_comment_blueprint', __name__)


@remove_comment_blueprint.route('/removekom', methods=['POST'])
def remove_comment():
    comment_id = request.form['kom_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM komentarze WHERE id=%s", (comment_id,))
    check_remover = cur.fetchone()
    if check_remover and check_remover['autor'] == session['login'] or check_remover and 'admin' in session:
        cur.execute("DELETE FROM komentarze WHERE id=%s", (comment_id,))
        mysql.connection.commit()
        cur.close()
        return redirect(request.referrer)
    return abort(401)
