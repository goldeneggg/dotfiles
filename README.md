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
2. `echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ${ZDOTDIR:-~}/.zshrc`
3. ターミナル再起動
4. `asdf plugin add ruby`
    - `asdf list all ruby` でインストール可能バージョン確認
5. `asdf install ruby 3.0.4`
6. `asdf install ruby 2.7.6`
7. `asdf global ruby 3.0.4`
8. `asdf reshim ruby`
9. シェルやターミナルを再起動して `ruby -v` で動作確認
10. 以降、pythonとnodejsも同様の流れでインストール
11. 言語ごとにglobalに導入したいツールやライブラリをインストール
    - nodejs `npm install -g ...` (`make init-npms`)
    - python `pip install --upgrade ...` (`make init-pips`)
        - ___pythonだけインストールしただけではツールのPATHが通っておらず `asdf reshim python` して解決___
    - ruby `gem install ...` (`make init-gems`)
12. ~/.asdfrc ファイル作成
    - See: [Using Existing Tool Version Files](http://asdf-vm.com/guide/getting-started.html#using-existing-tool-version-files)
13. 必要に応じて各プロジェクト配下に .tool-versions ファイルを用意

※ anyenv

1. `rm -fr ~/.anyenv`
2. `brew uninstall anyenv`
