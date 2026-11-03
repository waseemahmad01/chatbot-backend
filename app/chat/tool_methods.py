

import json
import logging
import httpx
from openai.types.chat import ChatCompletionMessageFunctionToolCall

from app.core.config import settings
from app.events.eventBus import event_bus


logging = logging.getLogger(__name__)

async def get_weather(location:str, user_id:int, unit:str = "celsius",) -> dict:
    async with httpx.AsyncClient() as client:
        await event_bus.publish(user_id, "tool_call", {
            "type":"tool_call",
            "data":f"Getting weather for {location}"
        })
        data = await client.get(f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid=e8b396927f6d1389fd7a11620c92e470&units={unit}")
        data = data.json()
        logging.info(f"data ====>{data}")
        return {
            "location": location,
            "unit": unit,
             "temperature": data["main"]["temp"],
    "description": data["weather"][0]["description"],
    "humidity": data["main"]["humidity"],
    "wind_speed": data["wind"]["speed"]
        }


async def get_currency_rate(currency_pair:str, user_id:int) -> dict:
    async with httpx.AsyncClient() as client:
        await event_bus.publish(user_id, "tool_call", {
            "type":"tool_call",
            "data":f"Getting currency rate for {currency_pair}"
        })
        data = await client.get(f"https://v6.exchangerate-api.com/v6/{settings.currency_api_key}/pair/{currency_pair}")
        data = data.json()
        logging.info(f"data ====>{data}")
        print(f"Publishing event tool_call to {user_id}")
        return {
            "currency_pair": currency_pair,
            "rate": data["conversion_rate"]
        }


async def web_search(query:str, user_id:int) -> dict:
    async with httpx.AsyncClient() as client:
        await event_bus.publish(user_id, "tool_call", {
            "type":"tool_call",
            "data":f"Searching the web for {query}"
        })
        data = await client.post(f"https://api.tavily.com/search", json={
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": 5,
            "include_answer": True
        })
# sdf
        data = data.json()
        logging.info(f"data ====>{data}")
        results = [{
            "title": d["title"],
            "url": d["url"],
            "content": d["content"]
        } for d in data.get("results", [])]

        return {
            "query": query,
            "answer": data.get("answer", ""),
            "results": results
        }



TOOL_REGISTRY = {
    "get_weather": get_weather,
    "get_currency_rate": get_currency_rate,
    "web_search": web_search
}



async def execute_tool_call(tool_call:ChatCompletionMessageFunctionToolCall, user_id:int) -> list[dict]:
    fn = TOOL_REGISTRY.get(tool_call.function.name)
    if not fn:
        return {
            "success": False,
            "error": f"Tool {tool_call.function.name} not found"
        }
    args = json.loads(tool_call.function.arguments)  
    args["user_id"] = user_id
    result = await fn(**args)
    return {
        "success": True,
        "result": result
    }