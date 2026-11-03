import asyncio
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging

from app.chat import tools
from app.chat.enums import MessageRole
from app.chat.tool_methods import execute_tool_call
from app.db.models import Conversation, Message

from app.chat.llm import get_client
from openai import NotFoundError, APIConnectionError, RateLimitError

from app.events.eventBus import event_bus


logging = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 16 

SYSTEM_PROMPT = (
    "You are a helpful assistant. You have access to tools, but you should only use them "
    "when the question genuinely requires current, real-time, or external information "
    "you wouldn't already know. For general knowledge, explanations, math, or coding questions, "
    "answer directly without calling any tool. "
    "When you do call a tool, use only the structured tool-calling mechanism, never plain text. "
    "After a tool call returns a reasonable answer, stop and respond directly — "
    "do not make additional unnecessary tool calls."
)

MAX_TOOL_ITERATIONS = 4

async def chat_with_tools(user_message: str) -> str:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    client = get_client("llama-3.1-8b-instant")
    iteration = 0
    while True:
        if iteration >= MAX_TOOL_ITERATIONS:
            print("Reached the maximum number of tool iterations, answering the question directly")
            # if we have reached the maximum number of tool iterations, we need to answer the question directly no need to use tools anymore since we already have the information in messages
            messages.append({
                "role": "user",
                "content":"You have enough information to answer the question. Please answer the questions in details with all the information you have gathered."
            })
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
            )
            return response.choices[0].message.content

        iteration += 1
        response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                tools=tools.tools,
                tool_choice="auto",
            )

        asssistent_message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        print("response ====>",response.model_dump_json(indent=2))

        
        if finish_reason == "tool_calls" and asssistent_message.tool_calls:
            messages.append(asssistent_message.model_dump(exclude_unset=True))
            for tc in asssistent_message.tool_calls:
                print("tool_call ====>",tc.function.name)
            tasks = [execute_tool_call(tool_call) for tool_call in asssistent_message.tool_calls]
            results = await asyncio.gather(*tasks)
            # for tool_call in asssistent_message.tool_calls:
            #     tool_result = await execute_tool_call(tool_call)
            #     print(tool_result)
            #     if tool_result["success"]:
            #         messages.append({
            #             "role": "tool",
            #             "content":(json.dumps(tool_result["result"] if tool_result["success"] else tool_result["error"])),
            #             "name": tool_call.function.name,
            #             "tool_call_id": tool_call.id
            #         })
            #     else:

            #         messages.append({
            #             "role": "tool",
            #             "content": tool_result["error"],
            #             "name": tool_call.function.name,
            #             "tool_call_id": tool_call.id
            #         })
            #         continue
            # continue
            for tool_call, result in zip(asssistent_message.tool_calls, results):
                content = result["result"] if result["success"] else result["error"]
                print(f"tool_result for {tool_call.function.name} ====> {content}")
                messages.append({
                    "role": "tool",
                    "content": json.dumps(content),
                    "name": tool_call.function.name,
                    "tool_call_id": tool_call.id
                })
            continue;   # continue to the next iteration of the loop
        print("No more tool calls, answering the question directly")
        return asssistent_message.content
 
def get_owned_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    return db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()

def message_to_llm_format(m: Message) -> dict:
    role = m.role.value if hasattr(m.role, "value") else m.role

    if role == "assistant" and m.tool_calls:
        return {"role": "assistant", "content": m.content, "tool_calls": m.tool_calls}

    if role == "tool":
        return {
            "role": "tool",
            "content": m.content,
            "tool_call_id": m.tool_call_id,
            "name": m.tool_name,
        }

    return {"role": role, "content": m.content}


async def stream_reply(db: Session, conversation: Conversation, user_message: str, user_id:int, temperature: float = 0.2,):
    db.add(Message(conversation_id = conversation.id, role = MessageRole.USER,content = user_message))  
    db.commit()

    history = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.id.desc()).limit(MAX_HISTORY_MESSAGES).all()

    history.reverse()

    messages = [{
        "role": MessageRole.SYSTEM,
        "content": SYSTEM_PROMPT}, *[message_to_llm_format(m) for m in history]
    ] 

    await event_bus.publish(user_id,"progress", {
        "type":"progress",
        "data":"Thinking..."
    })
    
    client = get_client(conversation.model)

    iterations = 0

    while True:
        
        if iterations >= MAX_TOOL_ITERATIONS:
            messages.append({
                "role": MessageRole.USER,
                "content": "You have enough information to answer the question. Please answer the questions in details with all the information you have gathered."
            })
       
        try:

            response = client.chat.completions.create(model=conversation.model, messages=messages, tools=tools.tools if iterations <= MAX_TOOL_ITERATIONS else None,
                tool_choice="auto" if iterations <= MAX_TOOL_ITERATIONS else None)

        except NotFoundError:
            raise HTTPException(status_code=404, detail="Model not found")
        except APIConnectionError:
            raise HTTPException(status_code=500, detail="API connection error")
        except RateLimitError:
            raise HTTPException(status_code=503, detail="Rate limit exceeded")

        assisstant_message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls" and assisstant_message.tool_calls:
            messages.append(assisstant_message.model_dump(exclude_unset=True))
            # persist the message to database
            db.add(Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content="",
                model=conversation.model,
                tool_calls=[tc.model_dump() for tc in assisstant_message.tool_calls]
            ))
            db.commit()
            
            tasks = [execute_tool_call(tool_call, user_id) for tool_call in assisstant_message.tool_calls]

            results = await asyncio.gather(*tasks)

            for tool_call, result in zip(assisstant_message.tool_calls, results):
                content = result["result"] if result["success"] else result["error"]
                messages.append({
                    "role": MessageRole.TOOL,
                    "content": json.dumps(content),
                    "name": tool_call.function.name,
                    "tool_call_id": tool_call.id
                })

                db.add(
                    Message(
                        conversation_id=conversation.id,
                        role=MessageRole.TOOL,
                        content=json.dumps(content),
                        model=conversation.model,
                        tool_name=tool_call.function.name,
                        tool_call_id=tool_call.id,
                        message_type="tool_result"
                    )
                )
            db.commit()
            continue
            # No more tool calls — break out to final streaming step
        break

    stream = client.chat.completions.create(model=conversation.model, messages=messages, stream=True, temperature=temperature, stream_options={"include_usage": True})

    def event_stream():
        full_reply = []
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        for chunk in stream:
            if chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens
                total_tokens = chunk.usage.total_tokens
            if not chunk.choices:
                continue           
            piece = chunk.choices[0].delta.content
            if piece:
                full_reply.append(piece)
                yield f"data: {piece}\n\n"
        db.add(Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="".join(full_reply),
            model=conversation.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        ))
        db.commit()
        yield "data: [DONE]\n\n"

    await event_bus.publish(user_id, "progress", {
        "type":"progress",
        "data":"Thinking..."
    })
    
    return event_stream()