# Azure deployment boundary

`main.bicep` declares a private TLS-protected storage foundation only. It does **not** deploy the training, lakehouse, or image-inference workflow. Validate with the Azure Bicep CLI and security review before deployment. Azure resources can incur charges.
