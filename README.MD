## AI Document Insight Extractor

## Project Overview

This project is a prototype of a full-stack web application designed to automate document analysis, extract key insights and generate summaries through large-scale language modelling (LLM).Users can interact with the AI in natural language by pasting text, view chat history, and process potential API keys. the entire application is packaged as a Docker image for easy deployment and testing.

## Core Features and Technology Stack
* **Frontend**: Provides an intuitive user interface using **React.js** (built with **Vite**).
    * Allows users to paste UTF-8 encoded plain text documents.
    * Provides natural language query input box to interact with AI.
    * Display real-time chat history (user questions and AI responses).
    * Clearly display error messages to ensure the app doesn't crash.
    * Provide UI interface for entering API Key (if LLM requires external API).
    * Detect and notify users of network connection status.
* **Backend**: RESTful API service built on **Flask**.
    * Responsible for loading and managing large language models for inference.
    * Processes user requests and performs text analysis (summarisation, insight extraction).
    * Efficiently serves front-end static files through the **WhiteNoise** library.
* **Large Language Models (LLM)**: load and run LLMs using the **Hugging Face Transformers** library.
    * * Default attempts to load `Meta-llama/Llama-3.2-1B`.** Please note that this model may require Hugging Face permissions.If it is inaccessible, I have commented out alternatives in the code and suggest using a publicly available model (e.g. `google/flan-t5-base`) and explaining this trade-off in the interview.**
    * The model is loaded once at application startup to optimise inference performance.
* **Containerisation**: multi-stage builds using **Docker** to package the front-end and back-end into a single, portable image.
    * All source code and build products are located in the `/home/src` directory within the Docker container.
    * The application is started with the `docker run -p 8080:8080 <image_tag>` command.
* **Tests**: Contains unit and integration tests based on **Python `unittest`**.
    * Test scripts are located at `/home/src/tests/run_tests.py`.
    * Can be executed with the `docker run <image_tag> python /home/src/tests/run_tests.py` command.



## Design decisions and trade-offs

1. **Single Docker image for full stack**.
    * **Decision**: Chose to package both the front-end and back-end into a single Docker image and serve static files and handle API requests via a Python Flask application (with WhiteNoise).
    * **Benefits**: Simplified deployment with a single `docker run` command to launch the entire application, meeting interview requirements.Reduces the complexity of inter-container network configuration.
    * **Cons**: Mirrors can be relatively large.Static file serving is not as efficient as a dedicated web server (e.g. Nginx), but is sufficient for prototype applications.
2. **LLM model loading**.
    * **Decision**: LLM is loaded into memory when the Flask application starts.
    * **Advantages**: Avoids reloading the model for each request, greatly reducing inference latency.
    * **Disadvantages**: Application startup can take longer and each Gunicorn worker process loads a copy of the model, which can increase memory (and VRAM) consumption.This is acceptable for small LLMs, but may require more complex deployment strategies (e.g., separate model services) for very large models.
3. **Prompt Engineering**.
    * **Decision**: Builds detailed prompt templates combining document text, user queries, and chat history.
    * **Benefits**: Helps guide the LLM to generate more relevant and accurate responses, and maintains dialogue context.
    * **Challenges**: Prompt engineering is iterative and requires continuous optimisation.Document length limits the amount of context that can be included.
4. **Performance Optimisation (p95 < 3s)**.
    * **QUANTIFICATION**: Default model loading attempts to use `bfloat16` (`torch_dtype=torch.bfloat16`), which helps to reduce memory footprint and speed up inference on supported GPUs.If more aggressive optimisations are required, `bitsandbytes` can be integrated for `int8` or `int4` quantisation.
    * **Gunicorn**: Starting 4 worker processes with `gunicorn -w 4` can handle concurrent requests and help reduce latency in multi-user scenarios.
    * **Model-resident**: Avoids reloading models.
    * **Limitations**: 3 seconds P95 latency may still be challenging for 1B parameter LLM on CPU.Actual performance will be highly dependent on the underlying hardware (especially GPU) and the specific inference efficiency of the LLM.
5. **Responsible AI**.
    * **Bias**: Recognise that all LLMs may have biases introduced by the training data.In practice, model outputs need to be monitored and manually reviewed when necessary.
    * **Transparency/Interpretability**: The black-box nature of LLM makes it difficult to fully explain the decision-making process.Through clear cue engineering, we try to guide the model to give relevant and accurate outputs, and clearly inform the user of what happens when the AI is unable to answer.
    * **Data Privacy**: The application is designed to process user input in plain text.In a production environment, any sensitive data would need to be encrypted during transmission and processing, and comply with relevant data privacy regulations.No data persistence is involved in this project prototype, and all data is destroyed at the end of the session (except for chat history which is maintained on the front-end).
    * **Error Handling**: Ensure that the front-end clearly displays error messages returned by the back-end instead of crashing, improving user experience and system stability.


## Installation and operation

### Prerequisites

* Docker (v20.10.0+ or later)
* At least 16GB RAM on local machine with 4 CPU cores.If using a GPU, 16GB VRAM and NVIDIA Docker Runtime are required.

### Build the Docker image

Execute the following command in the project root directory (the directory containing the ``Dockerfile``):

``bash
docker build -t ai-doc-analyzer .