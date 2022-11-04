# -*- coding:UTF-8 -*-
from flask import Flask
import crack

app = Flask(__name__)
#app.register_blueprint(v1_api, url_prefix="/api/v1")

@app.route("/", methods=["GET"])
def hello_flask():
    crack.crack()
    return "hello flask"

if __name__ == "__main__":
    app.run(debug=True)
