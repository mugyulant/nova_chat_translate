import ollama

def ollama_chat(model: str, messages: list):
    response = ollama.chat(model=model, messages=messages)
    return response.message.content