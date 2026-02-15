import os
import sys

import click
from dotenv import load_dotenv
from flask_migrate import Migrate, upgrade

from app_core import create_app, db
from app_core.models import User, Role, Gender, Permission, Follow, Comment, Post

dot_env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dot_env_path):
    load_dotenv(dot_env_path)

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include='app_core/*')
    COV.start()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Gender=Gender, Permission=Permission,
                User=User, Role=Role, Follow=Follow, Post=Post, Comment=Comment)


@app.cli.command()
@click.option('--code-coverage/--no-code-coverage', default=False, help='Run tests under code coverage.')
@click.argument('test_names', nargs=-1)
def test(code_coverage, test_names):
    """Run the unit tests."""
    if code_coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))

    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        base_dir = os.path.abspath(os.path.dirname(__file__))
        cov_dir = os.path.join(base_dir, 'test_result/coverage')
        COV.html_report(directory=cov_dir)
        print('HTML version: file://%s/index.html' % cov_dir)
        COV.erase()


@app.cli.command()
@click.option('--length', default=25, help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None, help='Directory where profiler data files are saved.')
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.middleware.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
    app.run()


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # migrate database to latest revision
    upgrade()

    # create or update genders
    Gender.insert_genders()

    # create or update user roles
    Role.insert_roles()

    # ensure all users are following themselves
    User.add_self_follows()
