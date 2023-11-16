#!/usr/bin/env sh

# Add Docker's official GPG key:
apt-get update -y && apt-get upgrade -y && apt-get dist-upgrade -y
apt-get install ca-certificates curl gnupg -y
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Fix the docker feed bug for Ubuntu 23.10(mantic)
if [ "$(. /etc/os-release && echo "$VERSION_CODENAME")" = "mantic" ]; then
  codename="lunar"
else
  codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"
fi

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$codename" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y && apt-get upgrade -y && apt-get dist-upgrade -y

apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

apt-get install python3 python3-pip unzip -y

return
