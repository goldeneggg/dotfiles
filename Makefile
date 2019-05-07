setup = ./setup.sh -$1 --github-user goldeneggg --github-mail jpshadowapps@gmail.com

setup-mac: setup-submodule
	@$(call setup,M)

setup-linux: setup-submodule
	@$(call setup,L)

setup-submodule:
	@git submodule update --init --recursive
