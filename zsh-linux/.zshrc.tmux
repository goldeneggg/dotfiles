DEFAULT_SESS_NAME=main

#- aliases for tmux
alias tmls='tmux lsp -a'
alias tmspl='tmux splitw'

# new session
function tm() {
  SESS=${1:-${DEFAULT_SESS_NAME}}
  tmux new -s ${SESS}
}

# kill session
function tmkl() {
  SESS=${1:-${DEFAULT_SESS_NAME}}
  tmux kill-session -t ${SESS}
}

MY_BASE_INDEX=1


GH_ACCOUNT=goldeneggg
GH_ACCOUNT_PRA=practice-goldeneggg
GH_ACCOUNT_PRACTA=practa-inc
GH_DIR=~/github
GH_MY=${GH_DIR}/${GH_ACCOUNT}
GH_PRA=${GH_DIR}/${GH_ACCOUNT_PRA}
GH_PRACTA=${GH_DIR}/${GH_ACCOUNT_PRACTA}
DIR_DOTFILES=~/dotfiles
DIR_BLOGEGGG=${GH_MY}/pages
DIR_BLOGEGGGSITE=${GH_MY}/goldeneggg.github.io

#- tmux session initialize function
#-- 1st arg = session name
function tminit() {
  SESS=${1:-${DEFAULT_SESS_NAME}}

  WINDOWS=(
    "wk"
    "ops"
    "blog"
    "go"
    "zig"
    "misc"
    "eb"
  )
  # 新規セッション作成
  ## TODO 既に同一セッション名のセッションが動いている場合、セッション名を動的に変化させる
  tmux new -d -s ${SESS}
  IND=${MY_BASE_INDEX}
  # ウインドウ * 7
  for window in ${WINDOWS[@]}
  do
    # -k : 指定ウインドウが既に存在している場合のエラーをスルー
    # -c : 開始ディレクトリ指定
    tmux neww -k -t ${SESS}:${IND} -n ${window} -c ${DIR_DOTFILES}
    # ペインに分割
    case ${window} in
      wk)
        # 垂直分割=50%
        tmux splitw -h -p 50 -c ${HOME}
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${DIR_DOTFILES}
        # 左ペインへ
        tmux select-pane -L
        tmux send-keys "cd ${HOME}" C-m
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${DIR_DOTFILES}
        ;;
      ops)
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${HOME}
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd ${HOME}" C-m
        ;;
      blog)
        # 垂直分割=50%
        tmux splitw -h -p 50 -c ${DIR_BLOGEGGG}
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_PRACTA}/corporate
        # 左ペインへ
        tmux select-pane -L
        # cd goldeneggg.github.io
        tmux send-keys "cd ${DIR_BLOGEGGGSITE}" C-m
        # 水平分割 下部=80%
        tmux splitw -v -p 80 -c ${GH_PRACTA}/practa-inc.github.io
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_PRA}/readlogs
        ;;
      go)
        # 垂直分割=50%
        tmux splitw -h -p 50 -c ${GH_PRACTA}/biz
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_MY}/structil
        # 左ペインへ
        tmux select-pane -L
        # cd watch-go
        tmux send-keys "cd ${GH_PRA}/watch-go" C-m
        # 水平分割 下部=80%
        tmux splitw -v -p 80 -c ${HOME}/goroot
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${GOROOT}/src
        ;;
      zig)
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_PRA}/ziglings
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd ${GH_PRA}/watch-zig" C-m
        ;;
      misc)
        # 垂直分割=80%
        tmux splitw -h -p 80 -c ${GH_MY}/misc-aws
        # 水平分割 下部=80%
        tmux splitw -v -p 80 -c ${GH_PRA}/watch-aws
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_PRA}/watch-docker
        # 左ペインへ
        tmux select-pane -L
        tmux send-keys "cd ${GH_PRA}/watch-wasm" C-m
        # 水平分割=80%
        tmux splitw -v -p 80 -c ${GH_PRA}/watch-rust
        # 水平分割=80%
        tmux splitw -v -p 80 -c ${GH_PRA}/watch-browser
        # 水平分割=50%
        tmux splitw -v -p 50 -c ${GH_PRA}/watch-ai
        ;;
      eb)
        # 水平分割 下部=50%
        tmux splitw -v -p 50 -c "${HOME}/Documents/#bookmark"
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd /Volumes" C-m
        ;;
      *)
        ;;
    esac

    IND=$((IND+1))
  done

  tmux a -t ${SESS}
}

