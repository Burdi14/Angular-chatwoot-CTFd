from flask import render_template

CONTENT = """
<script>
  window.chatwootSettings = {"position":"right","type":"standard","launcherTitle":"Chat with us"};
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
    }
  })(document,"script");
</script>
"""

def load(app):
    @app.route('/chat', methods=['GET'])
    def view_chat():
        return render_template('page.html', content=CONTENT)
