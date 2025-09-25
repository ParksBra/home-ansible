apt-get update -y
apt full-upgrade -y
cd {{ docker_compose_path }}
docker compose pull
docker compose up -d
sleep 10
shutdown -r now
