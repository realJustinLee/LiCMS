#!/usr/bin/env sh

apt-get update -y && apt-get upgrade -y && apt-get dist-upgrade -y

apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y && apt-get upgrade -y && apt-get dist-upgrade -y

apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

apt-get install python3 python3-pip unzip -y

return
