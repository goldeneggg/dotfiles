require 'pp'

require 'irb/completion'

# 以下ファイルは削除された
# See: https://github.com/ruby/irb/pull/613

begin
  require 'irb/ext/save-history'
rescue LoadError
  #puts "irb/ext/save-history not found. Not saving history."
end

IRB.conf[:USE_READLINE] = true
IRB.conf[:SAVE_HISTORY] = 1000
IRB.conf[:HISTORY_PATH] = File::expand_path("~/.irb.history")
