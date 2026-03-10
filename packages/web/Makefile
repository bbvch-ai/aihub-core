pr-ready:
	cd aihub_web && pnpm lint

format:
	cd aihub_web && pnpm lint --fix

lint:
	cd aihub_web && pnpm lint

test:
	@echo "No frontend tests configured. See CLAUDE.md"

dev:
	cd aihub_web && pnpm dev

build:
	cd aihub_web && pnpm build

generate-sdk:
	cd aihub_web && pnpm generate-sdk

e2e:
	cd aihub_web && pnpm test:e2e

e2e-headed:
	cd aihub_web && pnpm test:e2e:headed

e2e-ui:
	cd aihub_web && pnpm test:e2e:ui

e2e-install:
	cd aihub_web && pnpm install && npx playwright install chromium