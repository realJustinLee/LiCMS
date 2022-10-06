from flask import jsonify, request, g, url_for, current_app

from app_core import db
from app_core.api import api
from app_core.api.decorators import permission_required
from app_core.api.errors import forbidden
from app_core.models import Post, Permission


@api.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(page=page, per_page=current_app.config['LICMS_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    _prev = None
    if pagination.has_prev:
        _prev = url_for('api.get_posts', page=page - 1)
    _next = None
    if pagination.has_next:
        _next = url_for('api.get_posts', page=page + 1)
    return jsonify({
        'posts': [_post.to_json() for _post in posts],
        'prev': _prev,
        'next': _next,
        'count': pagination.total
    })


@api.route('/posts/<int:post_id>')
def get_post(post_id):
    _post = Post.query.get_or_404(post_id)
    return jsonify(_post.to_json())


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    _post = Post.from_json(request.json)
    _post.author = g.current_user
    db.session.add(_post)
    db.session.commit()
    return jsonify(_post.to_json()), 201, {'Location': url_for('api.get_post', post_id=_post.id)}


@api.route('/posts/<int:post_id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_post(post_id):
    _post = Post.query.get_or_404(post_id)
    if g.current_user != _post.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    _post.title = request.json.get('title', _post.body)
    _post.body = request.json.get('body', _post.body)
    db.session.add(_post)
    db.session.commit()
    return jsonify(_post.to_json())
