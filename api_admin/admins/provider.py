import datetime
import uuid
from starlette_admin.helpers import verify_password, hash_password
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from admins.model import AdminUserProject_admin, UsersSessions

from database import select, insert, delete, update, engine, and_
from sqlalchemy.orm import Session

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
        username = username.strip().lower()
        if len(username) < 1:
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )

        if username not in user_dict:
            raise LoginFailed("Invalid username or password")

        stored_hash = user_dict[username]["password"]

        if stored_hash.startswith("$2"):
            is_valid = verify_password(password, stored_hash)
            effective_hash = stored_hash
        else:
            new_hash = hash_password(password)
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
            effective_hash = new_hash

        if not is_valid or "admin" not in user_dict[username]["statususer"].split("/"):
            raise LoginFailed("Invalid username or password")

        with Session(engine["DB_admin"]) as session:
            numsid = guid()
            stmt_check = select(UsersSessions.session_id).where(UsersSessions.session_id == numsid)
            while session.execute(stmt_check).first():
                numsid = guid()
                stmt_check = select(UsersSessions.session_id).where(UsersSessions.session_id == numsid)

            request.session.update({"username": username})
            request.session.update({"sessionid": numsid})

            stmt_insert = (
                insert(UsersSessions)
                .values(
                    session_id=numsid,
                    user_name=username,
                    created_at=now_minus_5h(),
                    expires_at=now_minus_5h_plus_130m(),
                    browser_info=request.headers.get("user-agent"),
                    Flag1=1,
                )
            )
            session.execute(stmt_insert)
            session.commit()

        return response

    async def is_authenticated(self, request: Request) -> bool:
        uname = request.session.get("username")
        sid = request.session.get("sessionid")
        if (
            uname in users
            and "admin" in user_dict[uname]["statususer"].split("/")
            and sid
        ):
            with Session(engine["DB_admin"]) as session:
                stmt_check = select(UsersSessions.session_id).where(
                    and_(
                        UsersSessions.session_id == sid,
                        UsersSessions.Flag1 == 1,
                    )
                )
                if not session.execute(stmt_check).first():
                    return False

                stmt_update = (
                    update(UsersSessions)
                    .values(
                        updated_at=now_minus_5h(),
                        expires_at=now_minus_5h_plus_130m(),
                    )
                    .where(UsersSessions.session_id == sid)
                )
                session.execute(stmt_update)
                session.commit()

            request.state.user = users.get(uname)
            return True
        return False

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
