tools = [
    {
        "type":"function",
        "function":{
            "name":"get_weather",
            "description": "Get current weather for a given city",
            "parameters":{
                "type": "object",
                "properties":{
                    "location": {
                        "type": "string",
                        "description":"The city name e.g Lahore, Islamabad, etc."
                    },
                     "unit": {
                    "type":"string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature e.g celsius, fahrenheit"
                },
                },
               
                "required": ["location"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_currency_rate",
            "description": "Get current currency rate for a given currency pair",
            "parameters":{
                "type": "object",
                "properties":{
                    "currency_pair": {
                        "type": "string",
                        "description": "The currency pair e.g EUR/USD, GBP/USD, etc."
                    }
                },
                "required": ["currency_pair"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"web_search",
           "description": "Search the web for CURRENT events, news, prices, or facts that change over time and that you would not reliably know from training (e.g. today's weather, recent news, current stock prices, live scores). Do NOT use this for general knowledge, explanations, definitions, math, coding help, or anything answerable from what you already know.",   
            "parameters":{
                "type": "object",
                "properties":{
                    "query": {
                        "type": "string",
                        "description": "The query to search the web for"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
