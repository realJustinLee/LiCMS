# Invoke app via Docker Compose
echo 'Initializing Docker Compose'
docker compose build --no-cache
docker compose down
docker compose pull
docker compose up -d >> docker-licms.log

echo 'Auto cleaning...'
docker system prune -a

echo 'You are all done! Enjoy!'
