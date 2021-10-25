from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def permission_required(role_required):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_allowed(role_required):
                return redirect(url_for(current_user.role.name + '.dashboard', message="Whoops! We couldn't find that page!"))
            return f(*args, **kwargs)
        return decorated_function

    return decorator
