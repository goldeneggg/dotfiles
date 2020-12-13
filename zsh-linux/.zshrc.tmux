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

DIR_DOTFILES=~/dotfiles

GH_ACCOUNT=goldeneggg
GH_ACCOUNT_PRA=practice-goldeneggg
GH_ACCOUNT_HRZN=horizoon
GH_DIR=~/github
GH_MY=${GH_DIR}/${GH_ACCOUNT}
GH_PRA=${GH_DIR}/${GH_ACCOUNT_PRA}
GH_HRZN=${GH_DIR}/${GH_ACCOUNT_HRZN}
DIR_WK=${DIR_DOTFILES}
DIR_BLOG=${GH_MY}/pages
DIR_BLOGSITE=${GH_MY}/goldeneggg.github.io
DIR_FOUNDING=${GH_HRZN}/founding

#- tmux session initialize function
#-- 1st arg = session name
function tminit() {
  SESS=${1:-${DEFAULT_SESS_NAME}}

  WINDOWS=(
    "wk"
    "blog"
    "go"
    "misc-rb"
    "misc"
    "eb"
  )
  START_DIRS=(
    ${DIR_WK}
    ${DIR_BLOG}
    ${GOPATH}/src/github.com/${GH_ACCOUNT}
    ${GH_MY}
    ${GH_MY}
    ${HOME}
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
    tmux neww -k -t ${SESS}:${IND} -n ${window} -c ${START_DIRS[${IND}]}
    # ペインに分割
    case ${window} in
      wk)
        # 水平=50%
        tmux splitw -h -p 50 -c ${START_DIRS[${IND}]}
        # 左ペイン
        tmux select-pane -L
        tmux send-keys "cd ${HOME}" C-m
        # 垂直 下部=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        ;;
      blog)
        # 水平=50%
        tmux splitw -h -p 50 -c ${GH_HRZN}
        # 左ペイン
        tmux select-pane -L
        tmux send-keys "cd ${START_DIRS[${IND}]}" C-m
        # 垂直 下部=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        # 垂直 下部=50% 2
        tmux splitw -v -p 50 -c ${DIR_BLOGSITE}
        ;;
      go)
        # 水平=50%
        tmux splitw -h -p 50 -c ${START_DIRS[${IND}]}
        # 左ペイン
        tmux select-pane -L
        # 垂直 下部=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        ;;
      misc-rb)
        # 水平=50%
        tmux splitw -h -p 50 -c ${GH_PRA}/watch-ruby
        # 垂直 下部=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        # 左ペイン
        tmux select-pane -L
        tmux send-keys "cd ${GH_PRA}/rails6api" C-m
        # 垂直=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        ;;
      misc)
        # 水平=50%
        tmux splitw -h -p 50 -c ${GH_PRA}/watch-aws
        # 垂直 下部=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        tmux send-keys "cd ${GH_MY}/misc-aws" C-m
        # 左ペイン
        tmux select-pane -L
        tmux send-keys "cd ${GH_PRA}/watch-wasm" C-m
        # 垂直=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        ;;
      # eb)
      #   # 垂直 下部=50%
      #   tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
      #   # 垂直 下部=50% 2
      #   tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
      #   # 最上部ペイン
      #   tmux select-pane -D
      #   # 垂直 下部=50%
      #   tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
      #   ;;
      *)
        ;;
    esac

    IND=$((IND+1))
  done

  tmux a -t ${SESS}
}

