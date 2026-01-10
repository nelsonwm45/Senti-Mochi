.PHONY: up down stop dev build logs clean restart prune

# Run the application in detached mode
up:
	docker compose up -d

# Stop the application
down:
	docker compose down

# Stop the services only (without removing containers)
stop:
	docker compose stop

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

# Run in development mode with file watching
dev: build
	docker compose watch
