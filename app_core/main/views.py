from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app_core import db
from app_core.decorators import admin_required
from app_core.main import main
from app_core.main.forms import EditProfileForm, EditProfileAdminForm, PostForm
from app_core.models import User, Role, Permission, Post


@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico', _external=True))


@main.route('/', methods=['GET', 'POST'])
def index():
    _posts = Post.query.order_by(Post.timestamp.desc()).limit(8).all()
    _users = User.query.order_by(User.member_since.desc()).limit(8).all()
    return render_template('index.html', current_time=datetime.utcnow(), posts=_posts, users=_users)


@main.route('/user', methods=['GET', 'POST'])
@login_required
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(page, per_page=current_app.config[
        'LICMS_POSTS_PER_PAGE'], error_out=False)
    _users = pagination.items
    return render_template('users.html', users=_users, pagination=pagination)


@main.route('/user/<user_id>')
@login_required
def user(user_id):
    _user = User.query.filter_by(id=user_id).first_or_404()
    _posts = _user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=_user, posts=_posts)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.gender = form.gender.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.gender.data = current_user.gender_id
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    _user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=_user)
    if form.validate_on_submit():
        _user.email = form.email.data
        _user.confirmed = form.confirmed.data
        _user.role = Role.query.get(form.role.data)
        _user.name = form.name.data
        _user.gender = form.gender.data
        _user.location = form.location.data
        _user.about_me = form.about_me.data
        db.session.add(_user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=_user.username))
    form.email.data = _user.email
    form.confirmed.data = _user.confirmed
    form.role.data = _user.role_id
    form.name.data = _user.name
    form.gender.data = _user.gender_id
    form.location.data = _user.location
    form.about_me.data = _user.about_me
    return render_template('edit_profile.html', form=form, user=_user)


@main.route('/post', methods=['GET', 'POST'])
@login_required
def posts():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.posts'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config[
        'LICMS_POSTS_PER_PAGE'], error_out=False)
    _posts = pagination.items
    return render_template('posts.html', form=form, posts=_posts, pagination=pagination)
