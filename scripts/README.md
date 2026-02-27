# Scripts

This folder contains a docket compose file which starts:
* Confluent Kafka (localhost:9092)
* ksqldb (http://localhost:8088)
* ksqldb-cli

## Services

To start the stack.

```bash
docker-compose up
```

Hitting ^C will stop the services, but leave the state intact.

To destroy the state.


```bash
docker-compose up
```

## CLI

To use the command line client.

```bash
docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
```
