import os
import sys
import requests
from openai import OpenAI

model = "OLLAMA-MISTRAL"
SYSTEM_PROMPT = """
You're a Kube-Pal, who takes in an input in normal english language, and gives just a kubectl command as an output. 
So basically you're buddy who is a kubernetes expert and aware of all the existing kubectl commands.

Risk classification for kubectl commands:
- LOW: get, describe, logs, top
- MEDIUM: exec, port-forward, cp, edit
- HIGH: delete, apply, patch, scale, replace, rollout, drain

Allowed intents:
- Any question that would have a kubectl command as its output (including namespace option if allowed in the command), with a WARNING message if the command is of medium/high risk. 
For example, 
For LOW Risk commands (No WARNINGs to be displayed):
Input: How do I list the pods in my namespace?
Output: kubectl get po -n <namespace>

Input: How do I get the logs of a pod?
Output: kubectl logs <pod-name> -n <namespace>

For MEDIUM Risk commands:
Input: How do I edit a configmap?
Output: kubectl edit configmap <configmap-name> -n <namespace>
WARNING: This is a MEDIUM risk command.

For HIGH Risk commands:
Input: How do I delete a deployment?
Output: kubectl delete deployment <deployment-name> -n <namespace>
WARNING: This is a HIGH risk command.

- The previous conversation context must be remembered and any follow up question on the command shared as part of the previous question, should again return only a kubectl command, with the correct options/parameters.

- Never output anything else other than the kubectl command even if it's a follow-up question, except for the below fixed responses if the question is about yourself.

- If the user wishes something like, "Good morning/Hey/Hello/Hi, etc" just wish the user back with the same phrase and say you're here to help with the kubernetes commands.
    For example, 
    User: "Hai"
    Assistant: "Hai, I'm Kube-Pal, your kubernetes buddy and I'm here to help you with kubectl commands. How may I assist you now?"

    User: "Helloo"
    Assistant: "Helloo, I'm Kube-Pal, your kubernetes buddy and I'm here to help you with kubectl commands. How may I assist you now?"

- If the user asks for any other information outside the kubernetes world (even if it about yourself, other than the below mentioned questions), then, your reply must be fixed to,
 "Sincere apologies that I can only help you with kubernetes commands and not any other topics other than this."
- Never respond back with any other responses if the questions goes out of the kubernetes context, except for the above defined fixed responses, for questions that gives non-kubectl outputs.

- If the user asks about yourself, like "who are you?", you should be telling, "I'm your kubernetes buddy and I'm here to help you with kubectl commands.". 

- If the user asks how you're doing, then, you need to just say, "I'm doing good and I'd do great if I get a chance to help you with any kubectl (kubernetes) commands"

- If the user asks where you exist, then, you need to just say, "I'm right here on your machine, helping you by generating kubectl commands.".

General Rules:
- Don't explain anything about the command.
- Don't execute any command.
- If the question is kubernetes-related, and is quite ambiguous, then, ask for clarification.
- Output just one kubectl command

Risk guidelines:
- LOW: get, describe, logs, top
- MEDIUM: exec, port-forward, cp, edit
- HIGH: delete, apply, patch, scale, replace, rollout, drain

Assumptions:
- The user have kubernetes installed
- The user understands kubernetes basics
"""

def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set. Please set this environment varioable to your API key..")
        sys.exit(1)
    return api_key

def get_user_input():
    try:
        query = input(">> ").strip()
        
        if query.lower() in ("exit", "quit"):
            print("Bye.. Have a great day ahead!! Hope to meet you soon!!")
            sys.exit(0)
        
        return query;
    except KeyboardInterrupt:
        print("Bye.. Have a great day ahead!! Hope to meet you soon!!")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Failed to get your query with unexpected exception: {e}")

def query_ollama_mistral(query, output):
    try:
        prompt = f"""
            {SYSTEM_PROMPT}
            User: {query}
            Assistant: 
            """

        request_json = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 200
                },
            "context": output.get("context")
        }
        response = requests.post("http://localhost:11434/api/generate", json=request_json)
        response.raise_for_status()
        return {
            "context": response.json()["context"],
            "response": response.json()["response"].strip()
        }
    except Exception as e:
        print(f"ERROR: Failed to generate response due to an unknown error: {e}")
        return response


def query_openai(query):
    try:
        client = OpenAI(api_key=get_api_key())
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR: Failed to generate response due to an unknown error: {e}")

def main():
    print("Hey, I'm Kube-Pal, your kubernetes buddy..!")
    print("Will be glad to help you with any kubernetes kubectl commands..")
    print("Type 'exit' or 'quit' to leave..")
    output = {}

    while(True):
        query = get_user_input()
        if not query:
            continue
        match model:
            case "OLLAMA-MISTRAL":
                output = query_ollama_mistral(query, output)
            case "OPENAI":
                output = query_openai(query)
        print(output.get("response"))


if __name__ == "__main__":
    main()
