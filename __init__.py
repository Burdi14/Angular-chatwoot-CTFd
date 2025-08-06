import re
from uuid import uuid4
from flask import make_response, render_template
import requests
from CTFd.models import db
from CTFd.utils.user import get_current_user
from CTFd.plugins.migrations import upgrade


class TicketRef(db.Model):
    __tablename__ = 'ticket_refs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("Users", foreign_keys="TicketRef.user_id", lazy="select")

    source_id = db.Column(db.String(40), nullable=False)
    session = db.Column(db.String(400), nullable=False)

CONTENT = """
<!-- <button class="btn btn-success" onclick="run_window()">Run</button> -->
<script>
    window.chatwootSettings = {"hideMessageBubble": true};
    (function(d,t) {
        var BASE_URL="https://burdi.ru";
        var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
        g.src=BASE_URL+"/packs/js/sdk.js";
        g.async = true;
        s.parentNode.insertBefore(g,s);
        g.onload=function(){
            window.chatwootSDK.run({
            websiteToken: 'ko4mkL7B5Fgkd6HRPLR34X8b',
            baseUrl: BASE_URL
            })
            window.$chatwoot.toggle('open');
        }
    })(document,"script");
    
    // function run_window() {
    //     window.$chatwoot.toggle('open');
    // }
</script>
"""

CHATWOOT_HOST = "https://burdi.ru"
# ACCOUNT_ID = 2
# TOKEN = "aN8zpwSx2foSQetxHUGrLDSz"
# INBOX_ID = 1

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

def create_ticket():
    sess = requests.Session()
    r = sess.get(
        f"{CHATWOOT_HOST}/widget?website_token=ko4mkL7B5Fgkd6HRPLR34X8b",
    )
    token = re.search(r"window\.authToken = '([^']+)'", r.text).group(1)
    return (token, r.cookies.get("_chatwoot_session"))


def load(app):
    app.db.create_all()

    @app.route('/chat', methods=['GET'])
    def view_chat():
        user = get_current_user()

        if user is None:
            return render_template('page.html', content="Please log in.")

        ticket_ref = TicketRef.query.filter_by(user_id=user.id).first() if user else None

        if ticket_ref is None:
            token, session = create_ticket()
            ticket_ref = TicketRef(
                user_id=user.id,
                source_id=token,
                session=session
            )
            db.session.add(ticket_ref)
            db.session.commit()

        response = make_response(render_template('page.html', content=CONTENT))

        response.set_cookie('cw_conversation', ticket_ref.source_id)
        response.set_cookie('_chatwoot_session', ticket_ref.session)

        return response

    upgrade(plugin_name="chatwoot")