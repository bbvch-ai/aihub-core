pr-ready:
	cd swiss_ai_hub_web && pnpm lint

format:
	cd swiss_ai_hub_web && pnpm lint --fix

lint:
	cd swiss_ai_hub_web && pnpm lint

test:
	@echo "No frontend tests configured. See CLAUDE.md"

dev:
	cd swiss_ai_hub_web && pnpm dev

build:
	cd swiss_ai_hub_web && pnpm build

generate-sdk:
	cd swiss_ai_hub_web && pnpm generate-sdk

e2e:
	cd swiss_ai_hub_web && pnpm test:e2e

e2e-headed:
	cd swiss_ai_hub_web && pnpm test:e2e:headed

e2e-ui:
	cd swiss_ai_hub_web && pnpm test:e2e:ui

e2e-install:
	cd swiss_ai_hub_web && pnpm install && npx playwright install chromium