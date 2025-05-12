from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request, current_app, abort, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import record_queries
from sqlalchemy import asc, desc, func

from app_core import db
from app_core.decorators import admin_required, permission_required
from app_core.main import main
from app_core.main.forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, PasteForm
from app_core.models import User, Role, Permission, Post, Gender, Follow, Comment, Paste


@main.after_app_request
def after_request(response):
    for query in record_queries.get_recorded_queries():
        if query.duration >= current_app.config['LICMS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nLocation: %s\n' % (
                query.statement, query.parameters, query.duration, query.location))
    return response


@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico', _external=True))


@main.route('/xianglin')
@login_required
def xianglin():
    return render_template('hidden_letter/letter_to_xianglin.html')


@main.route('/', methods=['GET', 'POST'])
def index():
    _show_followed = False
    if current_user.is_authenticated:
        _show_followed = bool(request.cookies.get('show_followed', ''))
    if _show_followed:
        post_title = 'Latest Followed Posts'
        post_link = 'Show All Followed Posts'
        query = current_user.followed_posts
    else:
        post_title = 'Latest Posts'
        post_link = 'Show All Posts'
        query = Post.query
    _posts = query.order_by(desc(Post.timestamp)).limit(8).all()
    post_count_sub = Post.query.group_by(Post.author_id).with_entities(Post.author_id, func.count(Post.author_id).label(
        'post_count')).subquery()
    _users = db.session.query(User).join(post_count_sub, User.id == post_count_sub.c.author_id).order_by(
        desc(post_count_sub.c.post_count)).limit(8).all()
    return render_template('index.html', current_time=datetime.now(timezone.utc), show_followed=_show_followed,
                           posts=_posts, post_title=post_title, post_link=post_link, users=_users,
                           endpoint='main.index')


@main.route('/user', methods=['GET', 'POST'])
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(desc(User.member_since)).paginate(page=page, per_page=current_app.config[
        'LICMS_USERS_PER_PAGE'], error_out=False)
    _users = pagination.items
    return render_template('users.html', title="All authors", users=_users, pagination=pagination,
                           endpoint='main.users')


@main.route('/user/<int:user_id>')
def user(user_id):
    _user = User.query.filter_by(id=user_id).first_or_404()
    _posts = _user.posts.order_by(desc(Post.timestamp)).all()
    return render_template('user.html', user=_user, posts=_posts)


@main.route('/user/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.gender = Gender.query.get(form.gender.data)
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your profile has been updated.', 'alert-success')
        return redirect(url_for('main.user', user_id=current_user.id))
    form.name.data = current_user.name
    form.gender.data = current_user.gender_id
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    _user = db.get_or_404(User, user_id)
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
        flash('The profile has been updated.', 'alert-success')
        return redirect(url_for('main.user', user_id=_user.id))
    form.email.data = _user.email
    form.confirmed.data = _user.confirmed
    form.role.data = _user.role_id
    form.name.data = _user.name
    form.gender.data = _user.gender_id
    form.location.data = _user.location
    form.about_me.data = _user.about_me
    return render_template('edit_profile.html', form=form, user=_user, is_adm=True)


@main.route('/all/<_next>')
@login_required
def show_all(_next):
    resp = make_response(redirect(url_for(_next)))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed/<_next>')
@login_required
def show_followed(_next):
    resp = make_response(redirect(url_for(_next)))
    resp.set_cookie('show_followed', 'True', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/post', methods=['GET', 'POST'])
def posts():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        _post = Post(title=form.title.data, body=form.body.data, author=current_user)
        db.session.add(_post)
        db.session.commit()
        return redirect(url_for('main.posts'))
    _show_followed = False
    if current_user.is_authenticated:
        _show_followed = bool(request.cookies.get('show_followed', ''))
    if _show_followed:
        title = 'Followed Posts'
        query = current_user.followed_posts
    else:
        title = 'All Posts'
        query = Post.query
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(desc(Post.timestamp)).paginate(page=page,
                                                               per_page=current_app.config['LICMS_POSTS_PER_PAGE'],
                                                               error_out=False)
    _posts = pagination.items
    return render_template('posts.html', title=title, form=form, show_followed=_show_followed, posts=_posts,
                           pagination=pagination, endpoint='main.posts')


@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    _post = db.get_or_404(Post, post_id)
    form = CommentForm()
    if current_user.can(Permission.COMMENT) and form.validate_on_submit():
        comment = Comment(body=form.body.data, post=_post, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been published!", 'alert-success')
        # page=-1 takes you to the last page that contains your comment
        return redirect(url_for('main.post', post_id=post_id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = ((_post.comments.count() - 1) // current_app.config['LICMS_COMMENTS_PER_PAGE']) + 1
    pagination = _post.comments.order_by(asc(Comment.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_COMMENTS_PER_PAGE'], error_out=False)
    _comments = pagination.items
    return render_template('post.html', post=_post, form=form, comments=_comments, pagination=pagination,
                           endpoint='main.post', page=page, sample=page)


@main.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    _post = db.get_or_404(Post, post_id)
    if current_user != _post.author and not current_user.is_administrator():
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        _post.title = form.title.data
        _post.body = form.body.data
        db.session.add(_post)
        db.session.commit()
        flash('The post has been updated.', 'alert-success')
        return redirect(url_for('main.post', post_id=_post.id))
    form.title.data = _post.title
    form.body.data = _post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<int:user_id>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(user_id):
    _user = User.query.filter_by(id=user_id).first()
    if _user is None:
        flash('Invalid user.', 'alert-danger')
        return redirect(url_for('main.index'))
    if current_user.is_following(_user):
        flash('You are already following this user.')
        return redirect(url_for('main.user', user_id=user_id))
    current_user.follow(_user)
    flash('You are now following %s.' % _user.name, 'alert-success')
    return redirect(url_for('main.user', user_id=user_id))


@main.route('/unfollow/<int:user_id>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(user_id):
    _user = User.query.filter_by(id=user_id).first()
    if _user is None:
        flash('Invalid user.', 'alert-danger')
        return redirect(url_for('main.index'))
    if not current_user.is_following(_user):
        flash('You are not following this user.')
        return redirect(url_for('main.user', user_id=user_id))
    current_user.unfollow(_user)
    flash('You are not following %s anymore.' % _user.name, 'alert-success')
    return redirect(url_for('main.user', user_id=user_id))


@main.route('/followers/<int:user_id>')
def followers(user_id):
    _user = User.query.get(user_id)
    if _user is None:
        flash('Invalid user.', 'alert-danger')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = _user.followers.order_by(desc(Follow.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_USERS_PER_PAGE'], error_out=False)
    _followers = [item.follower for item in pagination.items if item.follower != _user]
    return render_template('users.html', title="Followers of " + _user.name, users=_followers, pagination=pagination,
                           endpoint='main.followers', user_id=user_id)


@main.route('/followed_by/<int:user_id>')
def followed_by(user_id):
    _user = User.query.get(user_id)
    if _user is None:
        flash('Invalid user.', 'alert-danger')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = _user.followed.order_by(desc(Follow.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_USERS_PER_PAGE'], error_out=False)
    _followed = [item.followed for item in pagination.items if item.followed != _user]
    return render_template('users.html', title="Users followed by " + _user.name, users=_followed,
                           pagination=pagination, endpoint='main.followers', user_id=user_id)


@main.route('/about')
def about():
    return render_template('about.html')


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(desc(Comment.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_COMMENTS_PER_PAGE'], error_out=False)
    _comments = pagination.items
    return render_template('moderate.html', comments=_comments, pagination=pagination, endpoint='main.moderate',
                           page=page)


@main.route('/moderate/enable/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(comment_id):
    _comment = db.get_or_404(Comment, comment_id)
    _comment.disabled = False
    db.session.add(_comment)
    db.session.commit()
    in_post = request.args.get('in_post', False, type=lambda v: v.lower() == 'true')
    page = request.args.get('page', 1, type=int)
    if in_post:
        return redirect(url_for('main.post', post_id=_comment.post_id, page=page))
    else:
        return redirect(url_for('main.moderate', page=page))


@main.route('/moderate/disable/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(comment_id):
    _comment = db.get_or_404(Comment, comment_id)
    _comment.disabled = True
    db.session.add(_comment)
    db.session.commit()
    in_post = request.args.get('in_post', False, type=lambda v: v.lower() == 'true')
    page = request.args.get('page', 1, type=int)
    if in_post:
        return redirect(url_for('main.post', post_id=_comment.post_id, page=page))
    else:
        return redirect(url_for('main.moderate', page=page))


@main.route('/paste', methods=['GET', 'POST'])
@login_required
def pastes():
    form = PasteForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        _paste = Paste(title=form.title.data, body=form.body.data, expiry=form.expiry.data, disabled=form.disabled.data,
                       author=current_user)
        db.session.add(_paste)
        db.session.commit()
        flash('The paste has been posted.', 'alert-success')
        return redirect(url_for('main.paste', paste_id=_paste.id))
    page = request.args.get('page', 1, type=int)
    pagination = current_user.pastes.order_by(desc(Paste.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_PASTES_PER_PAGE'], error_out=False)
    _pastes = pagination.items
    return render_template('pastes.html', title="My Pastes", form=form, pastes=_pastes, pagination=pagination,
                           endpoint='main.pastes')


@main.route('/paste/<int:paste_id>', methods=['GET'])
def paste(paste_id):
    _paste = db.get_or_404(Paste, paste_id)
    if _paste.author != current_user and not current_user.is_administrator():
        if _paste.disabled:
            abort(403)
        if _paste.expiry and datetime.now() >= _paste.expiry:
            abort(404)
    return render_template('paste.html', paste=_paste, current_time=datetime.now())


@main.route('/paste/edit/<int:paste_id>', methods=['GET', 'POST'])
@login_required
def edit_paste(paste_id):
    _paste = db.get_or_404(Paste, paste_id)
    if current_user != _paste.author and not current_user.is_administrator():
        abort(403)
    form = PasteForm()
    if form.validate_on_submit():
        _paste.title = form.title.data
        _paste.body = form.body.data
        _paste.expiry = form.expiry.data
        _paste.disabled = form.disabled.data
        db.session.add(_paste)
        db.session.commit()
        flash('The paste has been updated.', 'alert-success')
        return redirect(url_for('main.paste', paste_id=_paste.id))
    form.title.data = _paste.title
    form.body.data = _paste.body
    form.expiry.data = _paste.expiry
    form.disabled.data = _paste.disabled
    return render_template('edit_paste.html', form=form)


@main.route('/paste/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate_pastes():
    page = request.args.get('page', 1, type=int)
    pagination = Paste.query.order_by(desc(Paste.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_PASTES_PER_PAGE'], error_out=False)
    _pastes = pagination.items
    return render_template('moderate_pastes.html', title="All Pastes", pastes=_pastes, pagination=pagination,
                           endpoint='main.moderate_pastes', page=page)


@main.route('/paste/moderate/enable/<int:paste_id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable_paste(paste_id):
    _paste = db.get_or_404(Paste, paste_id)
    _paste.disabled = False
    db.session.add(_paste)
    db.session.commit()
    user_view = request.args.get('user_view', False, type=lambda v: v.lower() == 'true')
    page = request.args.get('page', 1, type=int)
    if user_view:
        return redirect(url_for('main.pastes', user_id=_paste.author_id, page=page))
    else:
        return redirect(url_for('main.moderate_pastes', page=page))


@main.route('/paste/moderate/disable/<int:paste_id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable_paste(paste_id):
    _paste = db.get_or_404(Paste, paste_id)
    _paste.disabled = True
    db.session.add(_paste)
    db.session.commit()
    user_view = request.args.get('user_view', False, type=lambda v: v.lower() == 'true')
    page = request.args.get('page', 1, type=int)
    if user_view:
        return redirect(url_for('main.pastes', user_id=_paste.author_id, page=page))
    else:
        return redirect(url_for('main.moderate_pastes', page=page))
