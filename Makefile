generate:
ifdef message
	alembic revision --autogenerate -m "$(message)"
else
	@read -p "Enter migration message: " msg && alembic revision --autogenerate -m "$$msg"
endif

migrate:
	alembic upgrade head

rollback:
	alembic downgrade -1
