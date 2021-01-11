from flask import Flask
app = Flask(__name__)
from flask import request

@app.route('/', methods=['POST'])
def print_request():
    print(request.json)

    return "ok"
