# UI Configuration Guide

This document explains how to customize the user interface of Mary 2.0ish using the UI configuration file.

## Overview

The UI configuration is stored in `ui.config.yaml` in the root directory of the project. This file allows you to customize various aspects of the chat interface without modifying the application code.

## Configuration File Structure

```yaml
# UI Configuration File for Mary 2.0ish Chat Application

# Page Configuration
page:
  # Title that appears in the browser tab
  title: "Mary"
  
  # Main header displayed at the top of the chat interface
  header: "Mary"
  
  # Icon displayed in the browser tab (emoji or path to icon file)
  icon: "🤖"

# Chat Interface Configuration
chat:
  # Display name for the AI assistant in chat messages
  agent_display_name: "Mary"
  
  # Display name for the user in chat messages
  user_display_name: "You"
  
  # Placeholder text for the chat input box
  input_placeholder: "Type your message here..."

# Branding (Optional)
branding:
  # Footer text or caption (if enabled)
  footer_caption: ""
  
  # Whether to show "Powered by fast-agent.ai" caption
  show_powered_by: false

# Styling (Optional - for future expansion)
styling:
  # Primary theme color (for future use)
  primary_color: "#1f77b4"
  
  # Background color (for future use)  
  background_color: "#ffffff"
```

## Customization Examples

### Example 1: Corporate Branding
```yaml
page:
  title: "CompanyBot Assistant"
  header: "CompanyBot"
  icon: "🏢"

chat:
  agent_display_name: "CompanyBot"
  user_display_name: "Employee"
  input_placeholder: "How can I help you today?"

branding:
  footer_caption: "© 2025 Company Name - Internal Use Only"
  show_powered_by: false
```

### Example 2: Customer Support
```yaml
page:
  title: "Customer Support"
  header: "Customer Support Assistant"
  icon: "🎧"

chat:
  agent_display_name: "Support Agent"
  user_display_name: "Customer"
  input_placeholder: "Describe your issue or question..."

branding:
  footer_caption: "For urgent issues, call 1-800-SUPPORT"
  show_powered_by: false
```

### Example 3: Educational Assistant
```yaml
page:
  title: "Learning Assistant"
  header: "EduBot - Your Learning Companion"
  icon: "📚"

chat:
  agent_display_name: "EduBot"
  user_display_name: "Student"
  input_placeholder: "Ask me anything about your studies..."

branding:
  footer_caption: "Remember: Learning is a journey, not a destination!"
  show_powered_by: true
```

## Visual Styling Features

The current implementation includes enhanced visual styling that provides:

### Speaker Name Styling
- **Font**: Segoe UI with fallbacks
- **Style**: Bold, uppercase, with letter spacing
- **Color**: Blue for users (#1565c0), Green for assistants (#2e7d32)
- **Separator**: Underline border to separate from message content

### Message Content Styling
- **Font**: Modern system fonts (-apple-system, BlinkMacSystemFont, etc.)
- **Style**: Regular weight, increased line height for readability
- **Color**: Dark gray (#1a1a1a) for good contrast
- **Spacing**: Proper margins and padding for visual separation

### Message Containers
- **User messages**: Light blue background with left margin and blue border
- **Assistant messages**: Light gray background with right margin and green border
- **Padding**: Generous padding for comfortable reading
- **Borders**: Rounded corners for modern appearance

## Configuration Loading

The application loads the UI configuration at startup with simplified direct file loading:

1. **File exists**: Loads configuration from `ui.config.yaml` in the current directory
2. **File missing**: Uses built-in defaults with basic Mary branding
3. **Partial configuration**: Missing sections fall back to sensible defaults
4. **Invalid YAML**: Application reports error and uses defaults

### Configuration File Locations

The UI configuration is loaded from `ui.config.yaml` in the application's working directory.

**For Docker deployments:**
- Example configs are included in the container at build time
- Real configs are mounted from the `config/` directory at runtime via docker-compose
- This allows customization without rebuilding the container

**For local development:**
- Place `ui.config.yaml` in the project root directory
- The file is loaded directly using Python's YAML parser

## Hot Reloading

Changes to `ui.config.yaml` require restarting the Streamlit application:

```bash
# Stop the current application (Ctrl+C)
# Then restart
uv run streamlit run app/main.py
```

## Troubleshooting

### Configuration Not Applied

- Check that `ui.config.yaml` is in the current working directory
- Verify YAML syntax is correct (use a YAML validator)  
- Restart the Streamlit application
- Check application logs for any configuration loading errors

### YAML Syntax Errors

- Ensure proper indentation (use spaces, not tabs)
- Quote string values containing special characters
- Use proper YAML list and dictionary syntax

### File Location

The configuration file should be in the working directory when the application starts:

```text
Mary2ish/
├── ui.config.yaml          # ← UI configuration file
├── fastagent.config.yaml   # ← FastAgent configuration  
├── app/
│   └── main.py
└── ...
```

## Future Enhancements

The styling section in the configuration file is prepared for future enhancements:

- Custom color themes
- Font family selection
- Message bubble styling
- Dark/light mode toggle
- Custom CSS injection

These features can be added as needed without breaking existing configurations.
