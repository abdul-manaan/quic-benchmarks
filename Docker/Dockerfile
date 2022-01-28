FROM curlimages/curl:latest
FROM zenika/alpine-chrome:with-node
FROM python:3

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y  tshark vim
RUN pip3 install numpy

# Installing Proxygen with HTTP3 Support
RUN apt-get install --yes wget net-tools iputils-ping tcpdump ethtool iperf git sudo cmake python3 libssl-dev m4 zlib1g-dev gcc g++
RUN git clone https://github.com/facebook/proxygen.git
RUN cd proxygen && cd proxygen && ./build.sh --with-quic --no-tests && ./install.sh

# Installing NgTCP2
RUN git clone --depth 1 -b OpenSSL_1_1_1l+quic https://github.com/quictls/openssl
RUN cd openssl
RUN cd openssl && ./config enable-tls1_3 --prefix=$PWD/build
RUN cd openssl && make -j$(nproc)
RUN cd openssl && make install_sw
RUN git clone https://github.com/ngtcp2/nghttp3
RUN cd nghttp3 && autoreconf -i
RUN cd nghttp3 && ./configure --prefix=$PWD/build --enable-lib-only
RUN cd nghttp3 && make -j$(nproc) check
RUN cd nghttp3 && make install
RUN git clone https://github.com/ngtcp2/ngtcp2
RUN cd ngtcp2
RUN apt-get install -y libev-dev
RUN cd ngtcp2 && autoreconf -i
RUN cd ngtcp2 && ./configure PKG_CONFIG_PATH=$PWD/../openssl/build/lib/pkgconfig:$PWD/../nghttp3/build/lib/pkgconfig LDFLAGS="-Wl,-rpath,$PWD/../openssl/build/lib"
RUN cd ngtcp2 && make -j$(nproc) check

# Setting up Chrome
RUN apt-get install -y chromium npm


RUN mkdir /app
ADD --chown=1000:1000 . /app

WORKDIR /app
RUN cd chrome && npm install
ENV config="/app/config.json"
ENV log="test1"
CMD ["./run_benchmark.sh",${log}]