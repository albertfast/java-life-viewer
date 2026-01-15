# Java Game of Life Viewer

Simple split-screen web application displaying Conway's Game of Life simulation alongside a Trefoil Knot animation.

## Features

- **Left Panel**: Live Java Game of Life terminal output with custom cell types:
  - `O` - Conway cells (standard rules)
  - `A` - Alternating cells (toggle every generation)
  - `R` - Random cells (50% chance to be alive each generation)
  - `X` - Always alive cells
  - `+` - Never alive cells

- **Right Panel**: Animated Trefoil Knot GIF (CC BY-SA 4.0, Raphaelaugusto via Wikimedia Commons)

## Local Development

```bash
docker-compose up --build
```

Open in browser: **http://localhost:8000**

## Deploy to Render

1. Push this repository to GitHub
2. Go to [Render.com](https://render.com) and sign up/login
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and deploy

**Free tier included!** App will sleep after 15 min of inactivity.

## Tech Stack

- **Backend**: FastAPI + WebSocket (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Simulation**: Java (compiled in Docker)
- **Deployment**: Docker container

## License

Code: MIT  
Trefoil Knot GIF: CC BY-SA 4.0 (Raphaelaugusto)

# Here is my project github source
https://github.com/albertfast/java-life-viewer.git
