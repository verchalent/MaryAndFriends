# Branch Configuration Documentation

## Branch Structure

### `main` Branch - Direct Port Exposure
The main branch now uses **direct port exposure** instead of Traefik reverse proxy.

**Configuration:**
- **Mary agent**: http://localhost:8004
- **Rick agent**: http://localhost:8005  
- **Future agents**: Start at port 8006, 8007, etc.

**Features:**
- Simple direct access to agents via localhost ports
- No reverse proxy complexity
- Easy testing and development
- Automatic port assignment for new agents

### `traefik-testing` Branch - Traefik Reverse Proxy
The traefik-testing branch contains the **Traefik reverse proxy configuration**.

**Configuration:**
- **Traefik dashboard**: http://localhost:8080
- **Mary agent**: http://mary.local (via Traefik)
- **Rick agent**: http://rick.local (via Traefik)
- **Future agents**: http://{agent-name}.local

**Features:**
- Single entry point for all agents
- Host-based routing
- Scalable for production
- Requires hosts file configuration

## Key Differences

| Feature | Main Branch | Traefik Branch |
|---------|-------------|----------------|
| **Access Method** | Direct ports | Host-based routing |
| **Mary Agent** | http://localhost:8004 | http://mary.local |
| **Rick Agent** | http://localhost:8005 | http://rick.local |
| **Setup Complexity** | Simple | Requires hosts file |
| **Production Ready** | Development/Testing | Production |
| **Port Management** | Auto-assigned | Single port (80) |

## Testing Both Configurations

### Testing Main Branch (Current)
```bash
# Ensure you're on main branch
git checkout main

# Start services
docker-compose up --build -d

# Test agents
curl http://localhost:8004   # Mary
curl http://localhost:8005   # Rick
```

### Testing Traefik Branch
```bash
# Switch to traefik branch
git checkout traefik-testing

# Add hosts entries (Linux/macOS)
sudo echo "127.0.0.1 mary.local" >> /etc/hosts
sudo echo "127.0.0.1 rick.local" >> /etc/hosts

# Start services
docker-compose up --build -d

# Test agents
curl http://mary.local       # Mary via Traefik
curl http://rick.local       # Rick via Traefik
curl http://localhost:8080   # Traefik dashboard
```

## Agent Generation Scripts

Both branches use the same `generate_agents.py` script, but with different behaviors:

### Main Branch
```bash
# Generate new agents with direct ports
uv run generate_agents.py alice bob charlie

# Results:
# - alice: http://localhost:8006
# - bob: http://localhost:8007  
# - charlie: http://localhost:8008
```

### Traefik Branch
```bash
# Generate new agents with Traefik routing
uv run generate_agents.py alice bob charlie

# Results:
# - alice: http://alice.local
# - bob: http://bob.local
# - charlie: http://charlie.local
```

## Docker Compose Differences

### Main Branch docker-compose.yml
```yaml
services:
  mary:
    build: ./Mary2ish
    ports:
      - "8004:8501"  # Direct port exposure
    networks:
      - ai_agents_network
    # No Traefik labels
```

### Traefik Branch docker-compose.yml  
```yaml
services:
  mary:
    build: ./Mary2ish
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mary.rule=Host(`mary.local`)"
      - "traefik.http.services.mary.loadbalancer.server.port=8501"
    networks:
      - ai_agents_network
    # No direct port exposure
    
  traefik:
    image: traefik:v3
    ports:
      - "80:80"
      - "8080:8080"
```

## When to Use Each Branch

### Use Main Branch When:
- **Development and testing**
- **Simple local deployment**  
- **Quick agent access**
- **No need for reverse proxy features**

### Use Traefik Branch When:
- **Production deployment**
- **Multiple agents with clean URLs**
- **Need load balancing or SSL termination**
- **Professional deployment setup**

## Switching Between Branches

### Save Current Work
```bash
# Commit any changes
git add -A
git commit -m "Save current changes"
```

### Switch to Main Branch
```bash
git checkout main
docker-compose down  # Stop current services
docker-compose up --build -d  # Start with direct ports
```

### Switch to Traefik Branch
```bash
git checkout traefik-testing
docker-compose down  # Stop current services
docker-compose up --build -d  # Start with Traefik
```

## Port Assignments (Main Branch)

| Agent | Port | URL |
|-------|------|-----|
| mary | 8004 | http://localhost:8004 |
| rick | 8005 | http://localhost:8005 |
| Next agent | 8006 | http://localhost:8006 |
| Next agent | 8007 | http://localhost:8007 |
| ... | ... | ... |

The `generate_agents.py` script automatically calculates the next available port starting from 8004.
