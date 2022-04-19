# IMPORTS ######################################################################
import json
import os
from urllib.error import HTTPError
import openai
from flask import Flask, redirect, render_template, request, url_for
################################################################################

# GLOBAL VARIABLES #############################################################
app = Flask(__name__)  # runs the web server
openai.api_key = os.getenv("OPENAI_API_KEY")  # store API in .env file

persona = ""  # Chatbot personality trait(s)
model = ""  # Fine-tuned GPT-3 model to query
temperature = None  # GPT-3 parameter set on chatbot home page
prev_human = "Hello."  # Previous human utterance, starting with Hello.
prev_bot = "Hi."  # Previous AI utterance, starting with Hi.
################################################################################

# CHATBOT API ##################################################################


@app.route("/", methods=["GET", "POST"])
def index():
    """GETs and POSTs information for the home page.

    Returns:
        Rendered template for the home page (index.html).
    """
    # If the user is POSTing information to the server, update global variables.
    if request.method == "POST":
        global persona
        persona = request.form["persona"]

        global model
        model = request.form["model"]

        global temperature
        temperature = float(request.form["temperature"])

        # Redirect the web page to the chatbot interface.
        # The persona_description will appear at the top of the web page with
        # the user's input filled in. Notice that the chat() API function will
        # use persona_description when the user makes a GET request, so we have
        # to provide the information here.
        return redirect(url_for(
            "chat",
            persona_description="GPT-3 Chatbot Persona: {}".format(persona)))

    # If the user is GETting the home page, render and return it.
    return render_template("index.html")


@app.route("/chat", methods=["GET"])
def chat():
    """GETs information for the chatbot interface page.

    This function handles actions related to the chatbot interface page. Notice
    that we do not need a method for POST because the user does not submit new
    data to the server. All of the chat bubbles are added dynamically through
    JavaScript onto a static page.

    Returns:
        Rendered template for chatbot interface page (chatbot.html).
    """
    # Remember: the persona_description is populated by the index() API method.
    persona_description = request.args.get("persona_description")
    return render_template("chatbot.html",
                           persona_description=persona_description)


@app.route("/get", methods=["GET"])
def get_bot_reply():
    """Queries GPT-3 API with human message and returns AI response.

    This is a helper method that works with a script embedded in chatbot.html
    to return the GPT-3 output. First, we retrieve the current human utterance
    from human_input. Then, we submit a query to the GPT-3 API. Finally, we
    update the previous human and AI utterances and return the GPT-3
    generation as the currernt AI response.

    Returns:
        GPT-3 generation (AI response string).
    """
    # Retrieve human_input populated by getResponse script in chatbot.html.
    human_input = request.args.get("human_input")
    prompt = generate_prompt(human_input)

    # Query OpenAI API for GPT-3 generation.
    global model
    global temperature
    try:
        if model == "text-davinci-002":
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=150,
                stop=["AI:", "Human:", "\n"],
            ).choices[0].text
        else:
            response = openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=150,
                stop=["AI:", "Human:", "\n"],
            ).choices[0].text
        is_successful = True
    except Exception as e:
        response = "ERROR: " + str(e)
        is_successful = False

    # Update global variables
    global prev_human
    prev_human = human_input
    global prev_bot
    prev_bot = response

    output = {
        "response": response,
        "success": is_successful,
    }

    return json.dumps(output)
################################################################################

# HELPER METHODS ###############################################################


def generate_prompt(human_input):
    """Generates the prompt for the GPT-3 generation.

    Args:
        human_input: the current utterance string from the user.

    Returns:
        GPT-3 prompt with the AI persona and past three turns.
    """
    global persona
    global prev_human
    global prev_bot
    return """The following is a conversation with an AI persona. The AI is {}.
    
    Human: {}
    AI: {}
    Human: {}
    AI:""".format(persona, prev_human, prev_bot, human_input)
################################################################################
