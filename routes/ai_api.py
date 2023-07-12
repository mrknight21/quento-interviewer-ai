"""The Endpoints to interviewer ai"""
from flask import jsonify, abort, request, Blueprint
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import shortuuid
import openai
from dotenv import load_dotenv, find_dotenv

from firebase_db_util import FirebaseConnection
from ai.agents import generate_single_interview_response


_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']

AI_API = Blueprint('ai_api', __name__)
db_connection = FirebaseConnection(base_collection='interviews')


def get_blueprint():
    """Return the blueprint for the main app module"""
    return AI_API


@AI_API.route('/ask_quento', methods=['POST'])
def get_ai_reponse():
    """Create a request for quento ai to generate response
    @param session: post : the session id
    @return: 201: a response as a flask/response object \
    with application/json mimetype.
    @raise 400: misunderstood request
    """
    if not request.get_json():
        abort(400)
    payload = request.get_json(force=True)
    session_id = payload["session_id"]
    interview_db_obj = db_connection.find_one(session_id)
    interview_session = interview_db_obj._data

    # check if session exist.
    if not interview_session:
        return jsonify({"response": "session does not exist."}), 400
    interviewee = interview_session.get("interviewee", "annonymous user")
    conversation = interview_session["conversation"]

    # check if session has been completed.
    completion = interview_session.get("completion", True)
    if completion:
        return jsonify({"response": "session has been completed."}), 400

    # check if interview plan exist.
    plan_id = interview_session["planId"]
    plan_db_obj = db_connection.find_one(plan_id, "plans")
    plan = plan_db_obj._data
    if not plan:
        return jsonify({"response": "interview plan does not exist."}), 400
    agent_name = plan["agent name"]

    if len(conversation) > 0 and not conversation[-1]["isAI"]:
        return jsonify({"response": "waiting for user reply"}), 400

    # generate agent response
    agent_response, signal_completion = generate_single_interview_response(agent_name, plan, conversation)
    if agent_response:
        new_utterance = {
            "messageId": shortuuid.ShortUUID().random(length=8),
            "isAI": True,
            "message": agent_response,
            "speaker": agent_name,
            "time": datetime.now(tz=ZoneInfo('Australia/Sydney'))
        }
        interview_session["conversation"].append(new_utterance)
        interview_session["conversation"] = [c for c in interview_session["conversation"] if c != ""]
        db_connection.insert(interview_session, collection="interviews", doc_id=session_id, mode='set')

        # HTTP 201 Created
        return jsonify({"response": "response successfully generated and stored in db."}), 201
    else:
        return jsonify({"response": "something went wrong, the response generation was not completed"}), 400



