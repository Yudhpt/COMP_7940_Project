# HKBU ChatGPT Telegram Bot

This is a Telegram chatbot project based on HKBU ChatGPT API, developed in Python, with Firebase database integration for data storage.

## Project Structure

```
.
├── codebase/
│   ├── chatbot_GPT.py      # Main program entry
│   ├── ChatGPT_HKBU.py     # ChatGPT API wrapper
│   ├── recommend.py        # Recommendation system implementation
│   └── utils.py           # Utility functions
├── Dockerfile             # Docker build file
├── docker-compose.yml     # Docker orchestration configuration
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Requirements

- Python 3.12
- Docker
- Docker Compose
- Azure account (for deployment)

## Local Setup Steps

1. Clone the project
```bash
git clone https://github.com/Yudhpt/COMP_7940_Project.git
cd COMP_7940_Project
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the project
```bash
python chatbot_GPT.py
```

## Docker Deployment

1. Build the image
```bash
docker build -t chatbot .
```

2. Run the container
```bash
docker-compose up -d
```

## Azure Deployment Guide

### 1. Prerequisites

1. Install Azure CLI
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

2. Login to Azure
```bash
az login
```

### 2. Create Azure Resources

1. Create a resource group
```bash
az group create --name <your_resource_group_name> --location eastasia
```

2. Create Azure Container Registry (ACR)
```bash
az acr create --resource-group <your_resource_group_name> --name <your_registry_name> --sku Basic
```

3. Login to ACR
```bash
az acr login --name <your_registry_name>
```

If on windows, use winget to install
'''bash
winget install --exact --id Microsoft.AzureCLI
'''

### 3. Build and Push Image

1. Build Docker image
```bash
docker-compose build
```

2. Tag the image
```bash
docker tag chatbot:latest <your_registry_name>.azurecr.io/chatbot:latest
```

3. Push image to ACR
```bash
docker push <your_registry_name>.azurecr.io/chatbot:latest
```

### 4. Create Azure Container Instance (ACI)

1. Create ACI
```bash
az container create \
  --resource-group <your_resource_group_name> \
  --name <your_container_name> \
  --image <your_registry_name>.azurecr.io/chatbot:latest \
  --dns-name-label <your_dns_label> \
  --ports 8080 \
  --registry_name <your_registry_id> \
  --password <your_registry_password>
```

### 5. Monitoring and Management

1. Check container status
```bash
az container show --resource-group <your_resource_group_name> --name <your_container_name>
```

2. View logs
```bash
az container logs --resource-group <your_resource_group_name> --name <your_container_name>
```

3. Restart container
```bash
az container restart --resource-group <your_resource_group_name> --name <your_container_name>
```

## Important Notes

1. Regularly check logs to ensure the application is running properly.
2. Consider using Azure Monitor for application performance monitoring.
3. For production environments, it's recommended to use Azure Kubernetes Service (AKS) instead of ACI for better scalability and management capabilities.

## Troubleshooting

If you encounter issues, check:
1. Network connectivity is working
2. Error messages in log files
3. Azure resource status and configuration

## Contributing

Pull requests are welcome. Please ensure:
1. Code follows PEP 8 standards
2. Appropriate tests are added
3. Documentation is updated

## License

This project is licensed under the MIT License. 