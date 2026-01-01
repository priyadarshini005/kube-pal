import os
import sys
import requests

model = "OLLAMA-MISTRAL"

SYSTEM_PROMPT = """
You're a Kube-Pal, who takes in an input in normal english language, and gives just a kubectl command as an output. 
So basically you're buddy who is a kubernetes expert and aware of all the existing kubectl commands.
- Never output anything else other than the kubectl command even if it's a follow-up question, except for the below fixed responses if the question is about yourself.

- If the user wishes something like, "Good morning/Hey/Hello/Hi, etc" just wish the user back with the same phrase and say you're here to help with the kubernetes commands.
    For example, 
    User: "Hai"
    Assistant: "Hai, I'm Kube-Pal, your kubernetes buddy and I'm here to help you with kubectl commands. Let me know if you need my help with any kubectl commands.."

    User: "Helloo"
    Assistant: "Helloo, I'm Kube-Pal, your kubernetes buddy and I'm here to help you with kubectl commands. Let me know if you need my help with any kubectl commands.."

- If the user asks for any other information outside the kubernetes world (even if it about yourself, how do you know kubernetes? or what model are you?, etc., anything other than the below mentioned questions), then, your reply must be fixed to,
 "Sincere apologies that I can only help you with kubernetes commands and not any other topics other than this."

- Never respond back with any other responses if the questions goes out of the kubernetes context, except for the above defined fixed responses, for questions that gives non-kubectl outputs.

- If the user asks about yourself, like "who are you?", you should be telling, "I'm your kubernetes buddy and I'm here to help you with kubectl commands.". 

- If the user asks how you're doing, then, you need to just say, "I'm doing good and I'd do great if I get a chance to help you with any kubectl (kubernetes) commands"

- If the user asks where you exist, then, you need to just say, "I'm right here on your machine, helping you by generating kubectl commands.".

- If the user asks anything incomplete, then, modify the last command

- If the user says something like, good work, thanks, thanks for the help, great, awesome, etc., you just need to say, "Happy to help! Let me know if you need my help with any other kubectl commands.."

General Rules:
- Don't explain anything about the command.
- Don't execute any command.
- If the question is kubernetes-related, and is quite ambiguous, then, ask for clarification.
- Output just one kubectl command

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

def build_prompt(query, state):
    memory = ""
    if state.get("prev_cmd"):
        memory = f"Previous Command: {state['prev_cmd']}"
    return f"""
    {SYSTEM_PROMPT}
    {memory}
    NOTE: Always use <namespace> as the placeholder, if namespace is an allowed option in the kubectl command.
    User: {query}
    Assistant: 
    """

def query_ollama_mistral(query, output):
    try:
        prompt = build_prompt(query, output)

        request_json = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 80
                }
        }
        if(output.get("context")):
            request_json["context"] = output["context"]

        response = requests.post("http://localhost:11434/api/generate", json=request_json)
        response.raise_for_status()
        json_response = response.json()
        output["prev_cmd"] = json_response["response"].strip()
        if output["prev_cmd"].startswith("kubectl"):
            output["context"] = json_response["context"]
        return output
    except Exception as e:
        print(f"ERROR: Failed to generate response due to an unknown error: {e}")
        return output

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
    output = {
        "prev_cmd": None,
        "context": None
    }
    risk_metrics = {
        "LOW": 
            ["get", "describe", "logs", "top"],
        "MEDIUM":
            ["exec", "port-forward", "cp", "edit"],
        "HIGH":
            ["delete", "apply", "patch", "scale", "replace", "rollout", "drain"]
    }
    while(True):
        query = get_user_input()
        if not query:
            continue
        match model:
            case "OLLAMA-MISTRAL":
                output = query_ollama_mistral(query, output)
            case "OPENAI":
                from openai import OpenAI
                output = query_openai(query)
        command = output.get("prev_cmd")
        if command != None:
            if not "kubectl" in command.split(" ")[0]:
                print(command)
                continue
            print(command)
            risk_level = "LOW" if command.split(" ")[1] in risk_metrics["LOW"] else "MEDIUM" if command.split(" ")[1] in risk_metrics["MEDIUM"] else "HIGH"
            match risk_level:
                case "MEDIUM" | "HIGH": print(f"WARNING: This is a {risk_level} risk command!")

if __name__ == "__main__":
    main()
