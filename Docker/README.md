# How to setup docker?

docker run --privileged --net="host" -v <path-to-config>/config.json:/app/config.json -v <path-to-result-folder>:/app/data -it quic_benchmarking_tool /bin/sh ./run_benchmark.sh <some-test-name>

