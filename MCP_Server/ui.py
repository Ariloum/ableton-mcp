import gradio as gr
import requests
import json

# Replace with the actual URL of your agent API
API_URL = "http://localhost:8000/prompt"  # Assuming you run FastAPI on port 8000. Adjust if needed.


def query_agent(prompt):
    """Sends a prompt to the LLM agent and returns the response."""
    try:
        payload = {"prompt": prompt}
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        if "error" in data:
            return f"Error: {data['error']}"

        llm_response = data.get("command", {}) # Display the command sent to Ableton
        ableton_result = data.get("result", {})  # Display the result from Ableton

        formatted_output = (
            f"**LLM Command:**\n```json\n{json.dumps(llm_response, indent=2)}\n```\n"
            f"**Ableton Result:**\n```json\n{json.dumps(ableton_result, indent=2)}\n```"
        )

        return formatted_output

    except requests.exceptions.RequestException as e:
        return f"Error connecting to the agent API: {e}"
    except json.JSONDecodeError as e:
        return f"Error decoding JSON response: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# Gradio Interface Definition
iface = gr.Interface(
    fn=query_agent,
    inputs=gr.Textbox(lines=5, placeholder="Enter your prompt here..."),
    outputs=gr.Code(language='json'), # Use Code output for better JSON formatting - removed show_input
    title="LLM Agent Interface",
    description="Interact with the LLM agent that controls Ableton Live.",
)

if __name__ == "__main__":
    iface.launch()
