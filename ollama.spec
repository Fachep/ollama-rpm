## Original file from https://src.fedoraproject.org/rpms/ollama

%bcond cuda 1

%if 0%{?fedora} >= 42
%bcond check 1
%bcond rocm 1
%else
%bcond check 0
%bcond rocm 0
%global goversion 1.24.1
%global __requires_exclude %{?__requires_exclude:%{__requires_exclude}|}^golang\\(.*\\)$
%global go_generate_buildrequires echo
%global gomodulesmode GO111MODULE=on
%endif

%global cuda_architectures 50;60;61;70;75;80;86;87;89;90;100;120

# https://github.com/ollama/ollama
%global goipath         github.com/ollama/ollama
%global forgeurl        https://github.com/ollama/ollama
Version:                0.6.1

%gometa -L -f

%global common_description %{expand:
Get up and running with Llama 3.3, DeepSeek-R1, Phi-4, Gemma 3, and other large
language models.}

%global golicenses      LICENSE
%global godocs          docs examples CONTRIBUTING.md README.md SECURITY.md\\\
                        app-README.md integration-README.md llama-README.md\\\
                        llama-runner-README.md macapp-README.md

Name:           ollama
Release:        1%{?dist}
Summary:        Meta-package containing Ollama and all backends.

License:        Apache-2.0 AND MIT
URL:            %{gourl}
Source:         %{gosource}
Source2:        ollama.service
Source3:        ollama-user.conf
Source4:        sysconfig.ollama
Source5:        ollama-discover-path.go

%if %{defined goversion}
BuildRequires:  curl
%endif

BuildRequires:  fdupes
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  systemd-rpm-macros
%{?sysusers_requires_compat}

%if %{with rocm}
BuildRequires:  hipblas-devel
BuildRequires:  rocblas-devel
BuildRequires:  rocm-comgr-devel
BuildRequires:  rocm-compilersupport-macros
BuildRequires:  rocm-runtime-devel
BuildRequires:  rocm-hip-devel
BuildRequires:  rocm-rpm-macros
BuildRequires:  rocminfo

Requires:       ollama-rocm = %{version}-%{release}
%endif

%if %{with cuda}
BuildRequires:  cuda-toolkit = 12.8.0
%if 0%{?fedora} >= 42
BuildRequires:  gcc14-c++

Requires:       ollama-cuda = %{version}-%{release}
%endif

Requires:       ollama-cpu = %{version}-%{release}

%endif

# Only tested on x86_64:
ExcludeArch:    ppc64le s390x aarch64

%description
This meta package will install Ollama version %{version} and all backends.

%gopkg

%prep
%goprep -A

# Remove some .git cruft
for f in `find . -name '.gitignore'`; do
    rm $f
done

# Rename README's
mv app/README.md app-README.md
mv integration/README.md integration-README.md
mv llama/README.md llama-README.md
mv runner/README.md llama-runner-README.md
mv macapp/README.md macapp-README.md

# install dir is off, lib -> lib64
sed -i -e 's@set(OLLAMA_INSTALL_DIR ${CMAKE_INSTALL_PREFIX}/lib/ollama)@set(OLLAMA_INSTALL_DIR ${CMAKE_INSTALL_PREFIX}/lib64/ollama)@' CMakeLists.txt

# Fix path for discovering ggml backends
cp %{SOURCE5} discover/path.go -f
sed -i -e 's@"lib/ollama"@"lib64/ollama"@' ml/backend/ggml/ggml/src/ggml.go

%generate_buildrequires
%go_generate_buildrequires

%build

# export GO111MODULE=off
# export GOPATH=$(pwd)/_build:%{gopath}

%if %{with cuda}

%if 0%{?fedora} >= 42
    # update environment variables for CUDA, necessary when using cuda-gcc-c++
    export CC=gcc-14
    export CXX=g++-14
%endif

%endif

%cmake \
%if %{with rocm}
    -DCMAKE_HIP_COMPILER=%rocmllvm_bindir/clang++ \
    -DAMDGPU_TARGETS=%{rocm_gpu_list_default} \
%endif
%if %{with cuda}
    -DCMAKE_CUDA_FLAGS="-Xcompiler -fPIC" \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc \
    -DCMAKE_CUDA_ARCHITECTURES="%{cuda_architectures}" \
%if 0%{?fedora} >= 42
    -DCMAKE_CUDA_HOST_COMPILER=g++-14 \
%endif
%endif

%cmake_build

%if %{defined goversion}

%ifarch x86_64
%define goarch amd64
%else
%define goarch aarch64
%endif

export PATH=%{_builddir}/go/bin:$PATH GOROOT=%{_builddir}/go
curl -fsSL https://golang.org/dl/go%{goversion}.linux-%{goarch}.tar.gz | tar xz -C %{_builddir}

%endif

export LDFLAGS=

%gobuild -o %{gobuilddir}/bin/ollama %{goipath}

%install
%cmake_install

install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/ollama.service
install -d -m 0755 %{buildroot}%{_sysusersdir}
install -m 0644 %{SOURCE3} %{buildroot}%{_sysusersdir}/ollama.conf
mkdir -p %{buildroot}%{_sharedstatedir}/ollama
install -d -m 0755 %{buildroot}%{_sysconfdir}/sysconfig
install -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/ollama

# remove copies of system libraries
runtime_removal="hipblas rocblas amdhip64 rocsolver amd_comgr hsa-runtime64 rocsparse tinfo rocprofiler-register drm drm_amdgpu numa elf"
for rr in $runtime_removal; do
    rm -rf %{buildroot}%{_libdir}/ollama/rocm/lib${rr}*
done
rm -rf %{buildroot}%{_libdir}/ollama/cuda_v12/libcu*
rm -rf %{buildroot}%{_libdir}/ollama/rocm/rocblas

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}/ollama/bin
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_libdir}/ollama/bin/

pushd .
cd %{buildroot}%{_bindir}
ln -s ../%{_lib}/ollama/bin/ollama ollama
popd

#Clean up dupes:
%fdupes %{buildroot}%{_prefix}

%if %{with check}
%check
%gocheck
%endif

%files

%package cpu
Summary:       Get up and running AI LLMs
%description cpu %{common_description}

%pre cpu
%sysusers_create_compat %{SOURCE3}

%post cpu
%systemd_post ollama.service

%preun cpu
%systemd_preun ollama.service

%postun cpu
%systemd_postun_with_restart ollama.service

%files cpu
%license LICENSE
%doc CONTRIBUTING.md SECURITY.md README.md app-README.md integration-README.md
%doc llama-README.md llama-runner-README.md macapp-README.md

%{_unitdir}/ollama.service
%{_sysusersdir}/ollama.conf
%config(noreplace) %{_sysconfdir}/sysconfig/ollama
%attr(-,ollama,ollama) %dir %{_sharedstatedir}/ollama

%dir %{_libdir}/ollama
%{_libdir}/ollama/libggml-base.so
%{_libdir}/ollama/libggml-cpu-alderlake.so
%{_libdir}/ollama/libggml-cpu-haswell.so
%{_libdir}/ollama/libggml-cpu-icelake.so
%{_libdir}/ollama/libggml-cpu-sandybridge.so
%{_libdir}/ollama/libggml-cpu-skylakex.so

%dir %{_libdir}/ollama/bin
%{_libdir}/ollama/bin/ollama
%{_bindir}/ollama

%if %{with rocm}

%package rocm
Summary:       ROCm backend for Ollama
%description rocm
This package contains the ROCm backend for Ollama.
Supported GPUs: %{rocm_gpu_list_default}

Requires:       hipblas
Requires:       rocblas
Requires:       ollama-cpu = %{version}-%{release}

%files rocm
%dir %{_libdir}/ollama/rocm
%{_libdir}/ollama/rocm/libggml-hip.so

%endif

%if %{with cuda}

%package cuda
Summary:       CUDA backend for Ollama
%description cuda
This package contains the CUDA v12.8 backend for Ollama.
Supported Architectures: %{cuda_architectures}

Requires:       cuda-cudart-12-8
Requires:       libcublas-12-8
Requires:       ollama-cpu = %{version}-%{release}

%files cuda
%dir %{_libdir}/ollama/cuda_v12
%{_libdir}/ollama/cuda_v12/libggml-cuda.so

%endif

%changelog
* Sun Mar 16 2025 Fachep <mail@fachep.com> - 0.6.1-1
 - Bump to v0.6.1

* Sat Mar 15 2025 Fachep <mail@fachep.com> - 0.5.12-1
 - Bump to v0.5.12

* Sat Mar 15 2025 Fachep <mail@fachep.com> - 0.5.9-1
 - First import v0.5.9