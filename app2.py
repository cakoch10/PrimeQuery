from flask import Flask, render_template
import requests
from flask_socketio import SocketIO, send, emit
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# Takes a list of keywords and
# returns the similarity
def similiarity(keywords1, keywords2):
    counter = 0
    for word in keywords1:
        if word in keywords2:
            counter += 2
    return 1.0*counter/(len(keywords1) + len(keywords2))


# This method handles a new message
def addQuestion(question):
    request_url = \
        "https://language.googleapis.com/" + \
        "v1/documents:analyzeEntities?key=" \
        + "AIzaSyCchGgYUMgG5BYF1mLBxHad-Z6J4jrrVlw"
    string_request = {}
    string_request["encodingType"] = "UTF8"
    string_request["document"] = {}
    string_request["document"]["type"] = "PLAIN_TEXT"
    string_request["document"]["content"] = question
    r = requests.post(request_url, json=string_request)
    response = json.loads(r.text)
    keywords = []
    for e in response["entities"]:
        keyword = e["name"]
        keywords.append(keyword)

    with open('questions.json') as f:
        quest = json.load(f)
    for questionToCompare in quest:
        s = similiarity(keywords, quest[questionToCompare])
        if s > 0.5:
            # we need to return a positive count
            return questionToCompare
    # at this point the question is new
    quest[question] = keywords
    with open('questions.json', 'w') as f:
        json.dump(quest, f)
    return question

def getMessages(keywords=[]):
    returnList = []
    for keyword in keywords:
        returnList.append("What does "+keyword+" mean?")
    returnList.append("Wait, I'm confused")
    return returnList


@app.route('/prof')
def prof():
    return render_template('prof.html')


@app.route('/student')
def student():
    return render_template('student.html')


@app.route('/')
def main():
    return render_template('index.html')


@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))


@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    send(message)
    submit_question(message)



@socketio.on('Upvote Feed Item')
def upvote(feedItem):
    print("upvoting: " + feedItem)
    with open('counts.json') as f:
        countDict = json.load(f)
        countDict[feedItem]["count"] += 1
    with open('counts.json', 'w') as f:
        json.dump(countDict, f)
    return


@socketio.on('Get Counter')
def getCount(feedItem):
    count = -1
    with open('counts.json') as f:
        countDict = json.load(f)
        count = countDict[feedItem]["count"]
    return count

@socketio.on('Get Json')
def getJson(feedItem):
    count = getCount(feedItem)
    returnDict = {feedItem, count}
    with open('solocount.json', 'w') as f:
        json.dump(returnDict, f)
    return



#@socketio.on('Submit Question')
def submit_question(question):
    c = addQuestion(question)
    if c == 1:
        with open('counts.json') as f:
            countDict = json.load(f)
            countDict[question]["count"] += 1
    else:

    print('Question Submitted: ' + str(question))


if __name__ == '__main__':
    socketio.run(app, debug=True)
