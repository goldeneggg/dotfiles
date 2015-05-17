DEFAULT_SESS_NAME=main
MY_BASE_INDEX=1

DIR_DOTFILES=~/dotfiles

GH_ACCOUNT=goldeneggg
GH_DIR=~/github/${GH_ACCOUNT}
DIR_NOTE=${GH_DIR}/notes
DIR_WATCH=~/github/_watch
DIR_BOT=${GH_DIR}/myhubot
DIR_RUBY=${GH_DIR}/ruby
DIR_RAILS=${GH_DIR}/rails


#- aliases for tmux
alias tmls='tmux lsp -a'
alias tmspl='tmux splitw'

# new session
function tm() {
  if [ $# -eq 1 ]
  then
    SESS=${1}
  else
    SESS=${DEFAULT_SESS_NAME}
  fi

  tmux new -s ${SESS}
}

# kill session
function tmkl() {
  if [ $# -eq 1 ]
  then
    SESS=${1}
  else
    SESS=${DEFAULT_SESS_NAME}
  fi

  tmux kill-session -t ${SESS}
}

#- tmux session initialize function
function tminit() {
  if [ $# -eq 1 ]
  then
    SESS=${1}
  else
    SESS=${DEFAULT_SESS_NAME}
  fi

  WINDOWS=("watch" "dot" "bot" "go" "r" "ra" "ra_wk")
  START_DIRS=(${DIR_WATCH} ${DIR_DOTFILES} ${DIR_BOT} ${GOPATH}/src/github.com/${GH_ACCOUNT} ${DIR_RUBY} ${DIR_RAILS} ${DIR_RAILS})
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
      note)
        # 垂直 下部=50%
        tmux splitw -v -p 50 -c ${START_DIRS[${IND}]}
        ;;
      bot)
        # 垂直 下部=20%
        tmux splitw -v -p 20 -c ${START_DIRS[${IND}]}
        ;;
      ra_wk)
        # 垂直 下部=25%
        tmux splitw -v -p 25 -c ${START_DIRS[${IND}]}
        ;;
      *)
        ;;
    esac

    IND=$((IND+1))
  done

  tmux a -t ${SESS}
}

DIR_VM=${GH_DIR}/vagrant
DIR_MYMG=${DIR_VM}/vagrant-mysql-ubuntu14
DIR_PROVI=${GH_DIR}/provisioning-bash

#- tmux session for vm
function tmvminit() {
  SESS=vmmain

  WINDOWS=("vmcn7" "vmubu14app" "vmubu14mas" "vmubu14sla" "provi")
  START_DIRS=("${DIR_VM}/vagrant-centos70-x86" "${DIR_VM}/vagrant-ubuntu14-x86-app" "${DIR_MYMG}/replication/mas1" "${DIR_MYMG}/replication/sla1" "${DIR_PROVI}")
  # 新規セッション作成
  ## TODO 既に同一セッション名のセッションが動いている場合、セッション名を動的に変化させる
  tmux new -d -s ${SESS}
  IND=${MY_BASE_INDEX}
  # ウインドウ
  for window in ${WINDOWS[@]}
  do
    # -k : 指定ウインドウが既に存在している場合のエラーをスルー
    # -c : 開始ディレクトリ指定
    tmux neww -k -t ${SESS}:${IND} -n ${window} -c ${START_DIRS[${IND}]}
    # 垂直 下部=40%
    tmux splitw -v -p 40 -c ${START_DIRS[${IND}]}

    IND=$((IND+1))
  done

  tmux a -t ${SESS}
}
