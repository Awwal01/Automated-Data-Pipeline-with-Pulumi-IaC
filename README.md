# Automated-Data-Pipeline-with-Pulumi-IaC
A scalable, infrastructure-as-code ETL pipeline that transforms HackerNews API data into actionable insights. This project demonstrates automated data engineering practices using AWS services orchestrated through Pulumi.

## Architecture Diagram
![etl-automated Pipeline Diagram](https://github.com/user-attachments/assets/5a234ab5-14bb-4cfa-9af1-924a8df66eac)

## Architecture Components
Orchestration: AWS Step Functions
ETL Processing: AWS Glue
Data Storage:
Raw Data: Amazon S3
Processed Data: Amazon Aurora PostgreSQL

Infrastructure: Pulumi
Data Source: HackerNews API

## Project Structure
│
├── .github/              # GitHub Actions workflows<br>
├── lambda-code/          # Lambda function source code<br>
├── resources/            # Pulumi resource definitions<br>
├── tests/                # Unit and integration tests<br>
├── requirements.txt      # Python dependencies<br>
├── Pulumi.yaml           # Pulumi project configuration<br>
├── Pulumi.dev.yaml       # Development stack configuration<br>
└── Pulumi.prod.yaml      # Production stack configuration<br>

## Usage
Setting Up a pulumi project
```{bash}
pulumi new aws-python
```
leave other settings as default, we used us-west-2 as region
bashCopy
### For development environment
```{bash}
pulumi config set bucketName hackernews-data-dev --stack dev
pulumi config set --secret dbPassword your-db-password --stack dev
pulumi config set --secret dbUsername postgres --stack dev 
pulumi config set databaseName hackernews --stack dev
pulumi config set vpcCidr 10.0.0.0/16 --stack dev
pulumi config set environment dev --stack dev
pulumi config set projectName hackernews-data-pipeline
```

### For production environment
replace postgres and your-db-password below respecitively with your databaseUsername and password
```{bash}
pulumi stack init prod
pulumi config set aws:region us-west-2 --stack prod
pulumi config set project:environment prod  --stack prod
pulumi config set bucketName hackernews-data-prod  --stack prod
pulumi config set --secret dbPassword your-db-password --stack prod
pulumi config set --secret dbUsername postgres --stack prod 
pulumi config set databaseName hackernews --stack prod
pulumi config set vpcCidr 10.0.0.0/16 --stack prod
pulumi config set projectName hackernews-data-pipeline --stack prod
```

clone the repository into your project folder
```{bash}
git clone git@github.com:Awwal01/Automated-Data-Pipeline-with-Pulumi-IaC.git
```
copy contents of the repo into your project folder
```{bash}
cp -r Automated-Data-Pipeline-with-Pulumi-IaC/* ./
```
preview necessary changes and spin your infrasture
```{bash}
pulumi preview
pulumi up
```

### To Clean Up
```{bash}
pulumi destroy
```
