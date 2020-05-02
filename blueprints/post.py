from flask import Flask, Blueprint, redirect, url_for, render_template
from flask_mysqldb import MySQL
from forms import AddPostForm
post_blueprint = Blueprint('post_blueprint', __name__)

app = Flask(__name__)
app.config.from_object('config')
mysql = MySQL(app)


@post_blueprint.route('/wpis/<int:postid>', methods=['GET'])
def wpis(postid):
    form = AddPostForm()
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM wpisy WHERE id=%s ORDER BY `id` DESC",(postid,))
    post = cur.fetchall()
    if post:
        cur.execute("SELECT * FROM komentarze WHERE post_id=%s ORDER BY `id` DESC",(postid,))
        comments = cur.fetchall()
        cur.execute("SELECT * FROM likes WHERE post_id=%s",(postid,))
        likes = cur.fetchall()
        cur.close()
        return render_template('index.html', posts=post, comments=comments, likes=likes, form=form)
    return redirect(url_for('index'))