# Automated-Data-Pipeline-with-Pulumi-IaC
A scalable, infrastructure-as-code ETL pipeline that transforms HackerNews API data into actionable insights. This project demonstrates automated data engineering practices using AWS services orchestrated through Pulumi.

## Usage
Setting Up a New Stack
bashCopy# For development environment
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi config set project:environment dev
pulumi config set project:bucketPrefix data-pipeline
pulumi config set project:databaseName analytics_dev


# For production environment
pulumi stack init prod
pulumi config set aws:region us-east-1
pulumi config set project:environment prod
pulumi config set project:bucketPrefix data-pipeline

