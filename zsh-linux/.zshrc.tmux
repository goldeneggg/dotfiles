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
GH_ACCOUNT_PRACTA=practa-inc
GH_DIR=~/github
GH_MY=${GH_DIR}/${GH_ACCOUNT}
GH_PRA=${GH_DIR}/${GH_ACCOUNT_PRA}
GH_PRACTA=${GH_DIR}/${GH_ACCOUNT_PRACTA}
DIR_WK=${DIR_DOTFILES}
DIR_BLOG=${GH_MY}/pages
DIR_BLOGSITE=${GH_MY}/goldeneggg.github.io

#- tmux session initialize function
#-- 1st arg = session name
function tminit() {
  SESS=${1:-${DEFAULT_SESS_NAME}}

  WINDOWS=(
    "wk"
    "blog"
    "ops"
    "go"
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
    tmux neww -k -t ${SESS}:${IND} -n ${window} -c ${DIR_WK}
    # ペインに分割
    case ${window} in
      wk)
        # 縦分割=50%
        tmux splitw -h -p 50 -c ${DIR_WK}
        # 横分割 下部=25%
        tmux splitw -v -p 25 -c ${DIR_WK}
        # 左ペインへ
        tmux select-pane -L
        tmux send-keys "cd ${HOME}" C-m
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${DIR_WK}
        ;;
      blog)
        # 縦分割=50%
        tmux splitw -h -p 50 -c ${GH_PRACTA}/corporate
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_PRACTA}/practa-inc.github.io
        # 左ペインへ
        tmux select-pane -L
        tmux send-keys "cd ${DIR_BLOG}" C-m
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${DIR_BLOG}
        # 横分割 下部=50% 2
        tmux splitw -v -p 50 -c ${DIR_BLOGSITE}
        ;;
      # TODO:
      ops)
        # 縦分割=50%
        tmux splitw -h -p 50 -c ${HOME}
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${HOME}
        # 左ペインへ
        tmux select-pane -L
        tmux send-keys "cd ${HOME}" C-m
        # 横分割=50%
        tmux splitw -v -p 50 -c ${HOME}
        ;;
      go)
        # 縦分割=50%
        tmux splitw -h -p 50 -c ${GOPATH}/src/github.com/${GH_ACCOUNT}
        # 横分割 下部=25%
        tmux splitw -v -p 25 -c ${GOPATH}/src/github.com/${GH_ACCOUNT}
        # 左ペインへ
        tmux select-pane -L
        # cd watch-go
        tmux send-keys "cd ${GH_PRA}/watch-go" C-m
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${HOME}/goroot
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${GOROOT}/src
        ;;
      misc)
        # 縦分割=50%
        tmux splitw -h -p 50 -c ${GH_PRA}/watch-aws
        # 横分割 下部=50%
        tmux splitw -v -p 50 -c ${GH_MY}/misc-aws
        #tmux send-keys "cd ${GH_MY}/misc-aws" C-m
        # 左ペインへ
        tmux select-pane -L
        tmux send-keys "cd ${GH_PRA}/watch-ruby" C-m
        # 横分割=50%
        tmux splitw -v -p 50 -c ${GH_PRA}/rails6api
        ;;
      *)
        ;;
    esac

    IND=$((IND+1))
  done

  tmux a -t ${SESS}
}

