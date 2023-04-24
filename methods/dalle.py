import openai


def create_picture(msg, token):
    openai.api_key = token
    picture = openai.Image.create(
      prompt=msg,
      n=1,
      size="1024x1024"
    )
    picture = picture['data'][0]['url']
    return picture