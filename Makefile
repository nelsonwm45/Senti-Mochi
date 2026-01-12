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
	@echo "Cleaning up all Docker resources..."
	docker system prune -af --volumes

# Kill any lingering processes on application ports
kill-zombies:
	@echo "Killing processes on ports 3000, 8000, 5432, 6379, 9000-9001..."
	-sudo kill -9 $$(sudo lsof -t -i:3000 -i:8000 -i:5432 -i:6379 -i:9000 -i:9001) 2>/dev/null || true
	@echo "Done."

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
