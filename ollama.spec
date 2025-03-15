## START: Set by rpmautospec
## (rpmautospec version 0.7.3)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 1;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

# Generated by go2rpm 1.14.0
%bcond check 1
%bcond cuda 1
%if 0%{?fedora} >= 42
%bcond rocm 1
%else
%bcond rocm 0
%endif

%define cuda_architectures 50;60;61;70;75;80;86;87;89;90;100;120

# https://github.com/ollama/ollama
%global goipath         github.com/ollama/ollama
%global forgeurl        https://github.com/ollama/ollama
Version:                0.5.9

%gometa -L -f

%global common_description %{expand:
Get up and running with Llama 3.2, Mistral, Gemma 2, and other large language
models.}

%global golicenses      LICENSE
%global godocs          docs examples CONTRIBUTING.md README.md SECURITY.md\\\
                        app-README.md integration-README.md llama-README.md\\\
                        llama-runner-README.md macapp-README.md

Name:           ollama
Release:        %autorelease
Summary:        Get up and running AI LLMs

License:        Apache-2.0 AND MIT
URL:            %{gourl}
Source:         %{gosource}
Source2:        ollama.service
Source3:        ollama-user.conf
Source4:        sysconfig.ollama

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

Requires:       hipblas
Requires:       rocblas
%endif

%if %{with cuda}
BuildRequires:  cuda-toolkit = 12.8.0
%if 0%{fedora} >= 42
BuildRequires:  gcc14-c++
%endif

Requires:       cuda-cudart-12-8
Requires:       libcublas-12-8
%endif

# Only tested on x86_64:
ExcludeArch:    ppc64le s390x aarch64

%description %{common_description}

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
mv llama/runner/README.md llama-runner-README.md
mv macapp/README.md macapp-README.md

# gcc 15 cstdint
sed -i '/#include <vector.*/a#include <cstdint>' llama/llama.cpp/src/llama-mmap.h

# install dir is off, lib -> lib64
sed -i -e 's@set(OLLAMA_INSTALL_DIR ${CMAKE_INSTALL_PREFIX}/lib/ollama)@set(OLLAMA_INSTALL_DIR ${CMAKE_INSTALL_PREFIX}/lib64/ollama)@' CMakeLists.txt


%generate_buildrequires
%go_generate_buildrequires

%build

# export GO111MODULE=off
# export GOPATH=$(pwd)/_build:%{gopath}

%if %{with cuda}

%if 0%{fedora} >= 42
    # update environment variables for CUDA, necessary when using cuda-gcc-c++
    export NVCC_PREPEND_FLAGS='-ccbin /usr/bin/g++-14'
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
%endif

%cmake_build

# cmake sets LDFLAGS env, this confuses gobuild
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

%pre
%sysusers_create_compat %{SOURCE3}

%post
%systemd_post ollama.service

%preun
%systemd_preun ollama.service

%postun
%systemd_postun_with_restart ollama.service

%files
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
%{_libdir}/ollama/libggml-cpu-sapphirerapids.so
%{_libdir}/ollama/libggml-cpu-skylakex.so

%dir %{_libdir}/ollama/bin
%{_libdir}/ollama/bin/ollama
%{_bindir}/ollama

%if %{with rocm}
%dir %{_libdir}/ollama/rocm
%{_libdir}/ollama/rocm/libggml-hip.so
%endif
%dir %{_libdir}/ollama/cuda_v12
%{_libdir}/ollama/cuda_v12/libggml-cuda.so
%if %{with cuda}

%endif

%changelog
* Sun Mar 16 2025 Fachep <mail@fachep.com> 0.5.10-1
- new package built with tito

## START: Generated by rpmautospec
* Wed Mar 12 2025 Tom Rix <Tom.Rix@amd.com> - 0.5.9-1
- Update to 5.9

* Thu Jan 30 2025 Tom Rix <Tom.Rix@amd.com> - 0.4.4-3
- Add more gpus

* Tue Jan 21 2025 Tom Rix <Tom.Rix@amd.com> - 0.4.4-2
- Use ExcludeArch instead of ExclusiveArch

* Tue Jan 21 2025 Tom Rix <Tom.Rix@amd.com> - 0.4.4-1
- Initial package
## END: Generated by rpmautospec
