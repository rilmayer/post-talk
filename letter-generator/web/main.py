from flask import Flask, request, render_template
app = Flask(__name__)


@app.route("/")
def toppage():
    return render_template('index.html')


@app.route("/letter", methods=['GET'])
def letter():
    return render_template('letter.html',
                           postal_code=request.args.get('postal_code'),
                           message=request.args.get('message'),
                           receiver_name=request.args.get('receiver_name'),
                           receiver_address=request.args.get(
                               'receiver_address'),
                           sender_name=request.args.get('sender_name'),
                           sender_address=request.args.get('sender_address'))
