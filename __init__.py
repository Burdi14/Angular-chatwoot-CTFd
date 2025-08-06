from flask import render_template

CONTENT = """
<script>
  (function(d,t) {
    var BASE_URL="https://burdi.ru/";
    var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
    g.src=BASE_URL+"/packs/js/sdk.js";
    g.async = true;
    s.parentNode.insertBefore(g,s);
    g.onload=function(){
      window.chatwootSDK.run({
        websiteToken: 'bcBpkacg6pnt7pG6RAGHcNDY',
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
