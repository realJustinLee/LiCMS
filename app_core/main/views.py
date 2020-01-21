from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user

from app_core import db
from app_core.decorators import admin_required, permission_required
from app_core.main import main
from app_core.main.forms import EditProfileForm, EditProfileAdminForm, PostForm
from app_core.models import User, Role, Permission, Post, Gender, Follow


@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico', _external=True))


@main.route('/', methods=['GET', 'POST'])
def index():
    _posts = Post.query.order_by(Post.timestamp.desc()).limit(8).all()
    _users = User.query.order_by(User.member_since.desc()).limit(8).all()
    return render_template('index.html', current_time=datetime.utcnow(), posts=_posts, users=_users)


@main.route('/user', methods=['GET', 'POST'])
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(page, per_page=current_app.config[
        'LICMS_USERS_PER_PAGE'], error_out=False)
    _users = pagination.items
    return render_template('users.html', title='All authors', users=_users, pagination=pagination,
                           endpoint='main.users')


@main.route('/user/<user_id>')
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
        current_user.gender = Gender.query.get(form.gender.data)
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('main.user', user_id=current_user.id))
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
        _user.gender = Gender.query.get(form.gender.data)
        _user.location = form.location.data
        _user.about_me = form.about_me.data
        db.session.add(_user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('main.user', user_id=_user.id))
    form.email.data = _user.email
    form.confirmed.data = _user.confirmed
    form.role.data = _user.role_id
    form.name.data = _user.name
    form.gender.data = _user.gender_id
    form.location.data = _user.location
    form.about_me.data = _user.about_me
    return render_template('edit_profile.html', form=form, user=_user)


@main.route('/post', methods=['GET', 'POST'])
def posts():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        _post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(_post)
        db.session.commit()
        return redirect(url_for('main.posts'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config[
        'LICMS_POSTS_PER_PAGE'], error_out=False)
    _posts = pagination.items
    return render_template('posts.html', title='All Posts', form=form, posts=_posts, pagination=pagination,
                           endpoint='main.posts')


@main.route('/post/<int:post_id>')
def post(post_id):
    _post = Post.query.get_or_404(post_id)
    return render_template('post.html', posts=[_post])


@main.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    _post = Post.query.get_or_404(post_id)
    if current_user != _post.author and not current_user.is_administrator():
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        _post.body = form.body.data
        db.session.add(_post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('main.post', post_id=_post.id))
    form.body.data = _post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<user_id>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(user_id):
    _user = User.query.filter_by(id=user_id).first()
    if _user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if current_user.is_following(_user):
        flash('You are already following this user.')
        return redirect(url_for('main.user', user_id=user_id))
    current_user.follow(_user)
    flash('You are now following %s.' % _user.name)
    return redirect(url_for('main.user', user_id=user_id))


@main.route('/unfollow/<user_id>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(user_id):
    _user = User.query.filter_by(id=user_id).first()
    if _user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if not current_user.is_following(_user):
        flash('You are not following this user.')
        return redirect(url_for('main.user', user_id=user_id))
    current_user.unfollow(_user)
    flash('You are not following %s anymore.' % _user.name)
    return redirect(url_for('main.user', user_id=user_id))


@main.route('/followers/<user_id>')
def followers(user_id):
    _user = User.query.filter_by(id=user_id).first()
    if _user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = _user.followers.order_by(Follow.timestamp.desc()).paginate(page, per_page=current_app.config[
        'LICMS_USERS_PER_PAGE'], error_out=False)
    _followers = [item.follower for item in pagination.items]
    return render_template('users.html', title="Followers of " + _user.name, users=_followers, pagination=pagination,
                           endpoint='main.followers', user_id=user_id)


@main.route('/followed_by/<user_id>')
def followed_by(user_id):
    _user = User.query.filter_by(id=user_id).first()
    if _user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = _user.followed.order_by(Follow.timestamp.desc()).paginate(page, per_page=current_app.config[
        'LICMS_USERS_PER_PAGE'], error_out=False)
    _followed = [item.followed for item in pagination.items]
    return render_template('users.html', title="Users followed by " + _user.name, users=_followed,
                           pagination=pagination, endpoint='main.followers', user_id=user_id)
