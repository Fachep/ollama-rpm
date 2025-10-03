ARG REPO_PATH
ARG SPEC_FILE
ARG OUTPUT
ARG GO_VENDOR_CONFIG=go-vendor-tools.toml

FROM fedora:latest AS builder
ARG REPO_PATH
ARG SPEC_FILE
ARG GO_VENDOR_CONFIG
ARG OUTPUT
WORKDIR /build
RUN dnf install -y rpm-build rpkg go-vendor-tools golang python3-specfile && dnf clean all
COPY . .
RUN rpkg sources --repo-path ${REPO_PATH} && \
    rpmspec -q --qf "VERSION=%{version}" --srpm ${SPEC_FILE} > /VERSION && \
    go_vendor_archive create --config ${GO_VENDOR_CONFIG} ${SPEC_FILE} && \
    mv $(echo -e "import specfile\nprint(specfile.Specfile('${SPEC_FILE}').sources().content[1].expanded_filename)" | python3) /${OUTPUT}

FROM scratch
ARG OUTPUT
COPY --from=builder /${OUTPUT} /VERSION /
