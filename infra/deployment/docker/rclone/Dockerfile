# rclone with a current CA bundle.
#
# Upstream rclone images bake in Alpine's ca-certificates at release time, and every release up to 1.75.2 was built
# before the eMudhra intermediate CA compromise (2026-10), so they still trust emSign ECC Root CA - G3. rclone talks TLS
# to the SharePoint, OneDrive and S3 sources, so the bundle is refreshed from Alpine here. Drop this image once an
# upstream release ships a bundle without that root.
#
# Re-publish via `make -C infra/deployment build-and-push-rclone-image` after editing this file, then bump
# image_tags.rclone in compose-config.yml.
FROM rclone/rclone:1.71.2

RUN apk upgrade --no-cache ca-certificates ca-certificates-bundle
