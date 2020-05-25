from flask import Flask, render_template, redirect, url_for, flash, jsonify, request, session
from flask_mysqldb import MySQL
from blueprints.logout import logout_blueprint
from blueprints.register import register_blueprint
from blueprints.login import login_blueprint
from blueprints.add_comment import add_comment_blueprint
from blueprints.add_post import add_post_blueprint
from blueprints.remove import remove_blueprint
from blueprints.post import post_blueprint
from blueprints.remove_comment import remove_comment_blueprint
from blueprints.likesystem import likesystem_blueprint
from blueprints.editsystem import editsystem_blueprint
from blueprints.settings import settings_blueprint
from blueprints.follows import follows_blueprint
from forms import AddPostForm
from errors import page_not_found
from errors import method_not_allowed
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import string
import bcrypt
import random


app = Flask(__name__)
app.config.from_object('config')
mysql = MySQL(app)
mail = Mail(app)

s = URLSafeTimedSerializer('secretkey')

app.register_error_handler(404, page_not_found)
app.register_error_handler(405, method_not_allowed)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


@app.route('/', methods=['GET'])
def index():
    form = AddPostForm()
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM wpisy ORDER BY `id` DESC")
    posts = cur.fetchall()
    cur.execute("SELECT * FROM komentarze ORDER BY `id` DESC")
    comments = cur.fetchall()
    cur.execute("SELECT * FROM likes")
    likes = cur.fetchall()
    cur.close()
    return render_template('index.html', posts=posts, comments=comments, likes=likes, form=form)


@app.route('/popularne', methods=['GET'])
def populary():
    form = AddPostForm()
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM wpisy ORDER BY `lajki` DESC")
    posts = cur.fetchall()
    cur.execute("SELECT * FROM komentarze ORDER BY `id` DESC")
    comments = cur.fetchall()
    cur.execute("SELECT * FROM likes")
    likes = cur.fetchall()
    cur.close()
    return render_template('index.html', posts=posts, comments=comments, likes=likes, form=form)


@app.route('/profil/<nick>', methods=['GET'])
def profil(nick):
    cur = mysql.connection.cursor()
    cur.execute("SELECT description FROM users WHERE login=%s", (nick,))
    check_user_exists = cur.fetchone()
    if check_user_exists:
        cur.execute("SELECT * FROM wpisy WHERE autor=%s ORDER BY `id` DESC", (nick,))
        posts = cur.fetchall()
        count_posts = len(list(cur))
        cur.execute("SELECT * FROM komentarze ORDER BY `id` DESC")
        comments = cur.fetchall()
        cur.execute("SELECT * FROM komentarze WHERE autor=%s", (nick,))
        count_comments = len(list(cur))
        cur.execute("SELECT * FROM likes")
        likes = cur.fetchall()
        description = check_user_exists['description']
        cur.close()
        return render_template('profil.html', posts=posts, comments=comments, likes=likes, nick=nick,
                               countComments=count_comments, countPosts=count_posts, description=description)
    flash("Nie znaleziono użytkownika z takim loginem")
    return redirect(url_for('index'))


@app.route('/tag/<tagname>')
def tag(tagname):
    form = AddPostForm()
    list_posts = []
    cur = mysql.connection.cursor()
    cur.execute("SELECT post_id FROM tags WHERE tag=%s", (tagname,))
    tags = cur.fetchall()
    if tags:
        for post_id in tags:
            list_posts.append(post_id['post_id'])
        cur.execute("SELECT * FROM wpisy WHERE id IN %s ORDER BY `id` DESC", (list_posts,))
        posts = cur.fetchall()
        cur.execute("SELECT * FROM komentarze WHERE post_id IN %s ORDER BY `id` DESC", (list_posts,))
        comments = cur.fetchall()
        cur.execute("SELECT * FROM likes WHERE post_id IN %s", (list_posts,))
        likes = cur.fetchall()
        cur.execute("SELECT  * FROM obserwowanetagi")
        follows = cur.fetchall()
        cur.close()
        return render_template('index.html', posts=posts, comments=comments, likes=likes, form=form, tag=tagname,
                               follows=follows)
    flash("Taki tag jeszcze nie istnieje")
    return redirect(url_for('index'))


@app.route('/likes', methods=['POST'])
def likes():
    users = []
    post_id = request.form['post_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id FROM likes WHERE post_id=%s", (post_id,))
    likes = cur.fetchall()
    if likes:
        for x in likes:
            #  users.append('<a href="/profil/'+x['user_id']+'"'+'>'+x['user_id']+'</a>')
            users.append(x['user_id'])
        return jsonify({'likes': ", ".join(users)})
    return jsonify({'likes': 'Nikt jeszcze nie polubił tego wpisu'})


@app.route('/reset', methods=['POST'])
def reset():
    email = request.form['email']
    if email:
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM users WHERE email=%s", (email,))
        userEmail = cur.fetchone()
        if userEmail:
            token = s.dumps(email, salt='password-reset')
            msg = Message('mikroblog.ct8.pl: resetuj hasło', sender='mikroblog@ivall.pl', recipients=[email])
            link = url_for('reset_token', token=token, _external=True)
            msg.body = 'Otrzymano prośbę o zresetowanie hasła do serwisu https://mikroblog.ct8.pl, link do resetowania hasła: {}'.format(
                link)
            mail.send(msg)
            flash("Wysłano link do resetowania hasła na podany email, link jest ważny 10 minut")
            return redirect(url_for('login_blueprint.login'))
        flash("Nie znaleziono użytkownika z takim emailem")
        return redirect(url_for('login_blueprint.login'))
    flash("Nie podałeś adresu email")
    return redirect(url_for('login_blueprint.login'))


@app.route('/reset/<token>')
def reset_token(token):
    if 'login' not in session:
        try:
            email = s.loads(token, salt='password-reset', max_age=600)
        except SignatureExpired:
            flash("Token jest już nieważny")
            return redirect(url_for('login_blueprint.login'))
        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(25))
        password_for_hash = password.encode('utf-8')
        hash_password = bcrypt.hashpw(password_for_hash, bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (hash_password, email,))
        mysql.connection.commit()
        cur.close()
        msg = Message('mikroblog.ct8.pl: nowe hasło', sender='mikroblog@ivall.pl', recipients=[email])
        msg.body = 'Twoje nowe hasło do logowania: {}'.format(password)
        mail.send(msg)
        flash("Wysłano nowe hasło na emaila")
        return redirect(url_for('login_blueprint.login'))
    return redirect(url_for('index'))


app.register_blueprint(follows_blueprint)

app.register_blueprint(settings_blueprint)

app.register_blueprint(editsystem_blueprint)

app.register_blueprint(likesystem_blueprint)

app.register_blueprint(post_blueprint)

app.register_blueprint(remove_blueprint)

app.register_blueprint(add_post_blueprint)

app.register_blueprint(add_comment_blueprint)

app.register_blueprint(register_blueprint)

app.register_blueprint(login_blueprint)

app.register_blueprint(logout_blueprint)

app.register_blueprint(remove_comment_blueprint)

if __name__ == '__main__':
    app.run()
