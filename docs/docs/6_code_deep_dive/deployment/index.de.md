# Swiss AI Hub Deployment Configurations

This directory contains the generated Docker Compose configurations for deploying the Swiss AI Hub platform in various
environments. The platform supports multiple deployment scenarios, each optimized for specific use cases ranging from
local development to production deployment.

Swiss AI Hub provides **5 deployment configurations**, each available in both **CPU** and **GPU** variants:

| Configuration | Use Case                | 1st Party Services | Traefik       | Port Exposure       |
| ------------- | ----------------------- | ------------------ | ------------- | ------------------- |
| **dev**       | Active development      | Not included       | None          | Direct to localhost |
| **local**     | Local testing with SSL  | Latest tagged      | Local SSL     | Through Traefik     |
| **build**     | Source code development | Built from source  | Local SSL     | Through Traefik     |
| **latest**    | Production deployment   | Latest tagged      | Let's Encrypt | Through Traefik     |
| **nightly**   | Pre-production testing  | Nightly tagged     | Let's Encrypt | Through Traefik     |

### Traefik Configuration

| Configuration | Traefik   | SSL Certificates     | Domain              |
| ------------- | --------- | -------------------- | ------------------- |
| dev           | ❌ None   | N/A                  | localhost           |
| local         | ✅ Local  | mkcert (self-signed) | \*.127.0.0.1.nip.io |
| build         | ✅ Local  | mkcert (self-signed) | \*.127.0.0.1.nip.io |
| latest        | ✅ Remote | Let's Encrypt        | Your domain         |
| nightly       | ✅ Remote | Let's Encrypt        | Your domain         |
