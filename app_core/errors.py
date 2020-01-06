from flask import render_template


def access_forbidden(_):
    return render_template('errors/403.html'), 403


def page_not_found(_):
    return render_template('errors/404.html'), 404


def internal_server_error(_):
    return render_template('errors/500.html'), 500
