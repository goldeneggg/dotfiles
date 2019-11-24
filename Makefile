setup = ./setup.bash -$1 --github-user goldeneggg --github-mail jpshadowapps@gmail.com $2

setup-mac: setup-submodule
	@$(call setup,M,)

setup-mac-skip-goget: setup-submodule
	@$(call setup,M,--skip-goget)

setup-linux: setup-submodule
	@$(call setup,L)

setup-submodule:
	@git submodule update --init --recursive

update-xxenvs:
	@./xxenv.bash update
