## Setup

```sh
git clone [this project] ~/dotfiles
cd ~/dotfiles

# for Mac only
# *require to install Homebrew. See: https://brew.sh/index_ja
make install-brew-pkgs

make setup
```

## Install npm global packages

```sh
make init-npms
```

## Setup my projects

```sh
make init-projects
```

## Update

### dotfiles

```sh
make reset

# skip "go get" as follows
make reset-skip-goget
```

## Refactoring

### [Improving Git protocol security on GitHub \| The GitHub Blog](https://github.blog/2021-09-01-improving-git-protocol-security-github/) の対応

neobundleのgit submodule URLが `git://` になっているので、`https://` に変更する

1. .gitmodules 修正
    - `url = https://github.com/Shougo/neobundle.vim`
2. `git submodule sync`
3. `git submodule update --remote --recursive` が正常動作するか確認
    - 上手くいかない場合、 `The unauthenticated git protocol on port 9418 is no longer supported.` エラーが出る

### anyenv -> asdf切り替え

See: [GitHub \- asdf\-vm/asdf: Extendable version manager with support for Ruby, Node\.js, Elixir, Erlang & more](https://github.com/asdf-vm/asdf)

1. `brew update && brew install asdf`
