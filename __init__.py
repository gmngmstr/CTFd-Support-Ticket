import os
from datetime import datetime
from werkzeug import secure_filename

from flask import session, json, Blueprint, request, redirect, Response, url_for, send_file, abort, render_template, current_app
from flask.helpers import safe_join
from sqlalchemy.sql import and_

from CTFd.admin import admin
from CTFd.views import views
from CTFd.plugins import register_user_page_menu_bar, register_plugin_assets_directory
from CTFd.plugins.flags import get_flag_class
from CTFd.models import Challenges, db, Solves, Users
from CTFd.schemas.notifications import NotificationSchema
from CTFd.utils.modes import get_model
from CTFd.utils.user import get_ip, get_current_user, get_current_team, is_admin, authed
from CTFd.utils import scores
from CTFd.utils import config, get_config
from CTFd.utils.dates import ctf_ended, ctf_paused, view_after_ctf
from CTFd.utils.decorators import during_ctf_time_only, require_verified_emails, admins_only, require_team
from CTFd.utils.decorators.visibility import check_challenge_visibility
from CTFd.utils.helpers import get_errors, get_infos


support_ticket_templates = Blueprint("support_ticket_templates", __name__, template_folder='templates')
support_ticket_static = Blueprint("support_ticket_static", __name__, static_folder='static')


def load(app):
    # Create new locking_challenge table if necessary
    app.db.create_all()

    app.register_blueprint(support_ticket_templates)
    app.register_blueprint(support_ticket_static, url_prefix='/support-ticket')

    register_user_page_menu_bar('Support Ticket', 'support-ticket')
    # register_plugin_assets_directory(app, base_path="/plugins/CTFd_Support_Ticket/static/")

    if not os.path.exists(app.config['UPLOAD_FOLDER'] + '/support_ticket'):
        os.mkdir(app.config['UPLOAD_FOLDER'] + '/support_ticket')
    ticket_upload = (app.config['UPLOAD_FOLDER'] + '/support_ticket/')

    def get_challenges_by_categories():
        user = get_current_user()

        challenges = (Challenges.query.filter(and_(Challenges.state != "hidden", Challenges.state != "locked")).order_by(Challenges.value).all())

        if user:
            solve_ids = (Solves.query.with_entities(Solves.challenge_id).filter_by(account_id=user.account_id).order_by(Solves.challenge_id.asc()).all())
            solve_ids = set([value for value, in solve_ids])

            # TODO: Convert this into a re-useable decorator
            if is_admin():
                pass
            else:
                if config.is_teams_mode() and get_current_team() is None:
                    abort(403)
        else:
            solve_ids = set()

        response = []
        for challenge in challenges:
            if challenge.requirements:
                requirements = challenge.requirements.get("prerequisites", [])
                anonymize = challenge.requirements.get("anonymize")
                prereqs = set(requirements)
                if solve_ids >= prereqs:
                    pass
                else:
                    if anonymize:
                        response.append({"id": challenge.id, "name": "???", "category": "???"})
                    # Fallthrough to continue
                    continue

            response.append({"id": challenge.id, "name": challenge.name, "category": challenge.category})

        # Sort into categories
        categories = set(map(lambda x: x['category'], response))
        cats = []
        for c in categories:
            cats.append({
                'name': c,
                'challenges': [j for j in response if j['category'] == c]
            })
        db.session.close()
        return cats

    def get_ticket_for_user():
        user = get_current_user()
        tickets = (SupportTickets.query.filter(and_(SupportTickets.user_id == user.account_id)).order_by(SupportTickets.state))

        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'id': ticket.id,
                'challenge_cat': ticket.challenge_cat,
                'challenge_name': ticket.challenge_name,
                'state': ticket.state
            })
        return ticket_list

    def get_ticket_for_admin():
        tickets = SupportTickets.query.all()
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'id': ticket.id,
                'challenge_cat': ticket.challenge_cat,
                'challenge_name': ticket.challenge_name,
                'creator': ticket.user,
                'state': ticket.state
            })
        return ticket_list

    def get_user_access(user):
        users = Users.query.all()
        admin_users = []
        user_users = []
        for u in users:
            if u.type == "admin":
                admin_users.append(u.name)
            elif u.type == "user":
                user_users.append(u.name)
        if user in admin_users:
            user = user + " (Admin)"
            return user
        elif user in user_users:
            user = user + " (User)"
            return user

    def upload_file(ticket_id, message_id, user, files):
        if not os.path.exists(ticket_upload + str(ticket_id)):
            os.mkdir(ticket_upload + str(ticket_id))
        time = datetime.now().time().strftime("%H:%M")
        for file in files:
            filename_temp = filename = secure_filename(file.filename)
            '''if os.path.exists(ticket_upload + str(ticket_id) + '/' + filename_temp):
                data = {
                    "user_id": user.id,
                    "title": "Upload Failed",
                    "content": "The file that you just uploaded already exist please change the name and try again."
                }
                send_notification(data=data, type="alert")
                return'''
            exist = True
            place = 0
            while exist:
                if os.path.exists(ticket_upload + str(ticket_id) + '/' + filename_temp):
                    place += 1
                    temp = filename.split('.')
                    filename_temp = '{name}({place}).{ext}'.format(name=temp[0], place=place, ext=temp[1])
                else:
                    filename = filename_temp
                    exist = False
            file.save(ticket_upload + str(ticket_id) + '/' + filename)
            size = os.stat((ticket_upload + str(ticket_id) + '/' + filename)).st_size
            uploaded_file = SupportTicketFiles(ticket_id=ticket_id, message_id=message_id, sender=user.name, time_sent=time, path=(ticket_upload + str(ticket_id) + '/' + filename), filename=filename, size=size)
            db.session.add(uploaded_file)
            db.session.commit()

    def send_notification(data, type, sound=True):
        data["sound"] = sound
        data["type"] = type
        schema = NotificationSchema()
        result = schema.load(data)

        if result.errors:
            return {"success": False, "errors": result.errors}, 400

        db.session.add(result.data)
        db.session.commit()

        response = schema.dump(result.data)

        response.data["type"] = type
        response.data["sound"] = sound
        print(response.data)
        current_app.events_manager.publish(data=response.data, type="notification")
        print("Success")

    @app.route('/support-ticket', methods=['GET', 'POST'])
    @during_ctf_time_only
    @require_verified_emails
    @check_challenge_visibility
    @require_team
    def user_tickets():
        if is_admin():
            return render_template('support_ticket_page.html', ticket_list=get_ticket_for_admin(), access="Admin")
        else:
            return render_template('support_ticket_page.html', ticket_list=get_ticket_for_user(), access="User")

    @app.route('/support-ticket/new', methods=['GET', 'POST'])
    def new_ticket():
        if request.method == 'POST':
            user = get_current_user()
            category = request.form['category']
            challenge = request.form['challenge']
            issue = request.form['issue']
            files = request.files.getlist('file')
            ticket = SupportTickets(user=user.name, user_id=user.account_id, challenge_cat=category, challenge_name=challenge, description=issue)
            db.session.add(ticket)
            db.session.commit()
            time = datetime.now().time().strftime("%H:%M")
            initial_message = SupportTicketConversation(ticket_id=ticket.id, sender=user.name, time_sent=time, message=issue.replace('\n', '   '))
            db.session.add(initial_message)
            db.session.commit()
            if files[0]:
                files = request.files.getlist('file')
                upload_file(ticket.id, initial_message.id, user, files)
            return redirect('/support-ticket')
        ticket = SupportTickets.query.all()
        ids = []
        for t in ticket:
            ids.append(t.id)
        ticket_id = 1
        for i in range(1, len(ids)):
            if i not in ids:
                ticket_id = i
                break
        return render_template('support_ticket_new_page.html', challenge_categories=get_challenges_by_categories(), ticket_id=ticket_id)

    @app.route('/support-ticket/view/<int:ticket_id>', methods=['GET', 'POST'])
    def view_ticket(ticket_id):
        if request.method == 'POST':
            ticket = SupportTickets.query.filter_by(id=ticket_id)
            message = request.form['message']
            time = datetime.now().time().strftime("%H:%M")
            user = get_current_user()
            files = request.files.getlist('file')
            for t in ticket:
                if request.form['ticket-state'] != t.state:
                    data = {
                        "user_id": ticket[0].user_id,
                        "title": "Ticket Status Change",
                        "content": "The admins have changed your tickets status to {0}.".format(request.form['ticket-state']) if user.type == "admin" else "A ticket has been changed to {0} by the user.".format(request.form['ticket-state'])
                    }
                    send_notification(data=data, type="alert")
                    t.state = request.form['ticket-state']
                    db.session.commit()
            if message.replace(' ', '').replace('\n', '') != "" or files[0]:
                ticket_message = SupportTicketConversation(ticket_id=ticket_id, sender=user.name, time_sent=time, message=message.replace('\n', '   '))
                db.session.add(ticket_message)
                db.session.commit()
                if user.type == "admin":
                    data = {
                        "user_id": ticket[0].user_id,
                        "title": "New Ticket Message",
                        "content": "You have a new message from the admins in one of your tickets."
                    }
                    send_notification(data=data, type="alert")
            if files[0]:
                files = request.files.getlist('file')
                upload_file(ticket_id, ticket_message.id, user, files)
            return redirect(url_for("view_ticket", ticket_id=ticket_id))

        ticket = SupportTickets.query.filter_by(id=ticket_id).first_or_404()
        ticket_message = SupportTicketConversation.query.filter_by(ticket_id=ticket_id)
        ticket_info = {}
        ticket_conversation = []
        ticket_info.update({"category": ticket.challenge_cat, "challenge": ticket.challenge_name, "description": ticket.description, "state": ticket.state})
        for message_info in ticket_message:
            message_files = SupportTicketFiles.query.filter_by(message_id=message_info.id).all()
            file_list = []
            for file in message_files:
                file_list.append({file.id: file.filename})
            if message_info.message != '' or len(file_list) > 0:
                ticket_conversation.append({"id": message_info.id, "sender": get_user_access(message_info.sender), "time": message_info.time_sent, "message": message_info.message, "files": file_list})
        if is_admin():
            return render_template('support_ticket_view_page.html', ticket_info=ticket_info, ticket_conversation=ticket_conversation, ticket=ticket_id, access="Admin")
        else:
            return render_template('support_ticket_view_page.html', ticket_info=ticket_info, ticket_conversation=ticket_conversation, ticket=ticket_id, access="User")

    @app.route('/support-ticket/download-file/<int:file_id>/<string:filename>')
    def download_file(file_id, filename):
        file = SupportTicketFiles.query.filter(and_(SupportTicketFiles.id == file_id)).first_or_404()
        return send_file(file.path, attachment_filename=file.filename)

    @app.route('/support-ticket/delete-file/<int:file_id>')
    def delete_file(file_id):
        file = SupportTicketFiles.query.filter_by(id=file_id)
        ticket_id = file[0].ticket_id
        if os.path.exists(file[0].path):
            os.remove(file[0].path)
        file.delete()
        db.session.commit()
        return redirect(url_for("ticket_management", ticket_id=ticket_id))

    @app.route('/admin/plugins/support-ticket', methods=['GET'])
    @admins_only
    def admin_ticket_management():
        return render_template('support_ticket_admin_view.html', ticket_list=get_ticket_for_admin())

    @app.route('/admin/plugins/support-ticket/view/<int:ticket_id>')
    @admins_only
    def ticket_management(ticket_id):
        ticket = SupportTickets.query.filter_by(id=ticket_id).first_or_404()
        ticket_info = {}
        ticket_info.update({"id": ticket_id, "creator": ticket.user, "category": ticket.challenge_cat, "challenge": ticket.challenge_name, "description": ticket.description, "state": ticket.state})
        file_info = SupportTicketFiles.query.filter_by(ticket_id=ticket_id)
        file_list = []
        for file in file_info:
            if int(file.size) >= 1000000:
                size = str(int(file.size) / 1000000) + 'MB'
            elif int(file.size) >= 1000:
                size = str(int(file.size) / 1000) + 'KB'
            else:
                size = str(file.size) + 'B'
            file_list.append({"id": file.id, "filename": file.filename, "size": size})
        print(file_list)
        return render_template('support_ticket_admin_edit.html', ticket_info=ticket_info, file_list=file_list)

    @app.route('/admin/plugins/support-ticket/delete/<int:ticket_id>', methods=['GET'])
    @admins_only
    def delete_ticket(ticket_id):
        files = SupportTicketFiles.query.filter_by(ticket_id=ticket_id).all()
        for file in files:
            delete_file(file.id)
        SupportTicketConversation.query.filter_by(ticket_id=ticket_id).delete()
        db.session.commit()
        SupportTickets.query.filter_by(id=ticket_id).delete()
        db.session.commit()
        return redirect(url_for("admin_ticket_management"))


class SupportTickets(db.Model):
    __tablename__ = "support_tickets"
    __mapper_args__ = {"polymorphic_identity": "support_tickets"}
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80))
    user_id = db.Column(db.Integer)
    challenge_cat = db.Column(db.String(80))
    challenge_name = db.Column(db.String(80))
    description = db.Column(db.Text)
    state = db.Column(db.String(80), nullable=False, default="Submitted")

    def __init__(self, user, user_id, challenge_cat, challenge_name, description):
        self.user = user
        self.user_id = user_id
        self.challenge_cat = challenge_cat
        self.challenge_name = challenge_name
        self.description = description


class SupportTicketConversation(db.Model):
    __mapper_args__ = {"polymorphic_identity": "support_ticket_conversation"}
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'))
    sender = db.Column(db.String(80), nullable=False)
    time_sent = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text)

    def __init__(self, ticket_id, sender, time_sent, message):
        self.ticket_id = ticket_id
        self.sender = sender
        self.time_sent = time_sent
        self.message = message


class SupportTicketFiles(db.Model):
    __mapper_args__ = {"polymorphic_identity": "support_ticket_files"}
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'))
    message_id = db.Column(db.Integer, db.ForeignKey('support_ticket_conversation.id'))
    sender = db.Column(db.String(80), nullable=False)
    time_sent = db.Column(db.String(80), nullable=False)
    path = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(80), nullable=False)
    size = db.Column(db.String(80))

    def __init__(self, ticket_id, message_id, sender, time_sent, path, filename, size):
        self.ticket_id = ticket_id
        self.message_id = message_id
        self.sender = sender
        self.time_sent = time_sent
        self.path = path
        self.filename = filename
        self.size = size
