# **Junior SDE Task List: AI Agent Collection Deployment**

This document outlines the detailed tasks for Junior Software Development Engineers (SDEs) to complete the AI Agent Collection Deployment project. Each phase includes specific tasks, self-check points, and a crucial User Acceptance Testing (UAT) checkpoint with the User/Product Manager (PM) before proceeding.

## **Phase 1: Core Agent Deployment Automation**

**Objective:** Establish an automated process for configuring and deploying individual AI agents based on the Mary2Ish template, including generating their configurations and updating the docker-compose setup.

**Tasks for Jr SDEs:**

* [x] **Task 1.1: Review Mary2Ish Project for Configuration Requirements**  
  * [x] Deeply review the Mary2Ish subfolder to identify all necessary configuration files, their expected formats (YAML, JSON, etc.), and the internal paths where the Mary2Ish agent expects them to be located within its container.  
  * [x] Document these specific file names and their internal container paths.  
  * [x] **Self-Check:** Have all configuration primitives and their required locations been identified and documented?  
* [x] **Task 1.2: Create a Simple Agent Config Template**  
  * [x] Create a template\_agent\_configs directory in the project root.  
  * [x] Inside template\_agent\_configs, create a complete set of *example* configuration files (e.g., main\_config.yaml.example, prompts/, connections.json.example) that mirror the structure and file names identified in Task 1.1. These files should contain generic, default values.  
  * [x] **Self-Check:** Does the template\_agent\_configs directory contain all required example config files, ready for copying?  
* [x] **Task 1.3: Create Thorough README for User Configuration**  
  * [x] Create or update the README.md in the project root.  
  * [x] Add a detailed section explaining to the user how to create configuration folders for their desired agents.  
  * [x] Clearly state that the folder name (e.g., configs/my\_agent\_name/) should directly map to the desired agent name.  
  * [x] Instruct the user to copy the contents of template\_agent\_configs into their new agent's folder and customize the values.  
  * [x] **Self-Check:** Is the README clear and comprehensive for a user to manually prepare agent configurations?  
* [x] **Task 1.4: Develop Python Script for Automated docker-compose Generation**  
  * [x] Write a Python script (e.g., generate\_agents.py) that will:  
    * [x] Accept a list of agent names as input (e.g., via command-line arguments or a simple input file).  
    * [x] For each agent name:  
      * [x] Create the agent's specific configuration directory under configs/ (e.g., configs/agent\_name/).  
      * [x] Copy the contents of template\_agent\_configs into this new agent's directory.  
      * [x] **Generate/Update docker-compose.yml:**  
        * [x] Read the base docker-compose.yml (which will initially contain only the network definition and potentially Traefik, but no agent services).  
        * [x] Add a new service entry for the agent, referencing the Mary2Ish build context (build: ./Mary2Ish).  
        * [x] Configure *all specific volume mounts* for the agent's config files from configs/agent\_name/ into the container's expected paths (as identified in Task 1.1).  
        * [x] Assign the agent to the ai\_agents\_network.  
        * [x] Add appropriate Traefik labels for routing (e.g., traefik.http.routers.agent-name.rule=Host(\\agent-name.local\`)\`).  
        * [x] Ensure the script can append new services without overwriting existing ones. Use a robust YAML library (e.g., PyYAML) for safe manipulation.  
    * [x] The script should then instruct the user to run docker-compose up \--build \-d to bring up the newly configured agents.  
  * [x] **Self-Check:** Does the script correctly create config folders and generate/update docker-compose.yml for a new set of agents (e.g., agent\_alpha, agent\_beta)? Does docker-compose config still pass after script execution?

### **Checkpoint 1.0: User Acceptance Testing (UAT) with User/PM**

* **Validation:** Demonstrate the full automated workflow for agent creation:  
  * ✅ Show the template\_agent\_configs structure.  
  * ✅ Run the generate\_agents.py script with a list of new agent names.  
  * ✅ Verify that the script creates the respective configs/ folders with copied templates.  
  * ✅ Show that docker-compose.yml has been correctly updated with the new agent services, including all necessary volume mounts and Traefik labels.  
  * 🔄 Run docker-compose up \--build \-d and confirm that all generated agents start successfully and load their unique configurations.  
* **User Acceptance:** Obtain explicit confirmation from the User/PM for the completeness, usability, and robustness of the automated agent generation process.

**Status**: ✅ Phase 1 COMPLETE - Ready for UAT  
**Date Completed**: July 7, 2025  
**Agents Created**: mary, rick  
**Documentation**: See `docs/PHASE1_COMPLETE.md` for full summary

## **Phase 2: Traefik Integration and Network Setup**

**Objective:** Refactor the Docker Compose setup to include a dedicated private network for agents and deploy/configure Traefik as the reverse proxy.

**Tasks for Jr SDEs:**

* [x] **Task 2.1: Establish Dedicated Docker Network**  
  * [x] Modify the docker-compose.yml (which is now primarily managed by the generate\_agents.py script) to define a single ai\_agents\_network of type bridge.  
  * [x] Ensure the generate\_agents.py script assigns all generated agent services to this ai\_agents\_network.  
  * [x] **Self-Check:** After running generate\_agents.py and docker-compose up, does docker network ls show ai\_agents\_network and docker inspect \<agent\_container\_id\> confirm the agent is on this network?  
* [x] **Task 2.2: Deploy Latest Traefik Container**  
  * [x] Add a new service named traefik to the base docker-compose.yml template (that generate\_agents.py reads from).  
  * [x] Use the traefik:v3 image (or traefik:latest if preferred for always getting the absolute newest).  
  * [x] Configure Traefik to expose ports 80 (for web traffic) and 8080 (for the dashboard, for testing).  
  * [x] Mount the Docker socket (/var/run/docker.sock) into the Traefik container for Docker provider access.  
  * [x] Connect Traefik to the ai\_agents\_network.  
  * [x] Add Traefik commands: \--api.insecure=true, \--providers.docker=true, \--providers.docker.exposedbydefault=false, \--entrypoints.web.address=:80.  
  * [x] **Self-Check:** Does Traefik start successfully and is its dashboard accessible at http://localhost:8080?  
* [x] **Task 2.3: Configure Traefik as Proxy for Agents**  
  * [x] Ensure the generate\_agents.py script correctly adds the following Traefik labels to *each* agent service it generates:  
    * [x] traefik.enable=true  
    * [x] traefik.http.routers.agent-name.rule=Host(\\agent-name.local\`)\` (using the agent's name dynamically)  
    * [x] traefik.http.routers.agent-name.entrypoints=web  
    * [x] **FIXED**: traefik.http.services.agent-name.loadbalancer.server.port=8501 (was missing)
    * [x] **FIXED**: traefik.docker.network=ai\_agents\_network (was missing)
  * [x] Ensure the Mary2Ish Dockerfile exposes the correct port (e.g., EXPOSE 8501\) that Traefik will use for routing.  
  * [ ] Modify your local hosts file (e.g., /etc/hosts on Linux/macOS, C:\\Windows\\System32\\drivers\\etc\\hosts on Windows) to map 127.0.0.1 to the generated agent hostnames (e.g., mary.local, rick.local).  
  * [ ] Run generate\_agents.py with a list of agents, then docker-compose up \--build \-d.  
  * [ ] Attempt to access http://mary.local, http://rick.local, etc., in your browser. Verify that each URL correctly routes to its respective agent.  
  * [ ] **Self-Check:** Can all deployed agents be reached via their Traefik-defined hostnames? Is the routing correct for each?

### **Checkpoint 2.0: User Acceptance Testing (UAT) with User/PM**

* **Validation:** Demonstrate the complete network and proxy setup:  
  * Show that all agents and Traefik are on the dedicated ai\_agents\_network.  
  * Verify that the latest Traefik container is running.  
  * Prove that Traefik successfully routes requests to the correct agent based on dynamic hostnames, showing the Traefik dashboard confirming service discovery.  
* **User Acceptance:** Obtain explicit confirmation from the User/PM before proceeding to Phase 3\.

## **Phase 3: Traefik SSO Integration with Authentik**

**Objective:** Configure Traefik to act as a middleware for Single Sign-On (SSO) using Authentik as an example identity provider.

**Tasks for Jr SDEs:**

* [ ] **Task 3.1: Research Traefik & Authentik SSO Integration**  
  * [ ] Research Traefik's external authentication middleware capabilities.  
  * [ ] Research Authentik's setup for Traefik integration (e.g., ForwardAuth, OAuth2 Proxy).  
  * [ ] Identify the necessary Traefik configuration (labels, entrypoints, middleware definitions) and Authentik setup steps.  
  * [ ] **Self-Check:** Have you identified a clear path for integrating Authentik with Traefik using middleware?  
* [ ] **Task 3.2: Deploy Authentik (Local Example)**  
  * [ ] Add Authentik services (e.g., authentik, authentik-postgresql, authentik-redis) to a *separate* docker-compose.yml file (or integrate into the main one if complexity allows without hindering agent deployment).  
  * [ ] Configure Authentik for a basic local setup with a test user and application.  
  * [ ] **Self-Check:** Is Authentik running locally and can you log in as a test user?  
* [ ] **Task 3.3: Configure Traefik for SSO Middleware**  
  * [ ] Modify the traefik service in docker-compose.yml to include necessary middleware definitions for SSO (e.g., traefik.http.middlewares.auth-middleware.forwardauth.address=http://authentik\_container\_name:port/outpost.go).  
  * [ ] Ensure the authentik container is accessible from the traefik container (likely by placing it on the ai\_agents\_network or a shared network).  
  * [ ] **Self-Check:** Does Traefik start with the new middleware configuration without errors?  
* [ ] **Task 3.4: Apply SSO Middleware to an Agent**  
  * [ ] Update the generate\_agents.py script to optionally add the SSO middleware label to an agent service (e.g., traefik.http.routers.agent-name.middlewares=auth-middleware@docker).  
  * [ ] Deploy a test agent with this SSO middleware enabled.  
  * [ ] Attempt to access the agent via Traefik. Verify that you are redirected to Authentik for login and then successfully redirected back to the agent after authentication.  
  * [ ] **Self-Check:** Is the test agent protected by SSO, requiring Authentik login?

### **Checkpoint 3.0: User Acceptance Testing (UAT) with User/PM**

* **Validation:** Demonstrate that a selected agent is protected by SSO, requiring authentication via Authentik before access is granted. Show the successful authentication flow.  
* **User Acceptance:** Obtain explicit confirmation from the User/PM for the successful implementation of Traefik SSO with Authentik.

## **Future Considerations (No Tasks Assigned in this Document)**

* **Health Checks:** Implement Docker health checks for agent containers to ensure they are responsive.  
* **Logging:** Centralized logging solution (e.g., ELK stack, Grafana Loki) for all agent logs.  
* **Monitoring:** Integrate Prometheus/Grafana for monitoring agent performance and resource usage.  
* **Scalability:** Consider Kubernetes for more advanced orchestration if the number of agents grows significantly or requires more complex scaling.  
* **Security:** Implement HTTPS for Traefik, secure API keys/secrets for LLMs, and restrict network access.  
* **Agent Communication:** If agents need to communicate directly, define clear protocols and mechanisms (e.g., internal API endpoints, message queues).