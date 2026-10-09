# Optional: run the agent headless (CLI) in a container. The GUI/.exe is Windows-only.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "-m", "code_agent.cli"]
