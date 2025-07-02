# **Project Plan: Embeddable AI Chat & Web GUI**

## **1\. Project Overview**

This project aims to develop a lightweight, embeddable AI chat interface with a web-based Graphical User Interface (GUI). The entire application will be containerized using Docker, allowing for easy deployment and integration into existing web environments via an iframe. The core AI logic will leverage fast-agent.ai to interact with various Large Language Model (LLM) providers.

## **2\. Core Technologies**

* **Containerization:** Docker  
* **AI Agent/LLM Orchestration:** fast-agent.ai  
* **Web GUI Framework:** Streamlit (initial proposal, confirmed for rapid prototyping)  
* **Language:** Python (for fast-agent.ai and Streamlit)

## **3\. Design Goals**

The following are the primary design objectives for this project:

* **Embeddability:** The web GUI must be designed to be loaded seamlessly within an iframe, ensuring minimal UI artifacts (e.g., headers, footers, sidebars) beyond the core input and output areas. It should also dynamically adjust its size to fit the iframe's dimensions.  
* **Docker Deployment:** The entire application, including the AI agent and web GUI, must be fully deployable as a self-contained Docker container.  
* **External LLM Provider Support:** The fast-agent.ai library will be used to facilitate connections to various external LLM providers, allowing flexibility in backend AI models.  
* **Configurability:** Essential configurations (e.g., API keys, LLM endpoints, agent parameters) should be mountable into the Docker container at launch time, enabling easy environment-specific setup without rebuilding the image.

## **4\. High-Level Architecture**

The proposed architecture involves two main components within the Docker container:

1. **Streamlit Web GUI:**  
   * Serves as the user-facing interface, handling chat input and displaying responses.  
   * Communicates with the fast-agent.ai backend.  
   * Designed with a minimalist layout suitable for iframe embedding.  
2. **fast-agent.ai Backend:**  
   * Manages the interaction with external LLM providers.  
   * Receives user queries from the Streamlit GUI.  
   * Processes queries, interacts with the configured LLM, and returns responses.  
   * Configuration for LLM providers will be loaded from mounted files/environment variables.

graph TD  
    User \--\>|Accesses| WebPage  
    WebPage \--\>|Embeds| Iframe  
    Iframe \--\>|Loads| DockerContainer(Docker Container)

    subgraph DockerContainer  
        StreamlitGUI(Streamlit Web GUI)  
        FastAgentAI(fast-agent.ai)  
    end

    StreamlitGUI \--\>|User Input| FastAgentAI  
    FastAgentAI \--\>|LLM API Call| ExternalLLM(External LLM Provider)  
    ExternalLLM \--\>|Response| FastAgentAI  
    FastAgentAI \--\>|Chat Response| StreamlitGUI  
    StreamlitGUI \--\>|Displays| Iframe

## **5\. Deployment Strategy**

The application will be deployed as a Docker image. A Dockerfile will define the environment, dependencies, and application code. Configuration files (e.g., .env files, JSON config files) containing sensitive information like API keys or LLM provider details will be mounted into the container at runtime, ensuring secure and flexible deployment.

Example Docker run command (conceptual):

docker run \-d \\  
  \-p 8501:8501 \\  
  \-v /path/to/your/config:/app/config \\  
  your-chat-app:latest

## **6\. Key Design Decisions & Implementation Details**

### **6.1. UI Framework Choice: Streamlit**

* **Decision:** We will proceed with **Streamlit** for the initial implementation.  
* **Rationale:** Streamlit offers rapid development capabilities, which aligns well with getting a functional prototype quickly. While it has some inherent UI elements, its ability to hide the main menu and sidebar (st.set\_page\_config(layout="wide", initial\_sidebar\_state="collapsed") and custom CSS to hide the "Deploy" button) makes it sufficiently minimal for an iframe. If, during development, we find Streamlit's limitations too restrictive for dynamic sizing or extreme minimalism, we can reconsider a Flask/FastAPI backend with a custom HTML/JS frontend.

### **6.2. Dynamic Sizing for Iframe Embedding**

* **Approach:** We will use the window.postMessage() API for cross-origin communication between the iframe (Streamlit app) and the parent web page.  
* **Implementation Details:**  
  * **Inside the Streamlit App (iframe):**  
    * A small JavaScript snippet will be injected (e.g., using st.components.v1.html or a custom Streamlit component) that periodically measures the height of the Streamlit content.  
    * This height will then be sent to the parent window using window.parent.postMessage({ height: document.body.scrollHeight, source: 'streamlit-chat-app' }, '\*').  
  * **In the Parent Web Page:**  
    * An event listener will be set up to listen for messages from the iframe: window.addEventListener('message', (event) \=\> { ... }).  
    * Upon receiving a message from the expected source, the parent page will update the height attribute or CSS style of the iframe element.  
* **Considerations:** This requires cooperation from the parent web page. The \* in postMessage should ideally be replaced with the specific origin of the parent page for better security in a production environment.

### **6.3. Security Considerations**

* **Iframe Sandboxing:** The parent web page embedding the iframe should use the sandbox attribute (e.g., \<iframe sandbox="allow-scripts allow-same-origin allow-popups allow-forms" ...\>) to restrict the iframe's capabilities and mitigate potential security risks. The specific allow-\* values will depend on the required functionality.  
* **CORS Policies:** Ensure that the Dockerized Streamlit application's server (if it's serving any static assets or APIs directly) has appropriate Cross-Origin Resource Sharing (CORS) headers configured to allow requests from the domain hosting the parent web page. Streamlit generally handles this for its core functionality, but custom endpoints might need attention.  
* **Secure API Key Handling:**  
  * API keys for external LLM providers should **never** be hardcoded in the Docker image or exposed directly to the client-side (Streamlit UI).  
  * They will be passed into the Docker container via **environment variables** or **mounted configuration files** (e.g., a .env file or a JSON config file).  
  * The fast-agent.ai backend will access these securely from the environment.

### **6.4. Error Handling**

* **User Feedback:** Implement clear and concise error messages within the Streamlit UI to inform the user if an LLM call fails, if there's a configuration issue, or if the agent encounters an unexpected problem.  
* **Logging:** Ensure robust logging within the fast-agent.ai backend and Streamlit application to capture errors, warnings, and debug information. This will be crucial for troubleshooting issues in the Docker container.  
* **Graceful Degradation:** Design the application to handle transient failures (e.g., network issues with LLM providers) gracefully, perhaps with retry mechanisms or informative "service unavailable" messages.

### **6.5. Session Management (Chat History)**

* **Approach:** For a simple, embeddable chat, we will initially manage chat history **in-memory within the Streamlit session state**.  
* **Implementation Details:** Streamlit's st.session\_state is ideal for this. Each user's chat interaction (input and LLM response) can be appended to a list stored in st.session\_state.  
* **Considerations:**  
  * This approach is stateless from the Docker container's perspective (each new connection gets a new session).  
  * If the Docker container restarts or scales, chat history for active users will be lost. This is acceptable for a "simple" embeddable chat.  
  * **Future Consideration (RAG/Memory):** For persistent history across sessions or users, or to incorporate Retrieval Augmented Generation (RAG) capabilities for long-term memory, a lightweight database (e.g., SQLite mounted as a volume) or integration with a dedicated vector database/memory service would be required. This adds complexity beyond the initial scope. We will stick to in-memory for now.

### **6.6. fast-agent.ai Configuration**

* **Approach:** All fast-agent.ai related configuration files will be supplied to the Docker container via **mounted volumes**.  
* **Implementation Details:**  
  * The Docker container will expect a specific directory (e.g., /app/config/fastagent) where these configuration files are located.  
  * At runtime, the user will mount their local configuration directory to this path using the \-v flag in the docker run command.  
  * The key configuration files to be mounted include:  
    * system\_prompt.txt: Contains the system-level instructions or persona for the LLM.  
    * fastagent.config.yaml: Defines the agent's overall configuration, including LLM provider settings, tool definitions, etc.  
    * fastagent.secrets.yaml: Contains sensitive information like API keys for LLM providers, which should be kept separate from the main configuration.  
* **Example Docker run command (refined):**  
  docker run \-d \\  
    \-p 8501:8501 \\  
    \-v /path/to/your/fastagent\_configs:/app/config/fastagent \\  
    your-chat-app:latest

## **7. Next Steps**

* Develop the basic Streamlit GUI with input and output areas.  
* Integrate fast-agent.ai for a basic LLM call, ensuring it loads configurations from the mounted volume.  
* Create the Dockerfile for containerization.  
* Implement the postMessage logic for dynamic iframe sizing.