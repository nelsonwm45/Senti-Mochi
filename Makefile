.PHONY: up down build logs clean restart

# Run the application in detached mode
up:
	docker compose up -d

# Stop the application
down:
	docker compose down

# Build the images
build:
	docker compose build

# View logs
logs:
	docker compose logs -f

# Clean up volumes and orphans
clean:
	docker compose down -v --remove-orphans

# Restart the application
restart: down up
