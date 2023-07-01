"""The Endpoints to interviewer ai"""
import uuid
from datetime import datetime, timedelta
from flask import jsonify, abort, request, Blueprint

AI_API = Blueprint('ai_api', __name__)


def get_blueprint():
    """Return the blueprint for the main app module"""
    return AI_API


@AI_API.route('/ask_quento', methods=['POST'])
def get_ai_repond():
    """Create a request for quento ai to generate respon
    @param session: post : the session id
    @return: 201: a response as a flask/response object \
    with application/json mimetype.
    @raise 400: misunderstood request
    """
    if not request.get_json():
        abort(400)
    data = request.get_json(force=True)

    # HTTP 201 Created
    return jsonify({"response": "hello world"}), 201



