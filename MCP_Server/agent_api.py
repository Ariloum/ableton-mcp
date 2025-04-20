# agent_api.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import requests  # Import the requests library
import logging
import json

from server import get_ableton_connection  # импорт из твоего агента
from server import set_tempo  # установить темп трека

# Настройки API и логгера
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Настройки LM Studio API
LMSTUDIO_API_URL = "http://localhost:1234/v1"  # LM Studio URL

# Модель запроса
class PromptInput(BaseModel):
    prompt: str

@app.post("/prompt")
async def process_prompt(payload: PromptInput):
    prompt = payload.prompt
    logging.info(f"Получен промпт: {prompt}")

    try:
        # Отправляем промпт в локальный LLM (через LM Studio)
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "gemma-3-27b",  # название модели в LM Studio
            "messages": [
                {"role": "system", "content": "You are sound producer who makes music with Ableton Live program. You are connected to the Ableton API and there is limited functions which you can use to interact with the Ableton. All these functions accepts syntax is only with the JSON format - example:  {'type': 'set_tempo', 'params': {'tempo': 96.0}} - and return JSON too, so you need to produce JSON only and receive Ableton responses in JSON only too. There is two function types - setters and getters, there is setters example: add_notes_to_clip(track_index, clip_index, notes) where notes is a list of params: pitch, velocity, start_time, duration; set_clip_name(track_index, clip_index, name); set_tempo(tempo); fire_clip(track_index, clip_index); stop_clip(track_index, clip_index); load_instrument_or_effect(track_index, uri); load_browser_item(track_index, item_uri). And here is getter functions example: get_session_info() -> {tempo: 120.0, ...}; get_track_info(track_index) -> {name: Track Name, ...}; get_browser_tree(category_type=all) -> {type: all, categories: [...]}; get_browser_items(path=, item_type=all) -> [...]; get_browser_items_at_path(path=) -> [{name: ItemName, ...}]. Here is description of what each function does: get_session_info = returns tracks amount and other project information; get_track_info - returns additional information on waht is on track; create_midi_track - creates new midi track; set_track_name - set track name; create_clip - creates emoty clip on given track; add_notes_to_clip - adds midi notes on existent clip (if there is no clip on that track it will produce error <No clip in slot>), where notes is a list of params: pitch, velocity, start_time, duration; set_clip_name - changes selected clip name - it must exists before you call this function; set_tempo - changes project tempo; fire_clip - start playing of selected existent clip on given track; stop_clip - if some of clips is playing that will stop it; start_playback - just master project play button; stop_playback - master project stop button; load_browser_item - here you can access and load items in browser, it could be audio / midi effects / audio effects / plugins or group fx and so on; load_instrument_or_effect - here you can load instrument or effects for given track; There is no other functions, only these. I didn't provided all them as JSON to shorten the prompt. Do not add word json as prefix before json data. Do not add params json if function call has no params. DO NOT PRODUCE ANY RESPONSE BUT JSON, DO NOT TRY TO EXPLAIN ANYTHING! For JSON syntax use double quotes. I need VERY CONCISE answer contains json only and no other text - this is very important to follow this rulte."},
                {"role": "user", "content": prompt}
            ],
            "stream": False  # Disable streaming for compatibility with LM Studio
        }

        response = requests.post(LMSTUDIO_API_URL + "/chat/completions", headers=headers, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        
        reply = response.text # Get the raw text of the response
        logging.info(f"Raw LLM Response: {reply}") # Log the raw response
        
        data = json.loads(reply)
        response_json = data['choices'][0]['message']['content'].replace("```json\n", "").replace("\n```", "")
        logging.info(f"Распарсен json ответ: {response_json}")

        try:
            command = json.loads(response_json)
            logging.info(f"Parsed Command: {command}")  # Log the parsed command if successful
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e}") # Log the JSON decode error
            return {"error": f"Failed to parse LLM response as JSON: {e}"}

        # Пытаемся распарсить JSON-команду


        # Получаем соединение с Ableton
        ableton = get_ableton_connection()

        # Отправляем команду
        command_type = command.get("type")
        logging.info(f"Command type: {command_type}")

        params = command.get("params", {})
        logging.info(f"Command params: {params}")

        result = ableton.send_command(command_type, params)

        return {
            "command": command,
            "result": result
        }

    except Exception as e:
        logging.exception("Ошибка при обработке запроса:")
        return {"error": str(e)}
