FROM ubuntu:20.04

# Set environment variables so that the locale is used system-wide
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PGPASSWORD=your_new_password \
    DEBIAN_FRONTEND=noninteractive

# Create a non-root user and grant sudo permissions
RUN apt-get update && apt-get install -y sudo python3.9-venv git && \
    useradd -m -s /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set the default user to the new non-root user
USER vscode

# Keep the container running by tailing /dev/null indefinitely.
CMD ["tail", "-f", "/dev/null"]
