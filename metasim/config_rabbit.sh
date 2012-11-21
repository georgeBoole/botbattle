#!/usr/bin/bash

rabbitmq-server

rabbitmqctl add_user michael password
rabbitmqctl add_vhost myvhost
rabbitmqctl set_permissions -p myvhost michael "" ".*" ".*"


