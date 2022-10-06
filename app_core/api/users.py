from flask import jsonify, request, current_app, url_for
from sqlalchemy import desc

from app_core.api import api
from app_core.models import User, Post


@api.route('/users/<int:user_id>')
def get_user(user_id):
    _user = User.query.get_or_404(user_id)
    return jsonify(_user.to_json())


@api.route('/users/<int:user_id>/posts/')
def get_user_posts(user_id):
    _user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    pagination = _user.posts.order_by(desc(Post.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    _prev = None
    if pagination.has_prev:
        _prev = url_for('api.get_user_posts', user_id=user_id, page=page - 1)
    _next = None
    if pagination.has_next:
        _next = url_for('api.get_user_posts', user_id=user_id, page=page + 1)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': _prev,
        'next': _next,
        'count': pagination.total
    })


@api.route('/users/<int:user_id>/timeline/')
def get_user_followed_posts(user_id):
    _user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    pagination = _user.followed_posts.order_by(desc(Post.timestamp)).paginate(page=page, per_page=current_app.config[
        'LICMS_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    _prev = None
    if pagination.has_prev:
        _prev = url_for('api.get_user_followed_posts', user_id=user_id, page=page - 1)
    _next = None
    if pagination.has_next:
        _next = url_for('api.get_user_followed_posts', user_id=user_id, page=page + 1)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': _prev,
        'next': _next,
        'count': pagination.total
    })
