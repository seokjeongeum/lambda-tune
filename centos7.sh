#!/bin/bash
# This script automates updating the Docker repository configuration and switching the Docker storage driver to overlay2

# Backup existing Docker repository configuration
echo "Backing up /etc/yum.repos.d/docker-ce.repo to /etc/yum.repos.d/docker-ce.repo.bak"
sudo cp /etc/yum.repos.d/docker-ce.repo /etc/yum.repos.d/docker-ce.repo.bak

# Update Docker repository configuration to use CentOS 7 (replace $releasever with 7)
echo "Updating Docker repository configuration..."
sudo sed -i 's|\$releasever|7|g' /etc/yum.repos.d/docker-ce.repo

# Clear YUM cache and rebuild cache
echo "Cleaning YUM cache and updating cache..."
sudo yum clean all
sudo yum makecache fast

# Update Docker storage driver to overlay2
echo "Setting Docker storage driver to overlay2..."
if [ ! -f /etc/docker/daemon.json ]; then
    echo '{"storage-driver": "overlay2"}' | sudo tee /etc/docker/daemon.json > /dev/null
else
    sudo sed -i 's|"storage-driver":.*|"storage-driver": "overlay2"|' /etc/docker/daemon.json
fi

# Restart Docker service
echo "Reloading systemd configuration and restarting Docker service..."
sudo systemctl daemon-reload
sudo systemctl restart docker

# Verify Docker storage driver configuration
echo "Verifying Docker storage driver ..."
sudo docker info | grep "Storage Driver"
