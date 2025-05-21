import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from whitenoise import WhiteNoise
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# --- Log Configuration Log Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask Application Initialisation---
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')


app.wsgi_app = WhiteNoise(app.wsgi_app, root=app.static_folder, index_file=True)


# --- LLM Model Global Variables and Load Functions ---
model = None
tokenizer = None

device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Detected device: {device}")

MODEL_NAME = "google/flan-t5-base"


def load_ai_model():
    """
    Load the AI model and the disambiguator.
    This function is called at app startup and loads the model into memory, avoiding reloading it for each request.
    """
    global model, tokenizer #, nlp_pipeline
    logging.info(f"Attempting to load model '{MODEL_NAME}'...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        model.to(device) 
        model.eval() 
        logging.info(f"Model '{MODEL_NAME}' loaded successfully to {device}.")



    except Exception as e:
        logging.error(f"Error loading model '{MODEL_NAME}': {e}", exc_info=True)
        model = None
        tokenizer = None

with app.app_context():
    load_ai_model()


# --- LLM Logic of Reasoning ---
def get_llm_response(document_text: str, user_query: str, chat_history: list) -> str:
    """
    Use LLM to generate responses to user queries.
    Combine document content, user queries and chat history to build prompts.
    """
    if not model or not tokenizer: # or not nlp_pipeline:
        raise ValueError("AI model is not loaded or failed to initialize.")

    # --- Prompt Engineering ---

    # Constructing Context for Chat History
    history_str = ""
    for item in chat_history:
        history_str += f"User: {item['user_query']}\nAI: {item['ai_response']}\n"
    if history_str:
        history_str = f"Previous conversation:\n{history_str}\n"

    # prompt
    prompt_template = (
        f"You are an intelligent assistant for document analysis. "
        f"Based on the provided document and the ongoing conversation, answer the user's query concisely and accurately. "
        f"If the answer cannot be found in the document, state that clearly.\n\n"
        f"--- Document ---\n{document_text}\n\n"
        f"--- Conversation History ---\n{history_str}"
        f"--- Current User Query ---\n{user_query}\n\n"
        f"--- Assistant's Response ---"
    )


    max_input_length = tokenizer.model_max_length - 100 

    inputs = tokenizer(prompt_template, return_tensors="pt", truncation=True, max_length=max_input_length).to(model.device)

    # Generated parameters
    generation_kwargs = {
        "max_new_tokens": 500, 
        "num_return_sequences": 1,
        "do_sample": True,     
        "temperature": 0.7,     
        "top_k": 50,           
        "top_p": 0.95,          
        "eos_token_id": tokenizer.eos_token_id, 
        "pad_token_id": tokenizer.eos_token_id  
    }

    try:
        logging.info("Starting LLM inference...")
        outputs = model.generate(**inputs, **generation_kwargs)
        generated_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        logging.info("LLM inference completed.")
        return generated_text.strip()
    except Exception as e:
        logging.error(f"Error during LLM inference: {e}", exc_info=True)
        raise RuntimeError("Failed to generate response from AI model. Please try again.")


# --- API endpoint---
api_keys = {}

@app.route('/api/set-api-key', methods=['POST'])
def set_api_key():
    """
    API endpoint for receiving and storing API Keys.

    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    key_name = data.get('key_name')
    key_value = data.get('key_value')

    if not key_name or not key_value:
        return jsonify({"error": "Missing 'key_name' or 'key_value'"}), 400

    api_keys[key_name] = key_value
    logging.info(f"API Key for '{key_name}' set successfully.")
    return jsonify({"message": f"API Key for '{key_name}' set successfully."}), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    The main chat API endpoint that receives documents, user queries, and chat history, and returns LLM responses.
    """
    logging.info("Received /api/chat request.")
    if not request.is_json:
        logging.warning("Request is not JSON.")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    document_text = data.get('document_text')
    user_query = data.get('user_query')
    chat_history = data.get('chat_history', []) 

    if not document_text or not user_query:
        logging.warning("Missing 'document_text' or 'user_query' in request.")
        return jsonify({"error": "Missing 'document_text' or 'user_query' field"}), 400

    try:
        response_text = get_llm_response(document_text, user_query, chat_history)
        logging.info("Successfully generated LLM response.")
        return jsonify({"response": response_text}), 200
    except ValueError as e:
        logging.error(f"LLM model error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    except RuntimeError as e:
        logging.error(f"LLM inference error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# --- Root route for provisioning front-end applications---
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# --- Application Launch Portal---
if __name__ == '__main__':
    logging.info("Starting Flask development server.")
    app.run(host='0.0.0.0', port=8080, debug=True) 