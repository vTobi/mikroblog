import bcrypt
from flask import session, url_for, redirect, flash, render_template, Blueprint
from .. import mysql
from ..utils.forms import ChangeEmail, ChangePassword, ChangeDescription

settings_blueprint = Blueprint('settings_blueprint', __name__)


@settings_blueprint.route('/ustawienia', methods=['GET'])
def show_settings():
    if 'login' in session:
        formr = ChangeEmail()
        formp = ChangePassword()
        formo = ChangeDescription()
        cur = mysql.connection.cursor()
        cur.execute("SELECT description FROM users WHERE login=%s", (session['login'],))
        old_description = cur.fetchone()
        formo.description.data = old_description['description']
        return render_template('ustawienia.html', formr=formr, formp=formp, formo=formo)
    return redirect(url_for('index_blueprint.index'))


@settings_blueprint.route('/zmienemail', methods=['POST'])
def change_email():
    if 'login' in session:
        formr = ChangeEmail()
        if formr.validate_on_submit():
            email = formr.email.data
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s",(email,))
            check_email = cur.fetchone()
            if not check_email:
                cur.execute("UPDATE users SET email=%s WHERE login=%s", (email, session['login'],))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('index_blueprint.index'))
            flash("Użytkownik z takim emailem już istnieje")
            return redirect(url_for('index_blueprint.index'))
        flash("Wystąpił błąd walidacji")
        return redirect(url_for('index_blueprint.index'))
    flash("Wystąpił błąd")
    return redirect(url_for('index_blueprint.index'))


@settings_blueprint.route('/zmienhaslo', methods=['POST'])
def change_password():
    if 'login' in session:
        formp = ChangePassword()
        if formp.validate_on_submit():
            old_password = formp.oldpassword.data.encode('utf-8')
            cur = mysql.connection.cursor()
            cur.execute("SELECT password FROM users WHERE login=%s", (session['login'],))
            check_old_password = cur.fetchone()
            cur.close()
            if bcrypt.hashpw(old_password, check_old_password['password'].encode('utf-8')) == check_old_password['password'].encode('utf-8'):
                password = formp.password.data.encode('utf-8')
                hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET password=%s WHERE login=%s", (hash_password, session['login'],))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('index_blueprint.index'))
            flash("Niepoprawne stare hasło")
            return redirect(url_for('index_blueprint.index'))
        flash("Wystąpił błąd")
        return redirect(url_for('index_blueprint.index'))
    flash("Wystąpił błąd")
    return redirect(url_for('index_blueprint.index'))


@settings_blueprint.route('/zmienopis', methods=['POST'])
def change_description():
    if 'login' in session:
        formo = ChangeDescription()
        if formo.validate_on_submit():
            description = formo.description.data
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET description=%s WHERE login=%s", (description, session['login'],))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('user_profile_blueprint.profil', nick=session['login']))
        flash("Wystąpił błąd, maksymlna długość opisu wynosi 50 znaków.")
        return redirect(url_for('index_blueprint.index'))
    flash("Nie jesteś zalogowany")
    return redirect(url_for('login_blueprint.login'))
