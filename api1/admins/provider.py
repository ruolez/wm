import datetime
import uuid

from passlib.context import CryptContext
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

from .model import Article, AdminUserProject
from ..users.model import Items_tbl, AdminUserProject_admin, UsersSessions
from .. import select, insert, delete, engine, X_TOKEN, update, and_
from sqlalchemy.orm import Session
from api1.config import MAX_SESSIONS_PER_USER, HARD_EXPIRATION_HOURS
from api1.constants import MINIMAL_LENGTH_USERNAME
from api1.helpers import get_client_ip


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def user_config():
    with Session(engine["DB_admin"]) as session:
        stmt = select(AdminUserProject_admin.__table__.columns)
        rows = session.execute(stmt).mappings().all()

        user_dict_temp = {}
        users_roles = {}
        for row in rows:
            record = dict(row)
            username_key = record["username"].strip().lower()
            user_dict_temp[username_key] = record
            users_roles[username_key] = {
                "name": username_key,
                "statususer": record["statususer"],
            }

        return user_dict_temp, users_roles

user_dict, users = user_config()

def guid():
    return str(uuid.uuid4())

def now_minus_5h():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=5)

def now_minus_5h_plus_130m():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=5) + datetime.timedelta(minutes=130)

class MyAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        user_dict, users = user_config()

        username = username.strip().lower()
        if len(username) < MINIMAL_LENGTH_USERNAME:
            raise FormValidationError({"username": f"Ensure username has at least {MINIMAL_LENGTH_USERNAME} characters"})
        if username not in user_dict:
            raise LoginFailed("Invalid username or password")

        stored_hash = user_dict[username]["password"]
        if not stored_hash.startswith("$2"):
            if password != stored_hash:
                raise LoginFailed("Invalid username or password")
            new_hash = pwd_context.hash(password)
            with Session(engine["DB_admin"]) as session:
                stmt_update = (
                    update(AdminUserProject_admin)
                    .values(password=new_hash)
                    .where(AdminUserProject_admin.username == username)
                )
                session.execute(stmt_update)
                session.commit()
            user_dict[username]["password"] = new_hash
            is_valid = True
        else:
            is_valid = pwd_context.verify(password, stored_hash)

        if not is_valid:
            raise LoginFailed("Invalid username or password")

        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        with Session(engine["DB_admin"]) as session:
            active_sessions = session.query(UsersSessions).filter(
                UsersSessions.user_name == username,
                UsersSessions.Flag1 == 1
            ).order_by(UsersSessions.created_at.asc()).all()

            if len(active_sessions) >= MAX_SESSIONS_PER_USER:
                to_delete = active_sessions[:len(active_sessions) - MAX_SESSIONS_PER_USER + 1]
                for s in to_delete:
                    session.delete(s)
                session.commit()

            # new session
            numsid = guid()
            request.session.clear()
            request.session.update({"username": username, "sessionid": numsid})

            now = datetime.datetime.utcnow()
            stmt_insert = insert(UsersSessions).values(
                session_id=numsid,
                user_name=username,
                created_at=now,
                updated_at=now,
                expires_at=now + datetime.timedelta(minutes=130),
                browser_info=user_agent,
                Dop1=client_ip,
                Flag1=True
            )
            session.execute(stmt_insert)
            session.commit()

        response.set_cookie(
            key="session",
            value=request.session.get("sessionid"),
            httponly=True,
            samesite="Strict"
        )

        return response

    async def is_authenticated(self, request) -> bool:
        if "x-token" in request.headers and request.headers["x-token"] == X_TOKEN:
            request.state.user = {"name": "system", "statususer": "admin"}
            return True

        uname = request.session.get("username")
        sid = request.session.get("sessionid")
        if not (uname and sid):
            return False

        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        with Session(engine["DB_admin"]) as session:
            session_obj = session.query(UsersSessions).filter(
                UsersSessions.session_id == sid,
                UsersSessions.user_name == uname,
                UsersSessions.Flag1 == 1
            ).first()

            if not session_obj:
                return False

            now = datetime.datetime.utcnow()

            # hard-expiration check
            if session_obj.created_at and (
                session_obj.created_at + datetime.timedelta(hours=HARD_EXPIRATION_HOURS) < now
            ):
                session.delete(session_obj)
                session.commit()
                return False

            # check of sliding-expiration
            if session_obj.expires_at and session_obj.expires_at < now:
                session.delete(session_obj)
                session.commit()
                return False

            # ip and user-agent check
            if (session_obj.browser_info and session_obj.browser_info != user_agent) or \
            (session_obj.Dop1 and session_obj.Dop1 != client_ip):
                return False

            # update of the sliding-expiration
            session_obj.updated_at = now
            session_obj.expires_at = now + datetime.timedelta(minutes=130)
            session.commit()

        user_rec = users.get(uname)
        if not user_rec:
            _, users_map = user_config()
            user_rec = users_map.get(uname)

        if not user_rec:
            user_rec = {"name": uname, "statususer": None}

        request.state.user = user_rec
        return True

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user
        return AdminUser(username=user["name"], photo_url=None)

    async def logout(self, request: Request, response: Response) -> Response:
        sid = request.session.get("sessionid")
        if sid:
            with Session(engine["DB_admin"]) as session:
                stmt_delete = delete(UsersSessions).where(UsersSessions.session_id == sid)
                session.execute(stmt_delete)
                session.commit()

        request.session.clear()
        return response
