import openai
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo

# Connect to the database
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['screeningDb']
app = Flask(__name__)
CORS(app)

@app.route('/get-cost-hits', methods=['get'])
def getCostNoOfHits():
    costStats = db['costStats']
    cursor = costStats.find()
    for doc in cursor:
        return json.dumps({"numberOfHits": doc["numberOfHits"],"totalCost": doc["totalCost"]})
    return ""

@app.route('/validate-hit', methods=['POST'])
def validatingArticle():
    requestData = request.get_json()
    name = requestData.get('name')
    content=requestData.get('article')
    description=requestData.get('description')
    return validatingTrueFalseHit(f"name: {name} || description: {description} || News article: `{content}`")

@app.route('/assess-materiality', methods=['POST'])
def matiealAssessment():
    requestData = request.get_json()
    name=requestData.get('name')
    article = requestData.get('article')
    return assessMateriality(f"Entity name: {name}, News article: {article}")

def assessMateriality(content):
    openai.api_key="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"
    prompt="inside the triple backticks we have an entity name and an article which mentions that entity. " \
           "give a short summary of about 2-3 lines about what the article talks about in relation to our entity include the numerical figures in the summary and timelines of financial crimes related to our entity. " \
           "also include the timeline of investigation if mentioned. " \
           "then act as a bank and do the materiality assessment of the news article against the given entity, also consider the following points: " \
           "- concept of time lapse to analyze if the news article still has an impact or is outdated based on the date you are processing this prompt. " \
           "- if the given allegations against the entity are proven or not. " \
           "- if the given entity is sanctioned by any other entity " \
           "then classify the news article only in relation to the given entity as one of the following: " \
           "'No financial crime negative news'- if article has material news but does not mention any Financial Crime(crime that involves money or other financial resources) commited by the entity, " \
           "'Material financial crime negative news'- if article is material and some Financial crimes might have been commited by the entity, " \
           "'Non material news'- if article does not have any material news. " \
           "then extract the important facts from given article about the given entity name in very very short as list, which can help the bank make informed decisions regarding accepting or continuing a business relationship with the given entity. " \
           "return the response in following format " \
           "first label as 'summary' , " \
           "second label as 'suggested classification', " \
           "third label as 'Facts' and value as list of facts, "
    completion=openai.ChatCompletion.create(
        model="gpt-3.5-turbo",messages=[
            {
                "role": "system",
                "content": "help a bank determine material impact of the given entity's activity on the bank's risk exposure, regulatory compliance, reputation, and overall business operations"
            },
            {
            "role":"user",
            "content":f"{prompt} ```{content}```"
            }
        ],temperature=0.5
    )
    # Checking for errors
    if 'error' in completion:
        error_message = completion['error']['message']
        raise Exception(f"ChatGPT API call failed: {error_message}")
    #,max_tokens=1
    # Use a breakpoint in the code line below to debug your script.
    # print("Data: " + completion.choices[0].message.content)
    totalOutputToken = int(completion.usage.total_tokens)-420
    toatalPrice = 0.05+float(totalOutputToken*0.002*83/1000)
    costStats = db['costStats']
    cursor = costStats.find()
    numberOfHits=0
    totalCost=0.0
    _id=None
    for doc in cursor:
        numberOfHits=doc["numberOfHits"]
        totalCost=doc["totalCost"]
        _id=doc["_id"]
    result = costStats.update_one({'_id': _id}, {'$set': {'numberOfHits': numberOfHits+1,'totalCost': totalCost+toatalPrice}})
    responsedata={"tokenPrice": str(toatalPrice),"content": completion.choices[0].message.content}
    return json.dumps(responsedata)
def validatingTrueFalseHit(content):
    openai.api_key="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"
    prompt="under triple backticks you will be given an entity or person name, some description about that entity or person and a news article seperated by ||. act as a news screener and follow the below steps" \
           "step1: decide if the article has any mention about the person or entity." \
           "step2: decide if the given description is correct according to the article" \
           "after completing step1 and step2 return the answer in the JSON format." \
           "use first label as 'result' and value as " \
           "'true': if and only if both step1 and step2 are true" \
           "'false': if either of step1 or step2 are false" \
           "use second label as 'explanation' and value as single sentence reason for the answer"
    completion=openai.ChatCompletion.create(
        model="gpt-3.5-turbo",messages=[
            {
            "role":"user",
            "content":f"{prompt} ```{content}```"
            }
        ],temperature=0.5
    )
    # Checking for errors
    if 'error' in completion:
        error_message = completion['error']['message']
        raise Exception(f"ChatGPT API call failed: {error_message}")

    #,max_tokens=1
    # Use a breakpoint in the code line below to debug your script.
    # totalOutputToken = int(completion.usage.total_tokens)-420
    # toatalPrice = 0.05+float(totalOutputToken*0.002*83/1000)
    # result = {"tokenPrice": str(toatalPrice),"content":json.loads(completion.choices[0].message.content)}
    return jsonify(json.loads(completion.choices[0].message.content))

if __name__ == '__main__':
    app.run(debug=True)















#
#
# # Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     callgpt()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
