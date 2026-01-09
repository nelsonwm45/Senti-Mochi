.PHONY: up down build logs clean restart prune

# Run the application in detached mode
up:
	docker compose up -d

# Stop the application
down:
	docker compose down

# Build the images
build: prune
	docker compose build

# Remove dangling images
prune:
	docker image prune -f

# View logs
logs:
	docker compose logs -f

# Clean up volumes and orphans
clean:
	docker compose down -v --remove-orphans

# Restart the application
restart: down up
