#!/usr/bin/env bash
tail -f pipe | nc $1 $2 | tee outgoing.log | nc 127.0.0.1 23 | tee pipe
