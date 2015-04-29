# prompt
Pry.config.prompt = proc do |obj, nest_level, _pry_|
version = ''
version << "[Ruby#{RUBY_VERSION}]"
version << "[Rails#{Rails.version}]" if defined? Rails

current = ''
current << "\001\e[0;36m\002"
current << "#{File.split(File.absolute_path("."))[1]}"
current << "\001\e[0m\002"

branch = ''
branch << `git branch | awk '{print $2}'`.gsub(/\n/,"")

#"#{version}#{current}\n#{Pry.config.prompt_name}(#{Pry.view_clip(obj)})> "
"#{version}(#{current}|#{branch})> "
end

# editor
Pry.config.editor = "vim"

# hirb
# FIXME - (pry) output error: #<NoMethodError: undefined method `pager' for nil:NilClass>
## See: https://github.com/cldwalker/hirb/issues/81
begin
  require 'hirb'
  Hirb.enable
  old_print = Pry.config.print
  Pry.config.print = proc do |*args|
    Hirb::View.view_or_page_output(args[1]) || old_print.call(*args)
  end
rescue LoadError
  # Missing goodies, bummer
end

# theme
begin
  require 'pry-theme'
  Pry.config.theme = "pry-modern-256"
rescue LoadError
  # Missing goodies, bummer
end

# pry-byebug
if defined?(PryByebug)
  Pry.commands.alias_command 'c', 'continue'
  Pry.commands.alias_command 's', 'step'
  Pry.commands.alias_command 'n', 'next'
  Pry.commands.alias_command 'f', 'finish'
end
