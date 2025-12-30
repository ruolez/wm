from datetime import datetime
import asyncio
import json
import os
import re
from smtplib import SMTP_PORT

from api1.api_v2.utils import SMTPEmailDeliveryService
from api1.config import SMTP_HOST, SMTP_PASSWORD, SMTP_SENDER_EMAIL, SMTP_USER
from api1.constants import VALID_ACTIVE_RANGE_MONTHS_VALUES
from api1.helpers import load_time_range_config, save_time_range_config
from api1.users.model import AdminUserProject_admin, Customers_tbl, Employees_tbl, Invoices_tbl, InvoicesDetails_tbl, Shippers_tbl, Terms_tbl, UsersSessions, AccountSyncSetting
from api1 import engine, engine_nick

from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, or_
from starlette.requests import Request


def get_invoice_info(request: Request):
    """
    Get full invoice details by InvoiceID or CustomerID, DB_name.
    Methods: GET
    """
    db_index = request.cookies.get("DB")
    invoice_id = request.query_params.get("invoice_id")
    customer_id = request.query_params.get("customer_id")

    if not db_index:
        return JSONResponse({"error": "Missing 'DB' cookie"}, status_code=400)

    try:
        with Session(engine[db_index]) as session:
            query = session.query(
                Invoices_tbl.InvoiceID,
                Invoices_tbl.InvoiceNumber,
                Invoices_tbl.InvoiceDate,
                Invoices_tbl.AccountNo,
                Invoices_tbl.BusinessName,
                Invoices_tbl.Notes,
                Invoices_tbl.SalesRepID,
            )

            if invoice_id:
                query = query.filter(Invoices_tbl.InvoiceID == invoice_id)
            if customer_id:
                query = query.filter(Invoices_tbl.CustomerID == customer_id)

            invoice = query.first()

            if not invoice:
                return JSONResponse({"error": "Invoice not found"}, status_code=404)

            sales_rep_name = "Not selected."
            if invoice.SalesRepID and invoice.SalesRepID != 0:
                employee = session.query(Employees_tbl.FirstName).filter(
                    Employees_tbl.EmployeeID == invoice.SalesRepID
                ).first()
                if employee:
                    sales_rep_name = employee.FirstName

            invoice_data = {
                "InvoiceNumber": invoice.InvoiceNumber,
                "InvoiceDate": invoice.InvoiceDate.isoformat() if invoice.InvoiceDate else None,
                "AccountNo": invoice.AccountNo,
                "BusinessName": invoice.BusinessName,
                "Notes": invoice.Notes,
                "FirstName": sales_rep_name
            }

        return JSONResponse(invoice_data)

    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)



def get_session_info(request: Request):
    """
    Retrieves session information from the database based on the session ID passed as a path parameter.
    Methods: GET
    """
    db_name = "DB_admin"
    session_id = request.session.get("sessionid", None)
    
    if not session_id:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)
    
    if db_name not in engine:
        return JSONResponse({"error": "Invalid database"}, status_code=400)
    try:
        with Session(engine[db_name]) as session:
            session_info = (
                session.query(UsersSessions)
                .filter(UsersSessions.session_id == session_id)
                .first()
            )
            
            if not session_info:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            
            return JSONResponse({
                "session_id": session_info.session_id,
                "user_id": session_info.user_id,
                "username": session_info.user_name
            })
    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)


def get_user_role(request: Request):
    """
    Retrieves user roles from the AdminUserProject_admin table in Admin DB.
    Methods: GET
    """
    db_name = "DB_admin"
    username = request.path_params.get("username")
    
    if not username:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)
    
    if db_name not in engine:
        return JSONResponse({"error": "Invalid database"}, status_code=400)
    
    try:
        with Session(engine[db_name]) as session:
            results = (
                session.query(AdminUserProject_admin.statususer)
                .filter(AdminUserProject_admin.username == username)
                .all()
            )
            roles = [row[0].split('/') for row in results]
        return JSONResponse({"roles": roles})
    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)


def get_shippers(request: Request):
    """
    Retrieves all unique shippers (id and name) from the shippers_tbl table.
    Methods: GET
    """
    db_name = request.path_params.get("db")
    
    if not db_name:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)
    
    if db_name not in engine:
        return JSONResponse({"error": "Invalid database"}, status_code=400)
    
    try:
        with Session(engine[db_name]) as session:
            results = session.query(Shippers_tbl.ShipperID, Shippers_tbl.Shipper).distinct().all()
            shippers = [{"id": row[0], "name": row[1]} for row in results]
        
        return JSONResponse({"shippers": shippers})
    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)


def update_invoice_data(request: Request):
    """
    Updates a single field in the Invoices table.
    
    Methods: GET
    """
    db_name = request.path_params.get("db")
    invoice_id = request.query_params.get("id")
    field = request.query_params.get("field")
    value = request.query_params.get("value")
    
    if not db_name or not invoice_id or not field or value is None:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)
    
    if db_name not in engine:
        return JSONResponse({"error": "Invalid database"}, status_code=400)
    
    try:
        with Session(engine[db_name]) as session:
            invoice = session.get(Invoices_tbl, invoice_id)
            if not invoice:
                return JSONResponse({"error": "Invoice not found"}, status_code=404)
            
            if not hasattr(invoice, field):
                return JSONResponse({"error": "Invalid field name"}, status_code=400)
            
            setattr(invoice, field, value)
            session.commit()
        
        return JSONResponse({"message": "Invoice updated successfully", "InvoiceID": invoice_id})
    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)


async def send_invoice_email(request: Request) -> JSONResponse:
    # avoid circular import
    from api1.pdf import create_invoice_pdf

    if request.method != "POST":
        return JSONResponse({"error": "Invalid method"}, status_code=405)

    form = await request.form()
    to_email = form.get("Email")
    body = form.get("body")
    if not to_email:
        return JSONResponse({"error": "Missing Email"}, status_code=400)
    if not body:
        return JSONResponse({"error": "Missing body"}, status_code=400)

    invoice_id     = form["InvoiceID"]
    invoice_number = form["InvoiceNumber"]
    db_name        = form["DBname"]

    # Load invoice data from DB & Generate PDF file.
    with Session(engine[engine_nick[db_name]]) as session:
        subq = select(Employees_tbl.FirstName).where(
            Invoices_tbl.SalesRepID == Employees_tbl.EmployeeID
        ).scalar_subquery()

        q = (
            select(
                Invoices_tbl.__table__.columns,
                subq.label("FirstName"),
                Terms_tbl.TermDescription,
                InvoicesDetails_tbl.__table__.columns,
            )
            .join(Terms_tbl, Invoices_tbl.TermID == Terms_tbl.TermID)
            .join(InvoicesDetails_tbl, Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID)
            .where(Invoices_tbl.InvoiceID == invoice_id)
        )
        rows      = session.execute(q).mappings().all()
        term_desc = session.execute(
            select(Terms_tbl.TermDescription).where(
                Terms_tbl.TermID == rows[0]["TermID"]
            )
        ).scalar()

    invoice_date = rows[0]["InvoiceDate"]
    if isinstance(invoice_date, datetime):
        invoice_date_str = invoice_date.strftime("%Y-%m-%d")
    else:
        invoice_date_str = str(invoice_date)

    sales_rep = rows[0]["FirstName"] or "Unknown"

    pdf_file = create_invoice_pdf(
        list_items       = rows,
        db_name          = db_name,
        invoice_number   = invoice_number,
        invoice_date     = invoice_date_str,
        business_name    = rows[0]["BusinessName"],
        sales_rep        = sales_rep,
        producer         = "Fcs",
        term_description = term_desc,
    )

    # Prepare and send email.
    email_service = SMTPEmailDeliveryService(
        smtp_host    = SMTP_HOST,
        smtp_port    = SMTP_PORT,
        smtp_user    = SMTP_USER,
        smtp_password= SMTP_PASSWORD,
        sender_email = SMTP_SENDER_EMAIL,
    )

    subject = f"Invoice #{invoice_number}"

    try:
        # offload blocking SMTP I/O to thread pool
        await asyncio.to_thread(
            email_service.deliver,
            to_email,
            subject,
            body,
            pdf_file,
        )
    except Exception as e:
        return JSONResponse(
            {"error": 1, "error_info": f"Email delivery failed: {e}"},
            status_code=500
        )

    try:
        os.remove(pdf_file)
    except OSError:
        pass

    return JSONResponse({"error": 0, "message": "Email sent successfully"})


def get_customer_email(request: Request) -> JSONResponse:
    """
    GET /api/get_customer_email/{db}/{account_no}/
    Extracts an email address from the Memo field of Customers_tbl.
    """
    db_name    = request.path_params.get("db")
    account_no = request.path_params.get("account_no")

    if not db_name or not account_no:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)
    if db_name not in engine:
        return JSONResponse({"error": "Invalid database"}, status_code=400)

    try:
        with Session(engine[db_name]) as session:
            memo = session.query(Customers_tbl.Memo) \
                          .filter(Customers_tbl.AccountNo == account_no) \
                          .scalar() or ""

        email = ""
        if isinstance(memo, str):
            m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', memo)
            if m:
                email = m.group(0)

        return JSONResponse({"email": email})

    except SQLAlchemyError as e:
        return JSONResponse(
            {"error": f"Database error: {str(e)}"},
            status_code=500
        )


def get_time_range(request: Request) -> JSONResponse:
    """
    GET /api/get_time_range/
    Returns the currently selected time range (in months).
    Methods: GET
    """
    try:
        cfg = load_time_range_config()
        return JSONResponse(cfg)
    except Exception as e:
        return JSONResponse(
            {"error": f"Config load error: {e}"}, status_code=500
        )


async def set_time_range(request: Request) -> JSONResponse:
    """
    POST /api/set_time_range/
    Expects JSON { "months": <number> } and updates the config accordingly.
    Methods: POST
    """
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    months = body.get("months")
    try:
        months = int(months)
    except (TypeError, ValueError):
        return JSONResponse({"error": "Missing or invalid 'months'"}, status_code=400)

    if months not in VALID_ACTIVE_RANGE_MONTHS_VALUES:
        return JSONResponse({"error": "Invalid months value"}, status_code=400)

    try:
        save_time_range_config({"months": months})
        return JSONResponse({"months": months})
    except Exception as e:
        return JSONResponse(
            {"error": f"Config save error: {e}"}, status_code=500
        )


async def get_user_accounts(request: Request) -> JSONResponse:
    """
    GET /api/get_user_accounts/
    Returns all sync settings for the current user across all databases.
    """
    username = request.headers.get("x-user-name")
    if not username:
        return JSONResponse({"error": "Missing X-User-Name header"}, status_code=400)

    try:
        with Session(engine["DB_admin"]) as sess:
            user = sess.query(AdminUserProject_admin).filter_by(username=username).first()
            if not user:
                return JSONResponse({"error": "User not found"}, status_code=404)

            settings = sess.query(AccountSyncSetting).filter_by(source_user_id=user.id).all()

        accounts = [
            {
                "db": s.db_name,
                "id": s.target_user_id,
                "username": s.target_username,
                "syncEnabled": s.sync_enabled,
            }
            for s in settings
        ]
        return JSONResponse({"accounts": accounts})

    except SQLAlchemyError as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def set_sync_accounts(request: Request) -> JSONResponse:
    """
    POST /api/set_sync_accounts/
    Body: { "accountIds": [EmployeeID, ...] }
    Updates which EmployeeIDs are enabled for sync for the current user across all databases.
    """
    try:
        body = await request.json()
    except ValueError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    account_ids = body.get("accountIds")
    if not isinstance(account_ids, list):
        return JSONResponse({"error": "Missing or invalid 'accountIds'"}, status_code=400)

    username = request.headers.get("x-user-name")
    if not username:
        return JSONResponse({"error": "Missing X-User-Name header"}, status_code=400)

    try:
        with Session(engine["DB_admin"]) as sess:
            user = sess.query(AdminUserProject_admin).filter_by(username=username).first()
            if not user:
                return JSONResponse({"error": "User not found"}, status_code=404)
            source_id = user.id
            selected = set(map(int, account_ids))

            # update existing settings
            settings = sess.query(AccountSyncSetting).filter_by(source_user_id=source_id).all()
            for s in settings:
                s.sync_enabled = s.target_user_id in selected

            sess.commit()

        return JSONResponse({"success": True})

    except SQLAlchemyError as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def admin_sync_all_accounts(request: Request) -> JSONResponse:
    """
    POST /api/admin/sync_all_accounts/
    Admin-only: rebuild all sync settings across every configured database.
    Skips:
      - any employee whose FirstName exactly equals the source username (case-insensitive)
      - duplicate (db, source_id, target_id) tuples
    """
    username = request.headers.get("x-user-name")
    if not username:
        return JSONResponse({"error": "Missing X-User-Name header"}, status_code=400)

    # verify admin
    with Session(engine["DB_admin"]) as admin_sess:
        admin = admin_sess.query(AdminUserProject_admin).filter_by(username=username).first()
        if not admin:
            return JSONResponse({"error": "User not found"}, status_code=404)
        roles = admin.statususer.split("/") if admin.statususer else []
        if "admin" not in roles:
            return JSONResponse({"error": "Forbidden"}, status_code=403)

        # clear existing settings
        admin_sess.execute(delete(AccountSyncSetting))
        admin_sess.commit()

        created = []
        sources = admin_sess.query(AdminUserProject_admin).all()

        # for each configured external DB
        for nick, eng_key in engine_nick.items():
            if eng_key == "DB_admin":
                continue
            db_engine = engine.get(eng_key)
            if not db_engine:
                continue

            seen = set()

            try:
                with Session(db_engine) as ext_sess:
                    for src in sources:
                        prefix = src.username or ""
                        # only exact match or prefix + space
                        pred = or_(
                            Employees_tbl.FirstName.ilike(prefix),
                            Employees_tbl.FirstName.ilike(f"{prefix} %")
                        )
                        matches = ext_sess.query(Employees_tbl).filter(pred).all()

                        for emp in matches:
                            # skip exact same username
                            if emp.FirstName.strip().lower() == src.username.strip().lower():
                                continue

                            key = (nick, src.id, emp.EmployeeID)
                            if key in seen:
                                continue
                            seen.add(key)

                            setting = AccountSyncSetting(
                                db_name=nick,
                                source_user_id=src.id,
                                target_user_id=emp.EmployeeID,
                                target_username=emp.FirstName,
                                sync_enabled=True
                            )
                            admin_sess.add(setting)
                            created.append({
                                "db": nick,
                                "source": src.id,
                                "target": emp.EmployeeID
                            })

                # commit per-database batch
                admin_sess.commit()

            except SQLAlchemyError:
                continue

    return JSONResponse({"synced_pairs": created})


async def admin_stop_all_syncs(request: Request) -> JSONResponse:
    """
    POST /api/admin/stop_all_sync/
    Admin-only: disable sync_enabled on all AccountSyncSetting records.
    """
    username = request.headers.get("x-user-name")
    if not username:
        return JSONResponse({"error": "Missing X-User-Name header"}, status_code=400)

    with Session(engine["DB_admin"]) as admin_sess:
        admin = admin_sess.query(AdminUserProject_admin).filter_by(username=username).first()
        if not admin:
            return JSONResponse({"error": "User not found"}, status_code=404)
        roles = admin.statususer.split("/") if admin.statususer else []
        if "admin" not in roles:
            return JSONResponse({"error": "Forbidden"}, status_code=403)

        result = admin_sess.execute(update(AccountSyncSetting).values(sync_enabled=False))
        admin_sess.commit()
        return JSONResponse({"stopped_count": result.rowcount})


async def get_user_access_menu(request: Request) -> JSONResponse:
    """
    GET /api/get_user_access_menu/{username}
    Returns the access menu for the specified user.
    """
    username = request.path_params.get("username")
    if not username:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)

    try:
        with Session(engine["DB_admin"]) as session:
            user = session.query(AdminUserProject_admin).filter_by(username=username).first()
            if not user:
                return JSONResponse({"error": "User not found"}, status_code=404)

            access_menu = list(user.accessmenu.split("/")) if user.accessmenu else []
            
            offset = [
                "CREATE NEW", "Create New", "ADMIN", "Invoice Details"
            ]

            # Filter out any items that are in the offset list
            access_menu = [item for item in access_menu if item not in offset]

        return JSONResponse({"access_menu": access_menu})

    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)


async def get_default_home_page(request: Request) -> JSONResponse:
    """
    GET /api/get_default_home_page/{username}
    Returns current value of default_home_page for selected user (or null).
    """
    username = request.path_params.get("username")
    if not username:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)

    try:
        with Session(engine["DB_admin"]) as session:
            user = session.query(AdminUserProject_admin).filter_by(username=username).first()
            if not user:
                return JSONResponse({"error": "User not found"}, status_code=404)

            return JSONResponse({"default_home_page": user.default_home_page})
    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)



async def set_default_home_page(request: Request) -> JSONResponse:
    """
    POST /api/set_default_home_page/{username}
    Body (JSON): { "default_home_page": "<string or null>" }
    Set (or clear to null) field default_home_page for selected user.
    """
    username = request.path_params.get("username")
    if not username:
        return JSONResponse({"error": "Invalid request data"}, status_code=400)

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    if "default_home_page" not in payload:
        return JSONResponse({"error": "Missing 'default_home_page'"}, status_code=400)

    new_home = payload.get("default_home_page")
    if new_home is not None and not isinstance(new_home, str):
        return JSONResponse(
            {"error": "Invalid 'default_home_page' value. Must be string or null."},
            status_code=400
        )

    try:
        with Session(engine["DB_admin"]) as session:
            user = session.query(AdminUserProject_admin).filter_by(username=username).first()
            if not user:
                return JSONResponse({"error": "User not found"}, status_code=404)

            if new_home is not None:
                raw_access = user.accessmenu or ""
                allowed_items = raw_access.split("/") if raw_access else []
                if new_home not in allowed_items:
                    return JSONResponse(
                        {"error": f"Menu item '{new_home}' is not in user's accessmenu"},
                        status_code=400
                    )

            user.default_home_page = new_home
            session.commit()

        return JSONResponse({
            "message": "default_home_page updated",
            "default_home_page": new_home
        })

    except SQLAlchemyError as e:
        return JSONResponse({"error": f"Database error: {str(e)}"}, status_code=500)