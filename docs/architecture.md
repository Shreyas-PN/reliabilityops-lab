# Architecture

- API receives requests and publishes/reads operational data.
- Worker consumes queue messages from RabbitMQ.
- Remediator receives webhook events to simulate automated action.
- Postgres/Redis/RabbitMQ act as platform dependencies.
