FROM kalilinux/kali-last-release:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        nikto \
        sqlmap \
        gobuster \
        ffuf \
        hydra \
        whois \
        curl \
        wget \
        dnsutils \
        nmap \
        python3 \
        python3-pip \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work