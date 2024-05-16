from flask import Flask, session, abort


class Hepatitis_C:
    def __init__(self, app: Flask) -> None:
        self.users = app

    @property
    def is_authenticated(self):
        return not not session.get("current_user")

    def login_required(self, fn):
        def run(*a, **kwa):
            if not self.is_authenticated:
                abort(401)
            return fn(*a, **kwa)

        return run

    @property
    def current_user(self):
        return session['current_user']

    def login_user(self, user):
        session['current_user'] = user

    def logout_user(self):
        if self.is_authenticated:
            session.pop('current_user')

