import re
from uuid import uuid4
from flask import make_response, render_template
import requests
from CTFd.cli import get_config
from CTFd.models import db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.utils.user import get_current_user
from CTFd.plugins.migrations import upgrade


class TicketRef(db.Model):
    __tablename__ = 'ticket_refs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("Users", foreign_keys="TicketRef.user_id", lazy="select")

    token = db.Column(db.String(400), nullable=False)


CHATWOOT_HOST = "https://chatwoot.burdi.ru"
CHATWOOT_WEBSITE_TOKEN = "ko4mkL7B5Fgkd6HRPLR34X8b"

# example
# curl 'https://burdi.ru/api/v1/widget/contact?website_token=ko4mkL7B5Fgkd6HRPLR34X8b' \
#   -H 'Accept: application/json, text/plain, */*' \
#   -H 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,ja;q=0.6,ar;q=0.5' \
#   -H 'Cache-Control: no-cache' \
#   -H 'Connection: keep-alive' \
#   -H 'Pragma: no-cache' \
#   -H 'Referer: https://burdi.ru/widget?website_token=ko4mkL7B5Fgkd6HRPLR34X8b' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: cors' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-Fetch-Storage-Access: active' \
#   -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36' \
#   -H 'X-Auth-Token: eyJhbGciOiJIUzI1NiJ9.eyJzb3VyY2VfaWQiOiIzOTM4Mzk0ZC1jZGRmLTQ1YWQtYWZkMi04YmU5NmRjN2E1YmIiLCJpbmJveF9pZCI6MX0.mGc4Qx4pcZxeidHQm0oOEDLynHqB60nYDMh8GTtLSyU' \
#   -H 'sec-ch-ua: "Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Windows"'


def load(app):
    app.db.create_all()

    def create_ticket():
        sess = requests.Session()
        r = sess.get(
            f"{CHATWOOT_HOST}/widget?website_token=ko4mkL7B5Fgkd6HRPLR34X8b",
        )

        token = re.search(r"authToken = '([^']+)'", r.text).group(1)
        return token

    @app.route('/chat', methods=['GET'])
    def view_chat():
        TEMPLATE = 'plugins/chatwoot/assets/chat.html'

        user = get_current_user()
        team = user.team if user is not None else None

        if user is None:
            return render_template(TEMPLATE, user=user)

        # find tickets belonging to a user which has the same team
        filter_query = TicketRef.user.has(team_id=team.id) if team is not None else TicketRef.user == user
        ticket_refs = TicketRef.query.filter(filter_query).all()

        ticket_ref = ticket_refs[0] if ticket_refs else None

        if ticket_ref is None:
            token = create_ticket()
            ticket_ref = TicketRef(
                user=user,
                token=token
            )
            db.session.add(ticket_ref)
            db.session.commit()

        response = make_response(render_template(TEMPLATE, user=user, chatwoot_host=CHATWOOT_HOST, chatwoot_website_token=CHATWOOT_WEBSITE_TOKEN))

        response.set_cookie('cw_conversation', ticket_ref.token)

        return response

    upgrade(plugin_name="chatwoot")
    register_plugin_assets_directory(
        app, base_path="/plugins/chatwoot/assets/"
    )