# CEREBRO FORGE PREPROD deployment notes

The GitHub Workload Identity provider is scoped to repository `carlosjmunoz78/capital-mapa-pro` and branch `cerebro-engine-factory-v0`.

The deployment workflow verifies the configured project ID and both dedicated service accounts after successful WIF authentication. It intentionally does not call `gcloud projects describe`, because that read requires the Cloud Resource Manager API, which is not needed for the PREPROD runtime itself and is not enabled in the zero-cost bootstrap.
