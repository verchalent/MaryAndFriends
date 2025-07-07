# **AI Agent Collection Deployment Plan**

## **1\. Project Overview**

This document outlines the plan for developing a robust and scalable framework to deploy multiple AI agents, each running in its own Docker container. The existing Mary2Ish agent will serve as the foundational template, allowing for easy replication and customization of new agents through external configuration files. The entire collection of agents will operate on a private Docker network, with Traefik acting as a reverse proxy for external access and routing.

## **2\. Project Goals**

The primary goals for this project are:

* **Deployment Framework:** Create a standardized deployment framework for generating new AI agents based on the Mary2Ish template.  
* **Containerization:** Each AI agent must run in its own isolated Docker container.  
* **Configurability:** Each agent container should be identical in its core application, but its behavior (connections, LLM configuration, prompts) will be customized via external configuration files mounted into the container.  
* **Easy Replication:** Develop an easy-to-replicate template or method for creating new agents and building their respective Docker containers.  
* **User-Driven Deployment:** The user should be able to define desired agents by creating specific configuration files, and then use docker-compose to build and configure these agents.  
* **Private Network & Reverse Proxy:** All agents must reside on a private Docker network, with Traefik used as a reverse proxy for routing external requests to the appropriate agent.

## **3\. Key Components/Technologies**

* **Docker:** Containerization platform for isolating agents.  
* **Docker Compose:** Orchestration tool for defining and running multi-container Docker applications (agents, Traefik, network).  
* **Traefik:** Edge router/reverse proxy for dynamic configuration and routing of requests to agents.  
* Mary2Ish **Agent:** Existing agent codebase serving as the template for all new agents.  
* **Configuration Files (YAML/JSON):** External files to define agent-specific settings (LLM, prompts, connections).  
* **Private Docker Network:** Dedicated network for inter-agent communication and Traefik routing.

## **4\. Architecture Design**

### **4.1. Agent Container Structure**

Each agent container will be built from a single Dockerfile based on the Mary2Ish agent's core application. The key principle is that the *application code within each container is identical*.

* **Base Image:** A suitable base image (e.g., Python slim, Node.js, depending on Mary2Ish's tech stack).  
* **Application Code:** The Mary2Ish application code will be copied into the container.  
* **Entrypoint/Command:** The container's entrypoint will execute the agent application.  
* **Volume Mounts:** Crucially, a volume will be mounted from the host machine into the container, containing the agent's specific configuration files. This allows for runtime customization without rebuilding the image.

\# Example Dockerfile for an agent  
FROM python:3.9-slim-buster \# Or appropriate base image for Mary2Ish  
WORKDIR /app  
COPY ./Mary2Ish/ . \# Copy the core Mary2Ish agent code  
\# Install dependencies (if any)  
\# RUN pip install \-r requirements.txt  
EXPOSE 8000 \# Or the port Mary2Ish listens on  
CMD \["python", "mary2ish\_agent.py"\] \# Or the command to run the agent

### **4.2. Configuration Management**

Configuration for each agent will strictly follow the primitives established within the Mary2Ish project. This involves specific files and directories that need to be mounted for each agent.

* **Structure:** A dedicated configs directory on the host will contain subdirectories for each agent, e.g., configs/agent\_alpha/, configs/agent\_beta/. Each agent's subdirectory will contain the specific configuration files (.yaml, .json, etc.) as defined by Mary2Ish's internal structure.  
* **Example Files at Build:** The Mary2Ish Dockerfile should include example or default configuration files at build time. These serve as a baseline and ensure the container has a runnable configuration even without external mounts.  
* **Specific File Mounting:** In docker-compose.yml, individual configuration files or specific subdirectories from the host's configs/agent\_name/ directory will be mounted into the precise paths expected by the Mary2Ish agent application inside the container. This allows for runtime override of the example files included at build.

\# Example docker-compose.yml snippet for an agent service  
services:  
  agent\_alpha:  
    build: ./Mary2Ish \# Path to the Mary2Ish Dockerfile context  
    volumes:  
      \# Example: Mount specific config files/directories as per Mary2Ish's structure  
      \- ./configs/agent\_alpha/main\_config.yaml:/app/config/main\_config.yaml  
      \- ./configs/agent\_alpha/prompts:/app/prompts \# If prompts are in a directory  
      \- ./configs/agent\_alpha/connections.json:/app/data/connections.json  
    environment:  
      \- AGENT\_CONFIG\_ENV\_VAR=/app/config/main\_config.yaml \# Example: if Mary2Ish uses an env var  
    networks:  
      \- ai\_agents\_network  
    labels:  
      \- "traefik.enable=true"  
      \- "traefik.http.routers.agent-alpha.rule=Host(\`agent-alpha.local\`)" \# Example routing rule  
      \- "traefik.http.routers.agent-alpha.entrypoints=web"

### **4.3. Networking**

A dedicated private Docker network will be created to ensure agents can communicate with each other (if needed) and with Traefik, while remaining isolated from the host's default network.

* **Private Network:** A bridge network named ai\_agents\_network (or similar) will be defined in docker-compose.yml.  
* **Traefik Integration:**  
  * Traefik will run in its own container, connected to ai\_agents\_network.  
  * Traefik will be configured to listen for Docker events, dynamically discovering new agent services and configuring routes based on Docker labels.  
  * Each agent service in docker-compose.yml will have labels that Traefik uses to define routing rules (e.g., Host() rules for subdomains or paths).

\# Example docker-compose.yml snippet for Traefik and network  
services:  
  traefik:  
    image: traefik:v3 \# Using :v3 to point to the latest stable version in the v3 series  
    command:  
      \- \--api.insecure=true \# For testing, remove in production  
      \- \--providers.docker=true  
      \- \--providers.docker.exposedbydefault=false  
      \- \--entrypoints.web.address=:80  
    ports:  
      \- "80:80"  
      \- "8080:8080" \# Traefik Dashboard (for testing)  
    volumes:  
      \- /var/run/docker.sock:/var/run/docker.sock:ro  
    networks:  
      \- ai\_agents\_network

networks:  
  ai\_agents\_network:  
    driver: bridge

## **5\. Deployment Workflow**

The user-driven deployment workflow will be as follows:

1. **Define Agent Configurations:** The user creates a new directory under configs/ (e.g., configs/new\_agent/) and places the agent-specific config.yaml (and other necessary files, following Mary2Ish's structure) within it.  
2. **Update** docker-compose.yml**:** The user adds a new service entry to docker-compose.yml for the new\_agent. This entry will:  
   * Reference the Mary2Ish codebase for building the image.  
   * Mount the *specific* configuration files and directories from configs/new\_agent/ into the container as required by Mary2Ish.  
   * Assign the agent to the ai\_agents\_network.  
   * Add Traefik labels for routing (e.g., traefik.http.routers.new-agent.rule=Host('new-agent.local')).  
3. **Build and Run:** The user executes docker-compose up \--build \-d. This command will:  
   * Build the Docker image for the Mary2Ish template (if not already built or if changes detected).  
   * Create and start containers for Traefik and all defined agents.  
   * Traefik will automatically detect the new agent service and configure routing.

## **6\. Development Steps/Phases**

1. **Phase 1: Mary2Ish Containerization \- Completed**  
   * The Mary2Ish agent is already containerized, fully built, and tested. It will serve as the stable template for all new agents.  
2. **Phase 2: Basic Multi-Agent Deployment**  
   * Set up a docker-compose.yml to run two identical Mary2Ish containers, each with a different mounted configuration.  
   * Verify both agents run simultaneously and independently.  
   * Establish the private Docker network.  
3. **Phase 3: Traefik Integration**  
   * Add Traefik to the docker-compose.yml.  
   * Configure Traefik to use Docker as a provider.  
   * Add Traefik labels to agent services for basic routing (e.g., by host header).  
   * Test accessing each agent via Traefik.  
4. **Phase 4: Templating and Documentation**  
   * Create clear documentation for the user on how to add new agents (creating config files, updating docker-compose.yml).  
   * Develop a simple script or guide for generating the initial configs/new\_agent/ structure.  
   * Refine docker-compose.yml for clarity and ease of use.