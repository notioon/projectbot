import openai


def get_answer(messages, token):
    openai.api_key = token
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    return response