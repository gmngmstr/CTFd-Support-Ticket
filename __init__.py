from datetime import datetime

from flask import Blueprint, request, redirect, abort, render_template
from sqlalchemy.sql import and_

from CTFd.models import Challenges, db, Solves, Users
from CTFd.plugins import register_user_page_menu_bar
from CTFd.utils import config
from CTFd.utils.user import get_current_user, get_current_team, is_admin

support_ticket = Blueprint("support_ticket", __name__, template_folder='templates')
support_ticket_static = Blueprint("support_ticket_static", __name__, static_folder='static')


def load(app):
    # Create new locking_challenge table if necessary
    app.db.create_all()

    app.register_blueprint(support_ticket)
    app.register_blueprint(support_ticket_static, url_prefix='/support_ticket')

    register_user_page_menu_bar('Support Ticket', 'support_ticket')

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

    @app.route('/support_ticket', methods=['GET', 'POST'])
    def user_tickets():
        if is_admin():
            return render_template('support_ticket_page.html', ticket_list=get_ticket_for_admin(), access="Admin")
        else:
            return render_template('support_ticket_page.html', ticket_list=get_ticket_for_user(), access="User")

    @app.route('/support_ticket/new', methods=['GET', 'POST'])
    def new_ticket():
        if request.method == 'POST':
            user = get_current_user()
            category = request.form['category']
            challenge = request.form['challenge']
            issue = request.form['issue']
            ticket = SupportTickets(user=user.name, user_id=user.account_id, challenge_cat=category, challenge_name=challenge, description=issue)
            db.session.add(ticket)
            db.session.commit()
            time = datetime.now().time().strftime("%H:%M")
            initial_message = SupportTicketConversation(ticket_id=ticket.id, sender=user.name, time_sent=time, message=issue)
            db.session.add(initial_message)
            db.session.commit()
            return redirect('/support_ticket')
        return render_template('support_ticket_new_page.html', challenge_categories=get_challenges_by_categories())

    @app.route('/support_ticket/view', methods=['GET', 'POST'])
    def view_ticket():
        if request.method == 'POST':
            ticket_id = request.form['ticket']
            message = request.form['message']
            time = datetime.now().time().strftime("%H:%M")
            user = get_current_user()
            if message.replace(' ', '').replace('\n', '') != "":
                ticket_message = SupportTicketConversation(ticket_id=ticket_id, sender=user.name, time_sent=time, message=message)
                db.session.add(ticket_message)
                db.session.commit()
            if is_admin():
                ticket = (SupportTickets.query.filter(SupportTickets.id == ticket_id))
                for t in ticket:
                    if request.form['ticket-state'] != t.state:
                        t.state = request.form['ticket-state']
                        db.session.commit()
            return redirect('view?ticket={0}'.format(ticket_id))
        ticket_id = request.args.get('ticket')
        ticket = (SupportTickets.query.filter(SupportTickets.id == ticket_id))
        ticket_message = (SupportTicketConversation.query.filter(SupportTicketConversation.ticket_id == ticket_id))
        ticket_info = {}
        ticket_conversation = []
        for t in ticket:
            ticket_info.update({"category": t.challenge_cat, "challenge": t.challenge_name, "description": t.description, "state": t.state})
        for message_info in ticket_message:
            ticket_conversation.append({"id": message_info.id, "sender": get_user_access(message_info.sender), "time": message_info.time_sent, "message": message_info.message})
        if is_admin():
            return render_template('support_ticket_view_page.html', ticket_info=ticket_info, ticket_conversation=ticket_conversation, ticket=ticket_id, access="Admin")
        else:
            return render_template('support_ticket_view_page.html', ticket_info=ticket_info, ticket_conversation=ticket_conversation, ticket=ticket_id, access="User")


class SupportTickets(db.Model):
    __mapper_args__ = {"polymorphic_identity": "support_tickets"}
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80))
    user_id = db.Column(db.Integer)
    challenge_cat = db.Column(db.String(80))
    challenge_name = db.Column(db.String(80))
    description = db.Column(db.Text)
    state = db.Column(db.String(80), nullable=False, default="Pending")

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
    message = db.Column(db.String)

    def __init__(self, ticket_id, sender, time_sent, message):
        self.ticket_id = ticket_id
        self.sender = sender
        self.time_sent = time_sent
        self.message = message
