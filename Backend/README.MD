Folder Structure for Backend:
```
Backend/
└── app/
    ├── api/        #fastapi routers
    ├── core/       #cross cutting concerns that all modules require handled here (config.py, security.py etc...)
    ├── database/   #everything for the PostgreSQL + Redis caching
    ├── ml/         #Machine Learning
    ├── models/     #ORM model classes handled here
    ├── search/     #OpenSearch interaction
    ├── tasks/      #celery for ML jobs
    ├── tests/      #pyTest suite
    ├── storage/    #AWS S3 storage
    ├── services/   #business logic
    ├── auth/       #authorization logic here
    ├── DockerFile
    ├── README.MD
    └── .dockerignore
```
