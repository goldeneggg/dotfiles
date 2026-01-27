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
    "home"
    "app"
    "go"
    "watch"
    "b-dev"
    "b-biz"
    "x"
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
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${DIR_DOTFILES}
        # 垂直分割=50%
        tmux splitw -h -l 50% -c ${DIR_DOTFILES}
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd ${HOME}" C-m
        ;;
      PARTNER-1)
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${GH_DIR}
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd ${GH_DIR}" C-m
        ;;
      PARTNER-2)
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${GH_DIR}
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd ${GH_DIR}" C-m
        ;;
      app)
        # 垂直分割 下部=50%
        tmux splitw -h -l 50% -c ${GH_MY}/biz/app
        # 右ペインへ
        tmux select-pane -R
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${GH_MY}/biz/app
        # 下ペインへ
        tmux select-pane -D
        tmux send-keys "cd ${GH_MY}/biz/app" C-m
        ;;
      go)
        # 垂直分割=50%
        tmux splitw -h -l 50% -c ${GH_MY}/biz
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${GH_PRA}/watch-go
        # 左ペインへ
        tmux select-pane -L
        # cd goldeneggg.github.io
        tmux send-keys "cd ${HOME}/goexample" C-m
        # 水平分割 下部=70%
        tmux splitw -v -l 70% -c ${HOME}/gotools
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${HOME}/goroot
        ;;
      watch)
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c ${GH_PRA}/watch-ai
        # 上ペインへ
        tmux select-pane -U
        tmux send-keys "cd ${GH_PRA}/watch-aws" C-m
        ;;
      b-dev)
        # 垂直分割 50%
        tmux splitw -h -l 50% -c "/Volumes"
        # 水平分割 50%
        tmux splitw -v -l 50% -c "/Volumes"
        # 左部ペインへ
        tmux select-pane -L
        tmux send-keys "cd /Volumes" C-m
        # 水平分割=50%
        tmux splitw -v -l 50% -c "/Volumes"
        ;;
      b-biz)
        # 垂直分割 50%
        tmux splitw -h -l 50% -c "/Volumes"
        # 水平分割 50%
        tmux splitw -v -l 50% -c "/Volumes"
        # 左部ペインへ
        tmux select-pane -L
        tmux send-keys "cd /Volumes" C-m
        # 水平分割=50%
        tmux splitw -v -l 50% -c "/Volumes"
        ;;
      x)
        # 水平分割 下部=50%
        tmux splitw -v -l 50% -c /Volumes
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

function tmccsplitpanes() {
  # 水平分割 下部=50%
  tmux splitw -v -l 50%
  # 上ペインへ
  tmux select-pane -U
  # 垂直分割=50%
  tmux splitw -h -l 50%
  # 右ペインへ
  #tmux select-pane -R
  # 水平分割 下部=50%
  tmux splitw -v -l 50%
  # 下ペインへ
  tmux select-pane -D
  # 垂直分割=50%
  tmux splitw -h -l 50%
  # 右ペインへ
  #tmux select-pane -R
  # 水平分割 下部=50%
  tmux splitw -v -l 50%
}

function tmcmdallpanes() {
  cmd="${1:-"ls -la"}"
  tmux list-panes -F "#{pane_id}" | xargs -I {} tmux send-keys -t {} "${cmd}" Enter
}

function tmccstartallpanes() {
  tmcmdtallpanes "claude"
}
