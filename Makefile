.PHONY: up down stop dev build logs clean restart prune prune-all clean-db reset-db help

help:
	@echo "Available commands:"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make stop        - Stop services (keep containers)"
	@echo "  make build       - Build all images"
	@echo "  make dev         - Build and run with file watching"
	@echo "  make logs        - Show logs"
	@echo "  make clean       - Stop and remove containers"
	@echo "  make restart     - Restart all services"
	@echo "  make prune       - Remove dangling images"
	@echo "  make prune-all   - Remove all unused Docker resources"
	@echo "  make clean-db    - Remove database volumes with confirmation"
	@echo "  make reset-db    - Full reset (stop, remove volumes, restart)"

# Run the application in detached mode
up:
	docker compose up -d

# Stop the application
down:
	docker compose down --remove-orphans

# Stop the services only (without removing containers)
stop:
	docker compose stop

# Build the images
build: prune
	docker compose build

# Remove dangling images
prune:
	docker image prune -f

# Remove all unused Docker resources
prune-all:
	@docker system prune -af --volumes

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
	docker compose up -d
	docker compose watch

# Remove database volumes only (with confirmation)
clean-db:
	@echo "⚠️  WARNING: This will delete all database data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down; \
		docker volume rm mochi_postgres_data mochi_minio_data || true; \
		echo "✅ Database volumes removed"; \
	else \
		echo "❌ Cancelled"; \
	fi

# Full database reset (stop, remove volumes, restart)
reset-db:
	@echo "🔄 Resetting database and restarting services..."
	docker compose down -v
	docker compose up -d
	@echo "✅ Database reset complete! Fresh start ready."
