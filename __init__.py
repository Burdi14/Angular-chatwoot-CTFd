import re
from uuid import uuid4
from flask import make_response, redirect, render_template, request, url_for
import requests
from CTFd.cli import get_config
from CTFd.models import db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.utils.user import get_current_user
from CTFd.plugins.migrations import upgrade
from CTFd.plugins import override_template, register_user_page_menu_bar
from CTFd.plugins.chatwoot.template_challenge import CHALLENGE_CONTENT

class TicketRef(db.Model):
    __tablename__ = 'ticket_refs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("Users", foreign_keys="TicketRef.user_id", lazy="select")

    token = db.Column(db.String(400), nullable=False)


CHATWOOT_HOST = "https://chatwoot.burdi.ru"
CHATWOOT_WEBSITE_TOKEN = "ko4mkL7B5Fgkd6HRPLR34X8b"

def load(app):
    app.db.create_all()

    def create_ticket():
        sess = requests.Session()
        r = sess.get(
            f"{CHATWOOT_HOST}/widget?website_token=ko4mkL7B5Fgkd6HRPLR34X8b",
        )

        token = re.search(r"authToken = '([^']+)'", r.text).group(1)
        return token

    @app.route('/view_ticket/<int:ticket_id>', methods=['GET'])
    def view_chat(ticket_id):
        TEMPLATE = 'plugins/chatwoot/assets/chat.html'

        user = get_current_user()
        team = user.team if user is not None else None

        if user is None:
            return render_template(TEMPLATE, user=user)

        filter_query = TicketRef.user.has(team_id=team.id) if team is not None else TicketRef.user == user
        ticket_refs = TicketRef.query.filter(filter_query).all()

        if not ticket_refs: 
            return "Not found", 404
        
        ticket_ref = next(x for x in ticket_refs if x.id == ticket_id)

        response = make_response(render_template(TEMPLATE, ticket_ref=ticket_ref, user=user, tickets=ticket_refs, chatwoot_host=CHATWOOT_HOST, chatwoot_website_token=CHATWOOT_WEBSITE_TOKEN))

        response.set_cookie('cw_conversation', ticket_ref.token)

        return response

    @app.route('/tickets', methods=['GET'])
    def view_tickets():
        TEMPLATE = 'plugins/chatwoot/assets/tickets.html'

        user = get_current_user()
        if user is None:
            return render_template(TEMPLATE, user=user)
        
        team = user.team if user is not None else None

        filter_query = TicketRef.user.has(team_id=team.id) if team is not None else TicketRef.user == user
        ticket_refs = TicketRef.query.filter(filter_query).all()

        return render_template(TEMPLATE, user=user, tickets=ticket_refs)

    @app.route('/create_ticket', methods=['GET'])
    def create_ticket_route():
        user = get_current_user()
        if user is None:
            return redirect(url_for("auth.login", next=request.full_path))

        token = create_ticket()
        ticket_ref = TicketRef(
            user=user,
            token=token
        )
        db.session.add(ticket_ref)
        db.session.commit()

        return redirect(url_for('view_chat', ticket_id=ticket_ref.id))


    upgrade(plugin_name="chatwoot")
    register_plugin_assets_directory(
        app, base_path="/plugins/chatwoot/assets/"
    )
    override_template('challenge.html', CHALLENGE_CONTENT)

    register_user_page_menu_bar("Tickets", "/tickets")
