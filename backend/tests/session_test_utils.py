from app.session import build_session_cookie_value


def session_cookie(user_id: int) -> dict[str, str]:
    return {"mufasa_session": build_session_cookie_value(user_id)}
