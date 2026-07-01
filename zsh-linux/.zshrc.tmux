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
GH_DIR=~/github
GH_MY=${GH_DIR}/${GH_ACCOUNT}
GH_PRA=${GH_DIR}/${GH_ACCOUNT_PRA}
DIR_DOTFILES=~/dotfiles

#- tmux session initialize function
#-- 1st arg = session name
function tminit() {
  SESS=${1:-${DEFAULT_SESS_NAME}}

  WINDOWS=(
    "dotfiles"
    "app"
    "biz"
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
      dotfiles)
        # 垂直分割=50%（左右均等）
        tmux splitw -h -l 50% -c ${DIR_DOTFILES}
        ;;
      app)
        # 垂直分割=50%（左右均等）
        tmux splitw -h -l 50% -c ${GH_MY}/repodocs
        # 右ペインで水平分割 上25%/下75%
        tmux splitw -v -l 75% -c ${GH_MY}/repodocs
        # 左ペインへ
        tmux select-pane -t 0
        # 左ペインで水平分割 上25%/下75%
        tmux splitw -v -l 75% -c ${GH_MY}/browser-tools
        # 左上ペイン(pane 0)はneww由来で~/dotfilesのままなのでcdで設定
        tmux select-pane -t 0
        tmux send-keys "cd ${GH_MY}/browser-tools" C-m
        ;;
      biz)
        # 垂直分割=50%（左右均等）
        tmux splitw -h -l 50% -c ${GH_MY}/biz/app/bizapi
        # 右ペインで水平分割 上25%/下75%
        tmux splitw -v -l 75% -c ${GH_MY}/biz
        # 右上ペイン(pane 1)のディレクトリをsend-keysで確実に設定
        tmux select-pane -t 1
        tmux send-keys "cd ${GH_MY}/biz/app/bizapi" C-m
        # 左ペインへ
        tmux select-pane -t 0
        # 左ペインで水平分割 上25%/下75%
        tmux splitw -v -l 75% -c ${GH_MY}/biz
        # 左上ペイン(pane 0)はneww由来で~/dotfilesのままなのでcdで設定
        tmux select-pane -t 0
        tmux send-keys "cd ${GH_MY}/biz/app/slacksocket" C-m
        ;;
      watch)
        # 垂直分割=50%（左右均等）
        tmux splitw -h -l 50% -c ${GH_PRA}/watch-browser
        # 右ペインで水平分割=50%
        tmux splitw -v -l 50% -c ${GH_PRA}/watch-ai
        # 左ペインへ
        tmux select-pane -t 0
        # 左ペインで水平分割=50%
        tmux splitw -v -l 50% -c ${HOME}/goroot
        # 左上ペインへ戻してcd
        tmux select-pane -t 0
        tmux send-keys "cd ${HOME}/gotools" C-m
        ;;
      b-dev)
        # 垂直分割=50%
        tmux splitw -h -l 50% -c "/Volumes"
        # 右ペインで水平分割=50%
        tmux splitw -v -l 50% -c "/Volumes"
        # 左ペインへ
        tmux select-pane -t 0
        # 左ペインで水平分割=50%
        tmux splitw -v -l 50% -c "/Volumes"
        # 左上ペイン(pane 0)はneww由来で~/dotfilesのままなのでcdで設定
        tmux select-pane -t 0
        tmux send-keys "cd /Volumes" C-m
        ;;
      b-biz)
        # 垂直分割=50%
        tmux splitw -h -l 50% -c "/Volumes"
        # 右ペインで水平分割=50%
        tmux splitw -v -l 50% -c "/Volumes"
        # 左ペインへ
        tmux select-pane -t 0
        # 左ペインで水平分割=50%
        tmux splitw -v -l 50% -c "/Volumes"
        # 左上ペイン(pane 0)はneww由来で~/dotfilesのままなのでcdで設定
        tmux select-pane -t 0
        tmux send-keys "cd /Volumes" C-m
        ;;
      x)
        # 水平分割=50%（上下均等）
        tmux splitw -v -l 50% -c "/Volumes"
        # 上ペイン(pane 0)はneww由来で~/dotfilesのままなのでcdで設定
        tmux select-pane -t 0
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
