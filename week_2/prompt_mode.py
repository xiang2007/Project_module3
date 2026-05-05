import ollama
import sys
import os

from dotenv import load_dotenv
from ollama import generate
from google import genai
from google.genai import types

def load_env():
        load_dotenv()

try:
    client = genai.Client(api_key=os.getenv('api_key'))
except ValueError:
        print('No Api key was provided')
        sys.exit(1)

def ollama_response(model: str, prompt: str) -> str:
    try:
        match model:
            case 'deepseek':
                response = generate('deepseek-r1:1.5b', prompt)
            case 'phi3':
                response = generate('phi3', prompt)
            case 'llama':
                response = generate('llama3.1', prompt)
            case _:
                  raise ValueError(f'Unkown model: {model}')
        return response['response']
    except ollama._types.ResponseError:
        print('Invalid model name')
        return ""

def genai_response(model: str, prompt: str) -> str:
    try:
        match model:
            case 'gemini-2.5-flash':
                response = client.models.generate_content(model=model, contents=prompt)
            case 'gemini-2.5-flash-lite':
                response = client.models.generate_content(model=model, contents=prompt)
            case 'gemini-3-flash-preview':
                response = client.models.generate_content(model=model, contents=prompt)
            case _:
                raise ValueError (f'model not found: {model}')
        res = response.text or ""
        return (res)
    except Exception as e:
        print(f'{e}')
        return ""

def prompt_model(model: str, prompt: str) -> str :
    match model:
        case 'deepseek' | 'phi3' | 'llama':
            return ollama_response(model, prompt)
        case 'gemini-2.5-flash' | 'gemini-2.5-flash-lite' | 'gemini-3-flash-preview':
            return genai_response(model, prompt)
    return ""

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Invalid argv')
        sys.exit(1)
    load_env()
    res = prompt_model(sys.argv[1], sys.argv[2])
    print (res)
    sys.exit(0)