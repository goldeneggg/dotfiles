# prompt
Pry.config.prompt = proc do |obj, nest_level, _pry_|
version = ''
version << "[#{RUBY_VERSION}]"
version << "[Rails#{Rails.version}]" if defined? Rails

"#{version} #{Pry.config.prompt_name}(#{Pry.view_clip(obj)})> "
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
