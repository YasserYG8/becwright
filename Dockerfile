FROM python:3.12-slim

# Install git since becwright shells out to git commands
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Install becwright from PyPI
RUN pip install --no-cache-dir becwright

# Set entrypoint to run becwright automatically
ENTRYPOINT ["becwright"]
