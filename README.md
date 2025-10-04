# ollama-rpm
| Package          |          Build Status (Package Page)           | Repo Link           |
| ---------------- | :--------------------------------------------: | ------------------- |
| ollama           | [![Copr build status][main-status]][main-copr] | [Pagure][main-repo] |
| ollama-ggml-cuda | [![Copr build status][cuda-status]][cuda-copr] | [GitHub][cuda-repo] |

Packaging Ollama for Fedora, via COPR.

## Usage
See [here](https://developer.nvidia.com/cuda-downloads) for CUDA installation.

```shell
dnf copr enable fachep/ollama
# Optional
dnf config-manager setopt copr:copr.fedorainfracloud.org:fachep:ollama.priority=90

dnf install ollama
systemctl enable --now ollama

# Configuration
cat /etc/sysconfig/ollama

# Models
ls /var/lib/ollama/.ollama/models
```

## Supported Platform
x86_64 is supported. Aarch64 (arm64-sbsa) is supposed to work, but not tested.
|         |  CPU  | CUDA 12 | CUDA 13 | ROCm 6 | ROCm 7 |
| ------: | :---: | :-----: | :-----: | :----: | :----: |
|     f41 | both  |  both   |    -    | x86_64 |   -    |
|     f42 | both  |  both   | x86_64  | x86_64 |   -    |
|     f43 | both  |  both   | x86_64  | x86_64 |   -    |
| rawhide | both  |  both   | x86_64  |   -    | x86_64 |

CUDA libraries are removed from dependencies of arm64-sbsa rpms, so you can install the runfile version of CUDA.
## Summary
The `vendor` branch provides dependency bundles for copr build.

## TODO
bash completion maybe

[main-repo]: https://src.fedoraproject.org/fork/fachep/rpms/ollama/
[main-copr]: https://copr.fedorainfracloud.org/coprs/fachep/ollama/package/ollama/
[main-status]: https://copr.fedorainfracloud.org/coprs/fachep/ollama/package/ollama/status_image/last_build.png
[cuda-repo]: https://github.com/fachep/copr_ollama-ggml-cuda/
[cuda-copr]: https://copr.fedorainfracloud.org/coprs/fachep/ollama/package/ollama-ggml-cuda/
[cuda-status]: https://copr.fedorainfracloud.org/coprs/fachep/ollama/package/ollama-ggml-cuda/status_image/last_build.png
