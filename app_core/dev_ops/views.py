from flask import current_app, abort, request

from app_core.dev_ops import dev_ops


@dev_ops.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(403)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'
