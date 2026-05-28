pr-ready:
	pnpm lint

format:
	pnpm lint --fix

lint:
	pnpm lint

test:
	@echo "No frontend tests configured. See CLAUDE.md"

dev:
	pnpm dev

build:
	pnpm build

generate-sdk:
	pnpm generate-sdk

e2e:
	pnpm test:e2e

e2e-headed:
	pnpm test:e2e:headed

e2e-ui:
	pnpm test:e2e:ui

e2e-install:
	pnpm install && npx playwright install chromium
